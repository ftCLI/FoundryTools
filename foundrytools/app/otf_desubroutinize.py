from cffsubr import desubroutinize

from foundrytools import Font


class DesubroutinizeError(Exception):
    """Raised when an error occurs while subroutinizing the CFF table."""


def run(font: Font) -> bool:
    """
    Desubroutinize the CFF table of a font.

    :param font: The font to desubroutinize.
    :type font: Font
    :return: True if the font was desubroutinized successfully.
    :rtype: bool
    :raises DesubroutinizeError: If an error occurs while desubroutinizing the font.
    """
    if not font.is_ps:
        raise NotImplementedError("Not a PostScript font.")

    try:
        desubroutinize(font.ttfont)
        return True
    except Exception as e:
        raise DesubroutinizeError(e) from e
