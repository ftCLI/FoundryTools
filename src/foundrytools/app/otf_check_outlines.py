"""OTF check outlines."""

from __future__ import annotations

from afdko import checkoutlinesufo

from foundrytools import Font
from foundrytools.utils.misc import restore_flavor


class CheckOutlinesError(Exception):
    """Raised when an error occurs while checking the CFF table."""


def run(font: Font, *, drop_hinting_data: bool = False) -> bool:
    """
    Run the checkoutlinesufo tool on the font.

    :param font: The font to check the outlines of.
    :type font: Font
    :param drop_hinting_data: Whether to drop the hinting data when checking the outlines.
    :type drop_hinting_data: bool
    :return: ``True`` if the outlines were checked, ``False`` otherwise.
    :rtype: bool
    :raises CheckOutlinesError: If an error occurred while checking the outlines.
    """
    if not font.is_ps:
        msg = "Not a PostScript font."
        raise CheckOutlinesError(msg)

    try:
        with restore_flavor(font.ttfont):
            # Make a copy of the hinting data before checking the outlines, in case we need to
            # restore it later.
            hinthing_data = font.t_cff_.get_hinting_data() if not drop_hinting_data else None

            font.save(font.temp_file)
            checkoutlinesufo.run(args=[font.temp_file.as_posix(), "--error-correction-mode"])
            temp_font = Font(font.temp_file)
            font.ttfont = temp_font.ttfont

            if hinthing_data and not drop_hinting_data:
                font.reload()  # DO NOT REMOVE
                font.t_cff_.set_hinting_data(**hinthing_data)

            return True

    except Exception as e:
        raise CheckOutlinesError(type(e).__name__) from e
