# pylint: disable=import-outside-toplevel
from collections import Counter
from typing import Union

from foundrytools import Font


class FixMonospaceError(Exception):
    """Raised when an error occurs in the fix_monospace method."""


# Copied from fontbakery/profiles/shared_conditions.py
def _get_glyph_metrics_stats(font: Font) -> dict[str, Union[bool, int]]:
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
    glyph_metrics = font.t_hmtx.table.metrics
    # NOTE: `range(a, b)` includes `a` and does not include `b`.
    #       Here we don't include 0-31 as well as 127
    #       because these are control characters.
    ascii_glyph_names = [
        font.ttfont.getBestCmap()[c] for c in range(32, 127) if c in font.ttfont.getBestCmap()
    ]

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
        for value, name in font.ttfont.getBestCmap().items():
            if unicodedata.category(chr(value)).startswith(("L", "M", "N", "P", "S", "Zs")):
                relevant_glyph_names.add(name)
        # Remove character glyphs that are mark glyphs.
        gdef = font.t_gdef.table
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


def run(font: Font) -> bool:
    """
    Fix the monospace attribute of a font.

    :param font: The Font.
    :type font: Font
    :return: Whether the font was modified.
    """
    try:
        glyph_metrics = _get_glyph_metrics_stats(font)
        seems_monospaced = glyph_metrics["seems_monospaced"]
        width_max = glyph_metrics["width_max"]

        if seems_monospaced:
            font.t_post.fixed_pitch = True
            font.t_os_2.table.panose.bFamilyType = 2
            font.t_os_2.table.panose.bProportion = 9
            font.t_hhea.advance_width_max = width_max

            modified = font.t_os_2.is_modified or font.t_post.is_modified or font.t_hhea.is_modified

            if font.is_ps and not font.t_cff_.top_dict.isFixedPitch:
                font.t_cff_.top_dict.isFixedPitch = True
                modified = True

            return modified

        return False

    except Exception as e:
        raise FixMonospaceError(f"{e}") from e
