from typing import Literal

import defcon
from extractor import extractUFO

from foundrytools import Font


class SortGlyphsError(Exception):
    """An error occurred while sorting the glyphs."""


def run(
    font: Font,
    sort_by: Literal["unicode", "alphabetical", "cannedDesign"] = "unicode",
) -> bool:
    """
    Reorder the glyphs based on the Unicode values, alphabetical order, or canned design order.

    :param font: The font to reorder the glyphs in.
    :type font: Font
    :param sort_by: The sorting method. Can be one of the following values: 'unicode',
        'alphabetical', or 'cannedDesign'. Defaults to 'unicode'.
    :type sort_by: Literal['unicode', 'alphabetical', 'cannedDesign']
    :return: ``True`` if the glyphs were reordered, ``False`` otherwise.
    :rtype: bool
    :raises SortGlyphsError: If an error occurred while sorting the glyphs.
    """
    try:
        ufo = defcon.Font()
        extractUFO(font.file, destination=ufo, doFeatures=False, doInfo=False, doKerning=False)
        old_glyph_order = font.ttfont.getGlyphOrder()
        new_glyph_order = ufo.unicodeData.sortGlyphNames(
            glyphNames=old_glyph_order,
            sortDescriptors=[{"type": sort_by}],
        )

        # Ensure that the '.notdef' glyph is always the first glyph in the font as required by
        # the OpenType specification. If the '.notdef' glyph is not the first glyph, compiling
        # the CFF table will fail.
        # https://learn.microsoft.com/en-us/typography/opentype/spec/recom#glyph-0-the-notdef-glyph
        if ".notdef" in new_glyph_order:
            new_glyph_order.remove(".notdef")
            new_glyph_order.insert(0, ".notdef")

        if old_glyph_order == new_glyph_order:
            return False

        font.ttfont.reorderGlyphs(new_glyph_order=new_glyph_order)

        return True

    except Exception as e:
        raise SortGlyphsError(e) from e
