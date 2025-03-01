from foundrytools import Font


class OTFDehintError(Exception):
    """Raised when an error occurs while dehinting a font."""


def run(font: Font, drop_hinting_data: bool = False) -> bool:
    """
    Dehint a PostScript font.

    :param font: The font to dehint.
    :type font: Font
    :param drop_hinting_data: If ``True``, drop hinting data from the CFF table. Defaults to
        ``False``.
    :type drop_hinting_data: bool
    :return: A boolean indicating whether the ``CFF`` table has been modified.
    :rtype: bool
    """
    if not font.is_ps:
        raise NotImplementedError("Not a PostScript font.")

    try:
        font.t_cff_.remove_hinting(drop_hinting_data=drop_hinting_data)
        return True
    except Exception as e:
        raise OTFDehintError(e) from e
