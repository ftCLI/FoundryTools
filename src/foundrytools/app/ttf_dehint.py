"""TTF dehint."""

from __future__ import annotations

from typing import TYPE_CHECKING

from dehinter.font import dehint

if TYPE_CHECKING:
    from foundrytools import Font


class TTFDehintError(Exception):
    """An error occurred while dehinting a TrueType font."""


def run(font: Font) -> bool:
    """
    Dehint a TrueType font.

    :param font: The Font to dehint.
    :type font: Font
    :raises NotImplementedError: If the font is not a TrueType flavored
    :raises TTFDehintError: If an error occurs while dehinting the font.
    """
    if not font.is_tt:
        msg = "Not a TrueType font."
        raise NotImplementedError(msg)

    try:
        dehint(font.ttfont, verbose=False)
    except Exception as e:
        raise TTFDehintError(e) from e

    return True
