"""Path operations."""

from __future__ import annotations

import itertools
from collections.abc import Mapping
from typing import TYPE_CHECKING, Callable

import pathops
from fontTools.misc.roundTools import noRound, otRound
from fontTools.pens.t2CharStringPen import T2CharStringPen
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.ttLib.ttGlyphSet import _TTGlyph

from foundrytools.constants import T_CFF, T_GLYF, T_HMTX

if TYPE_CHECKING:
    from fontTools.cffLib import CFFFontSet
    from fontTools.misc.psCharStrings import T2CharString
    from fontTools.ttLib import TTFont
    from fontTools.ttLib.tables import _g_l_y_f, _h_m_t_x

_TTGlyphMapping = Mapping[str, _TTGlyph]

__all__ = ["correct_cff_contours", "correct_glyf_contours", "simplify_path"]


class CorrectContoursError(Exception):
    """Raised when an error occurs while correcting the contours of a TrueType font."""


def _skia_path_from_glyph(glyph_name: str, glyph_set: _TTGlyphMapping) -> pathops.Path:
    path = pathops.Path()
    pen = path.getPen(glyphSet=glyph_set)
    glyph_set[glyph_name].draw(pen)
    return path


def _skia_path_from_glyph_component(component: _g_l_y_f.GlyphComponent, glyph_set: _TTGlyphMapping) -> pathops.Path:
    base_glyph_name, transformation = component.getComponentInfo()
    path = _skia_path_from_glyph(glyph_name=base_glyph_name, glyph_set=glyph_set)
    return path.transform(*transformation)


def _ttf_components_overlap(glyph: _g_l_y_f.Glyph, glyph_set: _TTGlyphMapping) -> bool:
    if not glyph.isComposite():
        msg = "This method only works with TrueType composite glyphs"
        raise ValueError(msg)
    if len(glyph.components) < 2:  # noqa: PLR2004
        return False

    component_paths = {}

    def _get_nth_component_path(index: int) -> pathops.Path:
        if index not in component_paths:
            component_paths[index] = _skia_path_from_glyph_component(glyph.components[index], glyph_set)
        return component_paths[index]

    return any(
        pathops.op(
            _get_nth_component_path(i),
            _get_nth_component_path(j),
            pathops.PathOp.INTERSECTION,
            clockwise=True,
            fix_winding=True,
        )
        for i, j in itertools.combinations(range(len(glyph.components)), 2)
    )


def _tt_glyph_from_skia_path(path: pathops.Path) -> _g_l_y_f.Glyph:
    tt_pen = TTGlyphPen(glyphSet=None)
    path.draw(tt_pen)
    glyph = tt_pen.glyph()
    glyph.recalcBounds(glyfTable=None)
    return glyph


def _t2_charstring_from_skia_path(
    path: pathops.Path,
    charstring: T2CharString,
) -> T2CharString:
    # https://github.com/fonttools/fonttools/commit/40b525c1e3cc20b4b64004b8e3224a67adc2adf1
    # The width argument of `T2CharStringPen()` is inserted directly into the CharString
    # program, so it must be relative to Private.nominalWidthX.
    if charstring.width == charstring.private.defaultWidthX:
        width = None
    else:
        width = charstring.width - charstring.private.nominalWidthX

    t2_pen = T2CharStringPen(width=width, glyphSet=None)
    path.draw(t2_pen)
    return t2_pen.getCharString(charstring.private, charstring.globalSubrs)


def _round_path(path: pathops.Path, rounder: Callable[[float], float] = otRound) -> pathops.Path:
    rounded_path = pathops.Path()
    for verb, points in path:
        rounded_path.add(verb, *((rounder(p[0]), rounder(p[1])) for p in points))
    return rounded_path


def _same_path(path_1: pathops.Path, path_2: pathops.Path) -> bool:
    """
    Check if two pathops paths are the same.

    Args:
        path_1 (pathops.Path): The first path
        path_2 (pathops.Path): The second path

    Returns:
        bool: ``True`` if the paths are the same, ``False`` if the paths are different

    """
    return {tuple(c) for c in path_1.contours} == {tuple(c) for c in path_2.contours}


