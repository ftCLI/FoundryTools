# pylint: disable=import-outside-toplevel
from collections import Counter
from collections.abc import Iterator
from contextlib import contextmanager
from typing import Union

from fontTools.pens.boundsPen import BoundsPen
from fontTools.ttLib import TTFont

from foundrytools.constants import T_GDEF, T_HMTX


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


# Copied from fontbakery/profiles/shared_conditions.py
def get_glyph_metrics_stats(font: TTFont) -> dict[str, Union[bool, int]]:
    """
    Returns a dict containing whether the font seems_monospaced, what's the maximum glyph width and
    what's the most common width.

    For a font to be considered monospaced, if at least 80% of ASCII characters have glyphs, then at
    least 80% of those must have the same width, otherwise all glyphs of printable characters must
    have one of two widths or be zero-width.

    :param font: The TTFont object.
    :type font: TTFont
    :return: A dictionary containing the metrics.
    :rtype: dict[str, Union[bool, int]]
    """
    glyph_metrics = font[T_HMTX].metrics
    # NOTE: `range(a, b)` includes `a` and does not include `b`.
    #       Here we don't include 0-31 as well as 127
    #       because these are control characters.
    ascii_glyph_names = [font.getBestCmap()[c] for c in range(32, 127) if c in font.getBestCmap()]

    if len(ascii_glyph_names) > 0.8 * (127 - 32):
        ascii_widths = [
            adv
            for name, (adv, lsb) in glyph_metrics.items()
            if name in ascii_glyph_names and adv != 0
        ]
        ascii_width_count = Counter(ascii_widths)
        ascii_most_common_width = ascii_width_count.most_common(1)[0][1]
        seems_monospaced = ascii_most_common_width >= len(ascii_widths) * 0.8
    else:
        from fontTools import unicodedata

        # Collect relevant glyphs.
        relevant_glyph_names = set()
        # Add character glyphs that are in one of these categories:
        # Letter, Mark, Number, Punctuation, Symbol, Space_Separator.
        # This excludes Line_Separator, Paragraph_Separator and Control.
        for value, name in font.getBestCmap().items():
            if unicodedata.category(chr(value)).startswith(("L", "M", "N", "P", "S", "Zs")):
                relevant_glyph_names.add(name)
        # Remove character glyphs that are mark glyphs.
        gdef = font.get(T_GDEF)
        if gdef and gdef.table.GlyphClassDef:
            marks = {name for name, c in gdef.table.GlyphClassDef.classDefs.items() if c == 3}
            relevant_glyph_names.difference_update(marks)

        widths = sorted(
            {
                adv
                for name, (adv, lsb) in glyph_metrics.items()
                if name in relevant_glyph_names and adv != 0
            }
        )
        seems_monospaced = len(widths) <= 2

    width_max = max(adv for k, (adv, lsb) in glyph_metrics.items())
    most_common_width = Counter([g for g in glyph_metrics.values() if g[0] != 0]).most_common(1)[0][
        0
    ][0]
    return {
        "seems_monospaced": seems_monospaced,
        "width_max": width_max,
        "most_common_width": most_common_width,
    }