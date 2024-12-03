from collections.abc import Iterator
from contextlib import contextmanager

from fontTools.pens.boundsPen import BoundsPen
from fontTools.ttLib import TTFont


@contextmanager
def restore_flavor(font: TTFont) -> Iterator[None]:
    """
    This context manager is used to temporarily set the font flavor to None and restore it after
    operations that require the flavor to be None (e.g.: subroutinization or desubroutinization).

    :param font: The TTFont object.
    :type font: TTFont
    :return: A generator that yields.
    :rtype: Iterator[None]
    """
    original_flavor = font.flavor
    font.flavor = None
    try:
        yield
    finally:
        font.flavor = original_flavor


def get_glyph_bounds(font: TTFont, glyph_name: str) -> dict[str, float]:
    """
    Get the bounding box of a glyph.

    :param font: The TTFont object.
    :type font: TTFont
    :param glyph_name: The name of the glyph.
    :type glyph_name: str
    :return: The bounds of the glyph.
    :rtype: dict[str, float]
    """
    glyph_set = font.getGlyphSet()
    if glyph_name not in glyph_set:
        raise ValueError(f"Glyph '{glyph_name}' does not exist in the font.")

    bounds_pen = BoundsPen(glyphSet=glyph_set)

    glyph_set[glyph_name].draw(bounds_pen)
    bounds = {
        "xMin": bounds_pen.bounds[0],
        "yMin": bounds_pen.bounds[1],
        "xMax": bounds_pen.bounds[2],
        "yMax": bounds_pen.bounds[3],
    }

    return bounds
