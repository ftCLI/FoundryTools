from typing import Optional

from fontTools.subset import Options, Subsetter

from foundrytools import Font
from foundrytools.constants import SUBSETTER_DEFAULTS


class RemoveGlyphsError(Exception):
    """Exception raised for errors in removing glyphs from a font object."""


def run(
    font: Font,
    glyph_names_to_remove: Optional[set[str]],
    glyph_ids_to_remove: Optional[set[int]],
) -> set[str]:
    """
    Removes glyphs from the font using the fontTools subsetter.

    :param font: The font object.
    :type font: Font
    :param glyph_names_to_remove: A set of glyph names to remove.
    :type glyph_names_to_remove: Optional[set[str]]
    :param glyph_ids_to_remove: A set of glyph IDs to remove.
    :type glyph_ids_to_remove: Optional[set[int]]
    :return: A set of glyph names that were removed.
    :rtype: set[str]
    """
    try:
        old_glyph_order = font.ttfont.getGlyphOrder()
        if not glyph_names_to_remove and not glyph_ids_to_remove:
            raise ValueError("No glyph names or glyph IDs provided to remove.")

        glyph_names_to_remove = glyph_names_to_remove or set()

        # Convert glyph IDs to glyph names to populate the subsetter with only one parameter.
        if glyph_ids_to_remove:
            for glyph_id in glyph_ids_to_remove:
                if glyph_id < 0 or glyph_id >= len(old_glyph_order):
                    continue
                glyph_names_to_remove.add(old_glyph_order[glyph_id])

        if not glyph_names_to_remove:
            return set()

        remaining_glyphs = {gn for gn in old_glyph_order if gn not in glyph_names_to_remove}
        options = Options(**SUBSETTER_DEFAULTS)
        options.recalc_timestamp = font.ttfont.recalcTimestamp

        subsetter = Subsetter(options=options)
        subsetter.populate(glyphs=remaining_glyphs)
        subsetter.subset(font.ttfont)

        new_glyph_order = font.ttfont.getGlyphOrder()
        return set(old_glyph_order).difference(new_glyph_order)

    except Exception as e:
        raise RemoveGlyphsError(e) from e
