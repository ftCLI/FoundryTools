"""OTF autohint."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from afdko.otfautohint.__main__ import _validate_path
from afdko.otfautohint.autohint import ACOptions, FontInstance, fontWrapper, openFont

from foundrytools.utils.misc import restore_flavor

if TYPE_CHECKING:
    from foundrytools import Font


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
        msg = "Not a PostScript font."
        raise NotImplementedError(msg)

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