def _remove_tiny_paths(path: pathops.Path, min_area: float) -> pathops.Path:
    """
    Remove tiny paths from a ``pathops.Path`` object.

    A path is considered tiny if its area is less
    than the given minimum area (default is 25).

    :param path: The path to clean.
    :type path: pathops.Path
    :param min_area: The minimum area of a contour to be considered. Defaults to 25.
    :type min_area: int
    :return: The cleaned path.
    :rtype: pathops.Path
    """
    cleaned_path = pathops.Path()
    for contour in path.contours:
        if contour.area >= min_area:
            cleaned_path.addPath(contour)
    return cleaned_path


def _correct_tt_glyph_contours(
    glyph_name: str,
    glyph_set: _TTGlyphMapping,
    glyf_table: _g_l_y_f.table__g_l_y_f,
    hmtx_table: _h_m_t_x.table__h_m_t_x,
    *,
    remove_hinting: bool = True,
    min_area: int = 25,
) -> bool:
    glyph: _g_l_y_f.Glyph = glyf_table[glyph_name]
    # decompose composite glyphs only if components overlap each other
    if glyph.numberOfContours > 0 or (
        glyph.isComposite() and _ttf_components_overlap(glyph=glyph, glyph_set=glyph_set)
    ):
        path = _skia_path_from_glyph(glyph_name, glyph_set)
        path_2 = simplify_path(path, glyph_name, clockwise=True)
        if min_area > 0:
            path_2 = _remove_tiny_paths(path_2, min_area=min_area)

        if not _same_path(path_1=path, path_2=path_2):
            glyf_table[glyph_name] = glyph = _tt_glyph_from_skia_path(path_2)
            width, lsb = hmtx_table[glyph_name]
            if lsb != glyph.xMin:
                hmtx_table[glyph_name] = (width, glyph.xMin)
            return True

    if remove_hinting:
        glyph.removeHinting()
    return False


def _correct_charstring_contours(
    glyph_name: str,
    glyph_set: _TTGlyphMapping,
    cff_font_set: CFFFontSet,
    min_area: float = 25,
) -> bool:
    try:
        path = _skia_path_from_glyph(glyph_name, glyph_set)
        path_2 = simplify_path(path, glyph_name, clockwise=False)

        if min_area > 0:
            path_2 = _remove_tiny_paths(path_2, min_area=min_area)

        if not _same_path(path_1=path, path_2=path_2):
            charstrings = cff_font_set[0].CharStrings
            charstrings[glyph_name] = _t2_charstring_from_skia_path(path_2, charstrings[glyph_name])
            return True

    except Exception as e:
        msg = f"Failed to correct contours of glyph {glyph_name!r}"
        raise CorrectContoursError(msg) from e

    return False


def simplify_path(path: pathops.Path, glyph_name: str, *, clockwise: bool) -> pathops.Path:
    """
    Simplifies a ``pathops.Path`` by removing overlaps and correcting the direction of the contours.

    :param path: The ``pathops.Path`` to simplify.
    :type path: pathops.Path
    :param glyph_name: The name of the glyph.
    :type glyph_name: str
    :param clockwise: Whether the contours should be clockwise.
    :type clockwise: bool
    :raises CorrectContoursError: If an error occurs while simplifying the path.
    :return: The simplified path.
    :rtype: pathops.Path
    """
    try:
        return pathops.simplify(path, fix_winding=True, clockwise=clockwise)
    except pathops.PathOpsError:
        pass

    path = _round_path(path, rounder=noRound)
    try:
        return pathops.simplify(path, fix_winding=True, clockwise=clockwise)
    except pathops.PathOpsError as e:
        msg = f"Failed to remove overlaps from glyph {glyph_name!r}"
        raise CorrectContoursError(msg) from e


