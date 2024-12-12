from cffsubr import subroutinize

from foundrytools import Font
from foundrytools.utils.misc import restore_flavor


class SubroutinizeError(Exception):
    """Raised when an error occurs while subroutinizing the CFF table."""


def run(font: Font) -> bool:
    """
    Subroutinize the CFF table of a font.

    :param font: The font to subroutinize.
    :type font: Font
    :return: True if the subroutinization process was successful.
    :rtype: bool
    :raises SubroutinizeError: If an error occurs while subroutinizing the font.
    """
    if not font.is_ps:
        raise NotImplementedError("Not a PostScript font.")

    with restore_flavor(font.ttfont):
        try:
            subroutinize(font.ttfont)
            return True
        except Exception as e:
            raise SubroutinizeError(e) from e
