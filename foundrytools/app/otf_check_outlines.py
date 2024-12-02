from afdko import checkoutlinesufo

from foundrytools import Font
from foundrytools.utils.misc import restore_flavor


class CheckOutlinesError(Exception):
    """Raised when an error occurs while checking the CFF table."""


def run(font: Font, drop_hinting_data: bool = False) -> bool:
    """Check the outlines of a PostScript font."""

    if not font.is_ps:
        raise NotImplementedError("Not a PostScript font.")

    try:
        with restore_flavor(font.ttfont):
            hinthing_data = font.cff.get_hinting_data() if not drop_hinting_data else None
            font.save(font.temp_file)
            checkoutlinesufo.run(args=[font.temp_file.as_posix(), "--error-correction-mode"])
            temp_font = Font(font.temp_file)
            font.ttfont = temp_font.ttfont
            if hinthing_data and not drop_hinting_data:
                font.reload()  # DO NOT REMOVE
                font.cff.set_hinting_data(**hinthing_data)
            return True
    except Exception as e:
        raise CheckOutlinesError(type(e).__name__) from e
