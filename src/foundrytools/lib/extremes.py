import math
from typing import Any

from fontTools.misc.bezierTools import solveQuadratic, splitCubicAtT, splitQuadraticAtT
from fontTools.misc.roundTools import otRound
from fontTools.pens.basePen import BasePen
from fontTools.pens.recordingPen import RecordingPen
from fontTools.pens.t2CharStringPen import T2CharStringPen
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.ttLib import TTFont

from foundrytools.constants import T_CFF, T_GLYF

__all__ = ["AddExtremesPen", "add_extremes_to_cff", "add_extremes_to_glyf"]

_EPSILON = 1e-3


def _inner_roots(roots: list[float]) -> list[float]:
    return [t for t in roots if _EPSILON < t < 1 - _EPSILON]


def _lerp(a: tuple, b: tuple, t: float) -> tuple:
    return a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t


def _point_at(points: tuple, t: float) -> tuple:
    while len(points) > 1:
        points = tuple(_lerp(points[i], points[i + 1], t) for i in range(len(points) - 1))
    return points[0]


def _filter_ts(candidates: list[tuple[float, int]], points: tuple, tolerance: float) -> list[float]:
    """
    Keeps only the extrema that are not already present within the given tolerance: those whose
    value on the extremum axis is within tolerance of an endpoint, those closer than tolerance to
    an endpoint, and those closer than tolerance to an already accepted extremum are discarded.
    """
    start, end = points[0], points[-1]
    accepted: list[tuple[float, tuple]] = []
    for t, axis in sorted(candidates):
        pt = _point_at(points, t)
        if tolerance > 0:
            if min(abs(pt[axis] - start[axis]), abs(pt[axis] - end[axis])) <= tolerance:
                continue
            if any(
                math.dist(pt, other) <= tolerance
                for other in (start, end, *(a[1] for a in accepted))
            ):
                continue
        accepted.append((t, pt))
    return [t for t, _ in accepted]


def _cubic_extrema_ts(
    p0: tuple, p1: tuple, p2: tuple, p3: tuple, tolerance: float = 0
) -> list[float]:
    candidates: list[tuple[float, int]] = []
    for axis in (0, 1):
        a = p3[axis] - 3 * p2[axis] + 3 * p1[axis] - p0[axis]
        b = 2 * (p2[axis] - 2 * p1[axis] + p0[axis])
        c = p1[axis] - p0[axis]
        candidates.extend((t, axis) for t in _inner_roots(list(solveQuadratic(a, b, c))))
    return _filter_ts(candidates, (p0, p1, p2, p3), tolerance)


def _quadratic_extrema_ts(p0: tuple, p1: tuple, p2: tuple, tolerance: float = 0) -> list[float]:
    candidates: list[tuple[float, int]] = []
    for axis in (0, 1):
        denominator = p0[axis] - 2 * p1[axis] + p2[axis]
        if denominator:
            candidates.extend(
                (t, axis) for t in _inner_roots([(p0[axis] - p1[axis]) / denominator])
            )
    return _filter_ts(candidates, (p0, p1, p2), tolerance)


class AddExtremesPen(BasePen):
    """
    A segment pen that splits curves at their horizontal and vertical extrema and draws the result
    to another pen. Quadratic curves are emitted as explicit single off-curve segments and cubic
    curves as ``curveTo`` segments, so it works for both TrueType and PostScript outlines.

    Extrema that already exist within ``tolerance`` font units (an endpoint on the extremum axis
    or a nearby point) are not added. A tolerance of 0 adds every extremum.

    Coordinates are rounded to integers, because both ``glyf`` and CFF store integer coordinates.
    """

    def __init__(self, out_pen: Any, tolerance: float = 1, round_coordinates: bool = True) -> None:
        super().__init__(None)
        self.out_pen = out_pen
        self.tolerance = tolerance
        self.round_coordinates = round_coordinates
        self.added_points = 0

    def _r(self, pt: tuple) -> tuple:
        if self.round_coordinates:
            return otRound(pt[0]), otRound(pt[1])
        return pt

    def _moveTo(self, pt: tuple) -> None:
        self.out_pen.moveTo(self._r(pt))

    def _lineTo(self, pt: tuple) -> None:
        self.out_pen.lineTo(self._r(pt))

    def _curveToOne(self, pt1: tuple, pt2: tuple, pt3: tuple) -> None:
        ts = _cubic_extrema_ts(self._getCurrentPoint(), pt1, pt2, pt3, self.tolerance)
        if not ts:
            self.out_pen.curveTo(self._r(pt1), self._r(pt2), self._r(pt3))
            return
        segments = splitCubicAtT(self._getCurrentPoint(), pt1, pt2, pt3, *ts)
        for segment in segments:
            self.out_pen.curveTo(*(self._r(p) for p in segment[1:]))
        self.added_points += len(ts)

    def _qCurveToOne(self, pt1: tuple, pt2: tuple) -> None:
        ts = _quadratic_extrema_ts(self._getCurrentPoint(), pt1, pt2, self.tolerance)
        if not ts:
            self.out_pen.qCurveTo(self._r(pt1), self._r(pt2))
            return
        segments = splitQuadraticAtT(self._getCurrentPoint(), pt1, pt2, *ts)
        for segment in segments:
            self.out_pen.qCurveTo(*(self._r(p) for p in segment[1:]))
        self.added_points += len(ts)

    def _closePath(self) -> None:
        self.out_pen.closePath()

    def _endPath(self) -> None:
        self.out_pen.endPath()


