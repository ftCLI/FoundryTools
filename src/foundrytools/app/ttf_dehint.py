from dehinter.font import dehint

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
        raise NotImplementedError("Not a TrueType font.")

    try:
        dehint(font.ttfont, verbose=False)
        return True
    except Exception as e:
        raise TTFDehintError(e) from e
