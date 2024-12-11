from ufo2ft.postProcessor import PostProcessor

from foundrytools import Font


class RenameGlyphError(Exception):
    """An error occurred while renaming a glyph."""


def run(font: Font, old_name: str, new_name: str) -> bool:
    """
    Rename a single glyph in the font.

    :param font: The font to rename the glyph in.
    :type font: Font
    :param old_name: The old glyph name.
    :type old_name: str
    :param new_name: The new glyph name.
    :type new_name: str
    :return: ``True`` if the glyph was renamed, ``False`` otherwise.
    :rtype: bool
    """
    try:
        old_glyph_order = font.ttfont.getGlyphOrder()
        new_glyph_order = []

        if old_name not in old_glyph_order:
            raise ValueError(f"Glyph '{old_name}' not found in the font.")

        if new_name in old_glyph_order:
            raise ValueError(f"Glyph '{new_name}' already exists in the font.")

        for glyph_name in old_glyph_order:
            if glyph_name == old_name:
                new_glyph_order.append(new_name)
            else:
                new_glyph_order.append(glyph_name)

        rename_map = dict(zip(old_glyph_order, new_glyph_order))
        PostProcessor.rename_glyphs(otf=font.ttfont, rename_map=rename_map)
        font.t_cmap.rebuild_character_map(remap_all=True)

        return new_glyph_order != old_glyph_order

    except Exception as e:
        raise RenameGlyphError(e) from e
