"""Quadratics to cubics."""

from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING

import pathops
from fontTools.cffLib import PrivateDict
from fontTools.pens.cu2quPen import Cu2QuPen
from fontTools.pens.qu2cuPen import Qu2CuPen
from fontTools.pens.t2CharStringPen import T2CharStringPen
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.ttLib.ttGlyphSet import _TTGlyph

from foundrytools.lib.pathops import simplify_path

if TYPE_CHECKING:
    from fontTools.misc.psCharStrings import T2CharString
    from fontTools.ttLib import TTFont

__all__ = ["quadratics_to_cubics", "quadratics_to_cubics_2"]


_TTGlyphMapping = Mapping[str, _TTGlyph]


def _skia_path_from_charstring(charstring: T2CharString) -> pathops.Path:
    path = pathops.Path()
    path_pen = path.getPen(glyphSet=None)
    charstring.draw(path_pen)
    return path


def _charstring_from_skia_path(path: pathops.Path, width: int) -> T2CharString:
    t2_pen = T2CharStringPen(width=width, glyphSet=None)
    path.draw(t2_pen)
    return t2_pen.getCharString()


def quadratics_to_cubics(
    font: TTFont, *, tolerance: float = 1.0, correct_contours: bool = True
) -> dict[str, T2CharString]:
    """
    Convert quadratic Bézier splines to cubic curves with a specified tolerance using the ``Qu2CuPen``.

    Optionally corrects the winding direction of the contours.

    :param font: The TTFont object representing the font to process.
    :type font: TTFont
    :param tolerance: The maximum acceptable deviation in font units when approximating the
        quadratic Bézier curves. Default is 1.0.
    :type tolerance: float
    :param correct_contours: Whether to correct contours for overlapping. Default is True.
    :type correct_contours: bool
    :return: A dictionary mapping glyph names to their corresponding T2CharString objects after
        conversion.
    :rtype: dict[str, T2CharString]
    """
    qu2cu_charstrings = {}
    glyph_set = font.getGlyphSet()

    for k, v in glyph_set.items():
        width = v.width

        try:
            t2_pen = T2CharStringPen(width=width, glyphSet={k: v})
            qu2cu_pen = Qu2CuPen(t2_pen, max_err=tolerance, all_cubic=True, reverse_direction=True)
            glyph_set[k].draw(qu2cu_pen)
            qu2cu_charstrings[k] = t2_pen.getCharString()

        except NotImplementedError:
            temp_t2_pen = T2CharStringPen(width=width, glyphSet=None)
            glyph_set[k].draw(temp_t2_pen)
            t2_charstring = temp_t2_pen.getCharString()
            t2_charstring.private = PrivateDict()

            tt_pen = TTGlyphPen(glyphSet=None)
            cu2qu_pen = Cu2QuPen(other_pen=tt_pen, max_err=tolerance, reverse_direction=False)
            t2_charstring.draw(cu2qu_pen)
            tt_glyph = tt_pen.glyph()

            t2_pen = T2CharStringPen(width=width, glyphSet=None)
            qu2cu_pen = Qu2CuPen(t2_pen, max_err=tolerance, all_cubic=True, reverse_direction=True)
            tt_glyph.draw(pen=qu2cu_pen, glyfTable=None)

        charstring = t2_pen.getCharString()

        if correct_contours:
            charstring.private = PrivateDict()
            path = _skia_path_from_charstring(charstring)
            simplified_path = simplify_path(path, glyph_name=k, clockwise=False)
            charstring = _charstring_from_skia_path(path=simplified_path, width=width)

        qu2cu_charstrings[k] = charstring

    return qu2cu_charstrings


def quadratics_to_cubics_2(font: TTFont) -> dict[str, T2CharString]:
    """
    Convert quadratic Bézier splines to cubic curves using the ``T2CharStringPen``.

    :param font: The ``TTFont`` object representing the font to process.
    :type font: TTFont
    :return: A dictionary mapping glyph names to their corresponding T2CharString objects after
        conversion.
    :rtype: dict[str, T2CharString]
    """
    t2_charstrings = {}
    glyph_set = font.getGlyphSet()

    for k, v in glyph_set.items():
        t2_pen = T2CharStringPen(v.width, glyphSet=glyph_set)
        glyph_set[k].draw(t2_pen)
        charstring = t2_pen.getCharString()
        t2_charstrings[k] = charstring

    return t2_charstrings
