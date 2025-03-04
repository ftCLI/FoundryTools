"""Fix empty notdef."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from fontTools.misc.roundTools import otRound
from fontTools.pens.recordingPen import RecordingPen
from fontTools.pens.t2CharStringPen import T2CharStringPen
from fontTools.pens.ttGlyphPen import TTGlyphPen

if TYPE_CHECKING:
    from fontTools.misc.psCharStrings import T2CharString
    from fontTools.ttLib.tables._g_l_y_f import Glyph

    from foundrytools import Font

logger = logging.getLogger(__name__)

NOTDEF = ".notdef"
WIDTH_CONSTANT = 600
HEIGHT_CONSTANT = 1.25
THICKNESS_CONSTANT = 10


class DrawNotdefError(Exception):
    """Raised when there is an error drawing the '.notdef' glyph."""


class DrawNotdefCFFError(DrawNotdefError):
    """Raised when there is an error drawing the '.notdef' glyph in a CFF font."""


class DrawNotdefTTError(DrawNotdefError):
    """Raised when there is an error drawing the '.notdef' glyph in a TTF font."""


def draw_notdef_cff(font: Font, width: int, height: int, thickness: int, cs_width: int | None = None) -> T2CharString:
    """
    Draws a '.notdef' glyph in a CFF font.

    :param font: The ``Font`` object.
    :type font: Font
    :param width: The width of the '.notdef' glyph.
    :type width: int
    :param height: The height of the '.notdef' glyph.
    :type height: int
    :param thickness: The thickness of the '.notdef' glyph.
    :type thickness: int
    :param cs_width: The width of the '.notdef' glyph to set in the CharString.
    :type cs_width: Optional[int]
    :return: The '.notdef' glyph.
    :rtype: T2CharString
    """
    try:
        pen = T2CharStringPen(width=cs_width, glyphSet=font.ttfont.getGlyphSet())
        glyph_set = font.ttfont.getGlyphSet()

        # Draw the outer contour (counterclockwise)
        pen.moveTo((0, 0))
        pen.lineTo((width, 0))
        pen.lineTo((width, height))
        pen.lineTo((0, height))
        pen.closePath()

        # Draw the inner contour (clockwise)
        pen.moveTo((thickness, thickness))
        pen.lineTo((thickness, height - thickness))
        pen.lineTo((width - thickness, height - thickness))
        pen.lineTo((width - thickness, thickness))
        pen.closePath()

        glyph_set[NOTDEF].draw(pen)
        charstring = pen.getCharString()

    except Exception as e:
        msg = f"Error drawing '.notdef' glyph in CFF font: {e}"
        raise DrawNotdefCFFError(msg) from e

    return charstring


def draw_notdef_glyf(font: Font, width: int, height: int, thickness: int) -> Glyph:
    """
    Draws a '.notdef' glyph in a TTF font.

    :param font: The ``Font`` object.
    :type font: Font
    :param width: The width of the '.notdef' glyph.
    :type width: int
    :param height: The height of the '.notdef' glyph.
    :type height: int
    :param thickness: The thickness of the '.notdef' glyph.
    :type thickness: int
    :return: The '.notdef' glyph.
    :rtype: Glyph
    """
    try:
        # Be aware: TTGlyphPen expects a dict[str, Any] object, not a _TTGlyphSet object
        pen = TTGlyphPen(glyphSet=font.ttfont.getGlyphSet())
        glyph_set = font.ttfont.getGlyphSet()

        # Draw the outer contour (clockwise)
        pen.moveTo((0, 0))
        pen.lineTo((0, height))
        pen.lineTo((width, height))
        pen.lineTo((width, 0))
        pen.closePath()

        # Draw the inner contour (counterclockwise)
        pen.moveTo((thickness, thickness))
        pen.lineTo((width - thickness, thickness))
        pen.lineTo((width - thickness, height - thickness))
        pen.lineTo((thickness, height - thickness))
        pen.closePath()

        glyph_set[NOTDEF].draw(pen)
        return pen.glyph()
    except Exception as e:
        msg = f"Error drawing '.notdef' glyph in TTF font: {e}"
        raise DrawNotdefTTError(msg) from e


def run(font: Font) -> bool:
    """
    If the '.notdef' glyph is empty, draws a simple rectangle in it.

    :param font: The Font object.
    :type font: Font
    :return: True if the '.notdef' glyph was fixed, False otherwise.
    :rtype: bool
    """
    try:
        glyph_set = font.ttfont.getGlyphSet()

        if NOTDEF not in glyph_set:
            logger.warning("Font does not contain a '.notdef' glyph")
            return False

        rec_pen = RecordingPen()
        glyph_set[NOTDEF].draw(rec_pen)
        if rec_pen.value:
            logger.warning("The '.notdef' glyph is not empty")
            return False

        width = otRound(font.t_head.units_per_em / 1000 * WIDTH_CONSTANT)
        height = width * HEIGHT_CONSTANT
        thickness = otRound(width / THICKNESS_CONSTANT)

        if font.is_ps:
            cs_width = (
                None
                if width == font.t_cff_.private_dict.defaultWidthX
                else width - font.t_cff_.private_dict.nominalWidthX
            )
            charstring = draw_notdef_cff(font=font, width=width, height=height, thickness=thickness, cs_width=cs_width)
            charstring.compile()
            font.t_cff_.top_dict.CharStrings[NOTDEF].setBytecode(charstring.bytecode)

        if font.is_tt:
            glyph = draw_notdef_glyf(font=font, width=width, height=height, thickness=thickness)
            font.t_glyf.table[NOTDEF] = glyph

        font.t_hmtx.table[NOTDEF] = (width, 0)

    except (DrawNotdefCFFError, DrawNotdefTTError) as e:
        raise DrawNotdefError from e

    return True
