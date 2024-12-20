from ufo2ft.postProcessor import PostProcessor

from foundrytools import Font
from foundrytools.lib.unicode import unicode_from_glyph_name, production_name_from_unicode


class SetProdNamesError(Exception):
    """Raised when an error occurs in the set_production_names method."""


def run(font: Font) -> list[tuple[str, str]]:
    """
    Set the production names for the glyphs in the font.

    The method iterates through each glyph in the old glyph order and determines its production name
    based on its assigned or calculated Unicode value. If the production name is already assigned,
    the glyph is skipped. If the production name is different from the original glyph name and is
    not yet assigned, the glyph is renamed and added to the new glyph order list. Finally, the font
    is updated with the new glyph order, the cmap table is rebuilt, and the list of renamed glyphs
    is returned.

    :return: A list of tuples containing the old and new glyph names.
    :rtype: List[Tuple[str, str]]
    :raises SetProdNamesError: If an error occurs during the process.
    """

    try:
        old_glyph_order: list[str] = font.ttfont.getGlyphOrder()
        reversed_cmap = font.t_cmap.table.buildReversed()
        new_glyph_order: list[str] = []
        renamed_glyphs: list[tuple[str, str]] = []

        for glyph_name in old_glyph_order:
            unicode_string = unicode_from_glyph_name(glyph_name, reversed_cmap)
            # If still no uni_str, the glyph name is unmodified.
            if not unicode_string:
                new_glyph_order.append(glyph_name)
                continue

            # In case the production name could not be found, the glyph is already named with
            # the production name, or the production name is already assigned, we skip the
            # renaming process.
            production_name = production_name_from_unicode(unicode_string)
            if (
                not production_name
                or production_name == glyph_name
                or production_name in old_glyph_order
            ):
                new_glyph_order.append(glyph_name)
                continue

            new_glyph_order.append(production_name)
            renamed_glyphs.append((glyph_name, production_name))

        if not renamed_glyphs:
            return []

        rename_map = dict(zip(old_glyph_order, new_glyph_order))
        PostProcessor.rename_glyphs(otf=font.ttfont, rename_map=rename_map)
        font.t_cmap.rebuild_character_map(remap_all=True)

        return renamed_glyphs

    except Exception as e:
        raise SetProdNamesError(e) from e
