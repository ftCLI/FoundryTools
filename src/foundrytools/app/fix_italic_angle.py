"""Fix italic angle."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from fontTools.misc.roundTools import otRound

if TYPE_CHECKING:
    from foundrytools import Font


class FixItalicAngleError(Exception):
    """Raised when an error occurs while fixing the italic angle of a font."""


def run(font: Font, *, min_slant: float = 2.0, italic: bool = True, oblique: bool = False) -> dict[str, dict[str, Any]]:
    """
    Fix the italic angle of the font.

    This method calculates the italic angle of the font and updates the ``post`` and ``hhea``
    tables with the new values if they differ from the current values. If the font is a
    PostScript font, the ``CFF`` table is also updated. The method also updates the italic and
    oblique bits in the ``OS/2`` and `head` tables.

    :param font: The ``Font`` to process.
    :type font: Font
    :param min_slant: The minimum slant value to consider the font italic. Defaults to 2.0.
    :type min_slant: float
    :param italic: If ``True``, set the font to italic when the italic angle is not zero.
        Defaults to ``True``.
    :type italic: bool
    :param oblique: If ``True``, set the font to oblique when the italic angle is not zero.
        Defaults to ``False``.
    :return: A dictionary containing the old and new values of the italic angle and the run/rise
             values, along with a check result indicating whether the values were updated.
    :rtype: dict[str, dict[str, Any]]
    """
    result: dict[str, dict[str, Any]] = {}
    try:
        is_italic = font.flags.is_italic
        is_oblique = font.flags.is_oblique
        post_italic_angle = font.t_post.italic_angle
        hhea_run_rise = (font.t_hhea.caret_slope_run, font.t_hhea.caret_slope_rise)
        run_rise_angle = font.t_hhea.run_rise_angle

        # Calculate the italic angle and the caret slope run and rise values.
        calculated_slant = font.calc_italic_angle(min_slant=min_slant)
        calculated_run = font.t_hhea.calc_caret_slope_run(italic_angle=calculated_slant)
        calculated_rise = font.t_hhea.calc_caret_slope_rise(italic_angle=calculated_slant)

        # Check if the ``is_italic`` attribute is correctly set.
        should_be_italic = italic and calculated_slant != 0.0
        italic_bits_check = is_italic == should_be_italic
        if not italic_bits_check:
            font.flags.is_italic = should_be_italic
        result["is_italic"] = {
            "old": is_italic,
            "new": should_be_italic,
            "pass": italic_bits_check,
        }

        # Check if the ``is_oblique`` attribute is correctly set. The oblique bit is only
        # defined in ``OS/2`` table version 4 and later.
        should_be_oblique = oblique and calculated_slant != 0.0 and font.t_os_2.version >= 4  # noqa: PLR2004
        oblique_bit_check = is_oblique == should_be_oblique
        if not oblique_bit_check:
            font.flags.is_oblique = should_be_oblique
        result["is_oblique"] = {
            "old": is_oblique,
            "new": should_be_oblique,
            "pass": oblique_bit_check,
        }

        # Check if the italic is correctly set in the ``post`` table.
        italic_angle_check = otRound(post_italic_angle) == otRound(calculated_slant)
        if not italic_angle_check:
            font.t_post.italic_angle = calculated_slant
        result["italic_angle"] = {
            "old": post_italic_angle,
            "new": calculated_slant,
            "pass": italic_angle_check,
        }

        # Check if the run/rise values are correctly set in the ``hhea`` table.
        run_rise_check = otRound(run_rise_angle) == otRound(calculated_slant)
        if not run_rise_check:
            font.t_hhea.caret_slope_run = calculated_run
            font.t_hhea.caret_slope_rise = calculated_rise
        result["run_rise"] = {
            "old": hhea_run_rise,
            "new": (calculated_run, calculated_rise),
            "pass": run_rise_check,
        }

        if font.is_ps:
            cff_italic_angle = font.t_cff_.top_dict.ItalicAngle
            cff_italic_angle_check = otRound(cff_italic_angle) == otRound(calculated_slant)
            if not cff_italic_angle_check:
                font.t_cff_.top_dict.ItalicAngle = otRound(calculated_slant)
            result["cff_italic_angle"] = {
                "old": cff_italic_angle,
                "new": calculated_slant,
                "pass": cff_italic_angle_check,
            }

    except Exception as e:
        raise FixItalicAngleError(e) from e

    return result
