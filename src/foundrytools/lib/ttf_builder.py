from fontTools.pens.cu2quPen import Cu2QuPen
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.ttLib import TTFont, newTable
from fontTools.ttLib.tables._g_l_y_f import (
    Glyph,
    table__g_l_y_f,
)
from fontTools.ttLib.ttGlyphSet import _TTGlyphCFF

from foundrytools.constants import (
    T_CFF,
    T_GLYF,
    T_HMTX,
    T_LOCA,
    T_MAXP,
    T_POST,
    T_VORG,
)

MAXP_TABLE_VERSION = 0x00010000


def build_ttf(
    font: TTFont, max_err: float = 1.0, reverse_direction: bool = True, post_format: float = 2.0
) -> None:
    """
    Builds an OpenType-TT font with quadratic outlines.

    :param font: The input ``TTFont`` object.
    :type font: TTFont
    :param max_err: The maximum approximation error, measured in UPEM.
    :type max_err: float, optional
    :param reverse_direction: Whether to reverse the direction of the contours.
    :type reverse_direction: bool, optional
    :param post_format: The format of the ``post`` table.
    :type post_format: float, optional
    """
    glyph_order = font.getGlyphOrder()

    font[T_LOCA] = newTable(T_LOCA)
    font[T_GLYF] = glyf = newTable(T_GLYF)
    glyf.glyphOrder = glyph_order
    glyf.glyphs = glyphs_to_quadratic(
        glyph_set=font.getGlyphSet(), max_err=max_err, reverse_direction=reverse_direction
    )
    del font[T_CFF]
    if T_VORG in font:
        del font[T_VORG]
    glyf.compile(font)
    update_hmtx(font=font, glyf=glyf)

    font[T_MAXP] = maxp = newTable(T_MAXP)
    maxp.tableVersion = MAXP_TABLE_VERSION
    maxp.maxZones = 1
    maxp.maxTwilightPoints = 0
    maxp.maxStorage = 0
    maxp.maxFunctionDefs = 0
    maxp.maxInstructionDefs = 0
    maxp.maxStackElements = 0
    maxp.maxSizeOfInstructions = 0
    maxp.maxComponentElements = max(
        len(g.components if hasattr(g, "components") else []) for g in glyf.glyphs.values()
    )
    maxp.compile(font)

    post = font[T_POST]
    post.formatType = post_format
    post.extraNames = []
    post.mapping = {}
    post.glyphOrder = glyph_order
    try:
        post.compile(font)
    except OverflowError:
        post.formatType = 3

    font.sfntVersion = "\000\001\000\000"


def update_hmtx(font: TTFont, glyf: table__g_l_y_f) -> None:
    """
    Updates the ``xMin`` values in the ``hmtx`` table of a font.

    :param font: The font to update the ``hmtx`` table of.
    :type font: TTFont
    :param glyf: The ``glyf`` table of the font.
    :type glyf: table__g_l_y_f
    """

    hmtx = font[T_HMTX]
    for glyph_name, glyph in glyf.glyphs.items():
        if hasattr(glyph, "xMin"):
            hmtx[glyph_name] = (hmtx[glyph_name][0], glyph.xMin)


def glyphs_to_quadratic(
    glyph_set: dict[str, _TTGlyphCFF], max_err: float = 1.0, reverse_direction: bool = False
) -> dict[str, Glyph]:
    """Converts a dictionary of glyphs to quadratic outlines."""

    quad_glyphs = {}
    for gname in glyph_set:
        glyph = glyph_set[gname]
        tt_pen = TTGlyphPen(glyph_set)
        cu2qu_pen = Cu2QuPen(tt_pen, max_err=max_err, reverse_direction=reverse_direction)
        glyph.draw(cu2qu_pen)
        quad_glyphs[gname] = tt_pen.glyph()
    return quad_glyphs
