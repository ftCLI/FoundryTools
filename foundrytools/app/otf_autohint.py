from typing import Any

from afdko.otfautohint.__main__ import _validate_path
from afdko.otfautohint.autohint import ACOptions, FontInstance, fontWrapper, openFont

from foundrytools import Font
from foundrytools.utils.misc import restore_flavor


class OTFAutohintError(Exception):
    """Raised when there is an error autohinting a font."""


def run(font: Font, **kwargs: dict[str, Any]) -> bool:
    """
    Autohint the font using the AFDKO autohinting process.

    :param font: The font to autohint.
    :type font: Font
    :param kwargs: Additional options to pass to the autohinting process.
    :type kwargs: dict[str, Any]
    """
    if not font.is_ps:
        raise NotImplementedError("Not a PostScript font.")

    try:
        options = ACOptions()
        for key, value in kwargs.items():
            setattr(options, key, value)

        with restore_flavor(font.ttfont):
            font.save(font.temp_file)
            in_file = _validate_path(font.temp_file)
            fw_font = openFont(in_file, options=options)
            font_instance = FontInstance(font=fw_font, inpath=in_file, outpath=None)
            fw = fontWrapper(options=options, fil=[font_instance])
            fw.hint()
            font.ttfont = fw.fontInstances[0].font.ttFont
            return True
    except Exception as e:
        raise OTFAutohintError(e) from e
