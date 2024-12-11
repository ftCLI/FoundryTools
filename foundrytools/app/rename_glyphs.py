from ufo2ft.postProcessor import PostProcessor

from foundrytools import Font


class RenameGlyphsError(Exception):
    """An error occurred while processing the font."""


def run(font: Font, new_glyph_order: list[str]) -> bool:
    """
    Rename the glyphs in the font based on the new glyph order.

    :param font: The font to rename the glyphs in.
    :type font: Font
    :param new_glyph_order: The new glyph order.
    :type new_glyph_order: List[str]
    :return: ``True`` if the glyphs were renamed, ``False`` otherwise.
    :rtype: bool
    :raises RenameGlyphsError: If an error occurred while renaming the glyphs.
    """
    try:
        old_glyph_order = font.ttfont.getGlyphOrder()
        if new_glyph_order == old_glyph_order:
            return False
        rename_map = dict(zip(old_glyph_order, new_glyph_order))
        PostProcessor.rename_glyphs(otf=font.ttfont, rename_map=rename_map)
        font.t_cmap.rebuild_character_map(remap_all=True)

        return True

    except Exception as e:
        raise RenameGlyphsError(e) from e
