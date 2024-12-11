from fontTools.subset import Options, Subsetter

from foundrytools import Font
from foundrytools.constants import SUBSETTER_DEFAULTS


class RemoveUnusedGlyphsError(Exception):
    """Exception raised for errors in removing unused glyphs from a font object."""


def run(font: Font) -> set[str]:
    """
    Remove glyphs that are not reachable by Unicode values or by substitution rules in the font.

    :return: A set of glyph names that were removed.
    :rtype: set[str]
    """
    try:
        options = Options(**SUBSETTER_DEFAULTS)
        options.recalc_timestamp = font.ttfont.recalcTimestamp
        old_glyph_order = font.ttfont.getGlyphOrder()
        unicodes = font.t_cmap.get_all_codepoints()
        subsetter = Subsetter(options=options)
        subsetter.populate(unicodes=unicodes)
        subsetter.subset(font.ttfont)
        new_glyph_order = font.ttfont.getGlyphOrder()

        return set(old_glyph_order) - set(new_glyph_order)

    except Exception as e:
        raise RemoveUnusedGlyphsError(e) from e