def add_extremes_to_glyf(
    font: TTFont, remove_hinting: bool = True, tolerance: float = 1
) -> set[str]:
    """
    Adds points at the horizontal and vertical extrema of the curves of the simple glyphs of a
    TrueType font. Composite glyphs are not modified.

    :param font: The ``TTFont`` object.
    :type font: TTFont
    :param remove_hinting: Whether to remove hinting instructions from the modified glyphs.
    :type remove_hinting: bool
    :param tolerance: Extrema closer than this value (in font units) to an existing point are
        not added. Defaults to 1.
    :type tolerance: float
    :return: The set of modified glyph names.
    :rtype: set[str]
    """
    glyf_table = font[T_GLYF]
    modified_glyphs = set()

    for glyph_name in font.getGlyphOrder():
        glyph = glyf_table[glyph_name]
        if glyph.isComposite() or glyph.numberOfContours <= 0:
            continue

        tt_pen = TTGlyphPen(None)
        extremes_pen = AddExtremesPen(tt_pen, tolerance)
        glyph.draw(extremes_pen, glyf_table)
        if not extremes_pen.added_points:
            continue

        new_glyph = tt_pen.glyph()
        if remove_hinting:
            new_glyph.removeHinting()
        new_glyph.recalcBounds(glyf_table)
        glyf_table[glyph_name] = new_glyph
        modified_glyphs.add(glyph_name)

    return modified_glyphs


def add_extremes_to_cff(
    font: TTFont,
    remove_hinting: bool = True,
    remove_unused_subroutines: bool = True,
    tolerance: float = 1,
) -> set[str]:
    """
    Adds points at the horizontal and vertical extrema of the curves of the glyphs of a CFF font.

    :param font: The ``TTFont`` object.
    :type font: TTFont
    :param remove_hinting: Whether to remove hinting data if one or more glyphs are modified.
    :type remove_hinting: bool
    :param remove_unused_subroutines: Whether to remove unused subroutines if one or more glyphs
        are modified.
    :type remove_unused_subroutines: bool
    :param tolerance: Extrema closer than this value (in font units) to an existing point are
        not added. Defaults to 1.
    :type tolerance: float
    :return: The set of modified glyph names.
    :rtype: set[str]
    """
    glyph_set = font.getGlyphSet()
    cff_font_set = font[T_CFF].cff
    charstrings = cff_font_set[0].CharStrings
    modified_glyphs = set()

    for glyph_name in font.getGlyphOrder():
        charstring = charstrings[glyph_name]

        # Probe first, so unmodified glyphs keep their original charstring (hints and subroutines)
        probe_pen = AddExtremesPen(RecordingPen(), tolerance)
        glyph_set[glyph_name].draw(probe_pen)
        if not probe_pen.added_points:
            continue

        if charstring.width == charstring.private.defaultWidthX:
            width = None
        else:
            width = charstring.width - charstring.private.nominalWidthX

        t2_pen = T2CharStringPen(width=width, glyphSet=None)
        probe_pen.out_pen.replay(t2_pen)
        charstrings[glyph_name] = t2_pen.getCharString(charstring.private, charstring.globalSubrs)
        modified_glyphs.add(glyph_name)

    if modified_glyphs:
        if remove_hinting:
            cff_font_set.remove_hints()
        if remove_unused_subroutines:
            cff_font_set.remove_unused_subroutines()

    return modified_glyphs