def correct_glyf_contours(
    font: TTFont,
    remove_hinting: bool,  # noqa: FBT001
    ignore_errors: bool,  # noqa: FBT001
    min_area: int = 25,
) -> set[str]:
    """
    Correct the contours of the given TrueType font.

    Achieves this by removing overlaps, correcting the direction
    of the contours, and removing tiny paths. The function returns the list of modified glyphs.

    :param font: The ``TTFont`` object.
    :type font: TTFont
    :param remove_hinting: Whether to remove hinting instructions.
    :type remove_hinting: bool
    :param ignore_errors: Whether to ignore errors.
    :type ignore_errors: bool
    :param min_area: The minimum area of a contour to be considered. Defaults to 25.
    :type min_area: int
    :raises CorrectContoursError: If an error occurs while correcting the contours.
    :return: The list of modified glyphs.
    :rtype: set[str]
    """
    glyph_names = font.getGlyphOrder()
    glyph_set = font.getGlyphSet()
    glyf_table = font[T_GLYF]
    hmtx_table = font[T_HMTX]

    # The minimum area is given in font units, so we need to convert it to em units
    min_area = min_area / 1000 * font["head"].unitsPerEm

    # process all simple glyphs first, then composites with increasing component depth,
    # so that by the time we test for component intersections the respective base glyphs
    # have already been simplified
    glyph_names = sorted(
        glyph_names,
        key=lambda name: (
            (
                glyf_table[name].getCompositeMaxpValues(glyf_table).maxComponentDepth
                if glyf_table[name].isComposite()
                else 0
            ),
            name,
        ),
    )
    modified_glyphs = set()
    for glyph_name in glyph_names:
        try:
            if _correct_tt_glyph_contours(
                glyph_name=glyph_name,
                glyph_set=glyph_set,
                glyf_table=glyf_table,
                hmtx_table=hmtx_table,
                remove_hinting=remove_hinting,
                min_area=min_area,
            ):
                modified_glyphs.add(glyph_name)
        except CorrectContoursError:  # noqa: PERF203
            if not ignore_errors:
                raise

    return modified_glyphs


def correct_cff_contours(
    font: TTFont,
    remove_hinting: bool,  # noqa: FBT001
    ignore_errors: bool,  # noqa: FBT001
    *,
    remove_unused_subroutines: bool = True,
    min_area: int = 25,
) -> set[str]:
    """
    Correct the contours of the given CFF font.

    Achieves this by removing overlaps, correcting the direction of
    the contours, and removing tiny paths. The function returns the list of modified glyphs.

    :param font: The ``TTFont`` object.
    :type font: TTFont
    :param remove_hinting: Whether to remove hinting instructions.
    :type remove_hinting: bool
    :param ignore_errors: Whether to ignore errors.
    :type ignore_errors: bool
    :param remove_unused_subroutines: Whether to remove unused subroutines. Defaults to True.
    :type remove_unused_subroutines: bool
    :param min_area: The minimum area of a contour to be considered. Defaults to 25.
    :type min_area: int
    :raises CorrectContoursError: If an error occurs while correcting the contours.
    :return: The list of modified glyphs.
    :rtype: set[str]
    """
    glyph_names = font.getGlyphOrder()
    glyph_set = font.getGlyphSet()
    cff_font_set: CFFFontSet = font[T_CFF].cff
    modified_glyphs = set()

    # The minimum area is given in font units, so we need to convert it to em units
    min_area = min_area / 1000 * font["head"].unitsPerEm

    for glyph_name in glyph_names:
        try:
            if _correct_charstring_contours(
                glyph_name=glyph_name,
                glyph_set=glyph_set,
                cff_font_set=cff_font_set,
                min_area=min_area,
            ):
                modified_glyphs.add(glyph_name)
        except CorrectContoursError:  # noqa: PERF203
            if not ignore_errors:
                raise

    if not modified_glyphs:
        return set()

    if remove_hinting:
        cff_font_set.remove_hints()

    if remove_unused_subroutines:
        cff_font_set.remove_unused_subroutines()

    return modified_glyphs
