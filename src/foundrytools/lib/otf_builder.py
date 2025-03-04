"""OpenType fonts."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from fontTools.fontBuilder import FontBuilder

from foundrytools.constants import T_CFF, T_HEAD, T_NAME, T_POST

if TYPE_CHECKING:
    from fontTools.misc.psCharStrings import T2CharString
    from fontTools.ttLib import TTFont


def build_otf(
    font: TTFont,
    charstrings_dict: dict[str, T2CharString],
    ps_name: str | None = None,
    font_info: dict[str, Any] | None = None,
    private_dict: dict[str, Any] | None = None,
) -> None:
    """
    Build an OpenType-PS font with ``fontTools.fontBuilder.FontBuilder``.

    :param font: The ``TTFont`` object.
    :type font: TTFont
    :param charstrings_dict: The charstrings dictionary.
    :type charstrings_dict: dict
    :param ps_name: The PostScript name of the font. If None, it will be extracted from the font
        metadata.
    :type ps_name: str, optional
    :param font_info: The font info dictionary. If None, it will be extracted from the font
        metadata.
    :param private_dict: The private dict dictionary. If None, it will be extracted from the font
        metadata.
    :type private_dict: dict, optional
    """
    if not ps_name:
        ps_name = _get_ps_name(font=font)
    if not font_info:
        font_info = _get_font_info_dict(font=font)
    if not private_dict:
        private_dict = _get_private_dict(font=font)

    fb = FontBuilder(font=font)
    fb.isTTF = False
    _delete_ttf_tables(font=fb.font)
    fb.setupGlyphOrder(font.getGlyphOrder())
    fb.setupCFF(
        psName=ps_name,
        charStringsDict=charstrings_dict,
        fontInfo=font_info,
        privateDict=private_dict,
    )
    metrics = _get_hmtx_values(font=fb.font, charstrings=charstrings_dict)
    fb.setupHorizontalMetrics(metrics)
    fb.setupDummyDSIG()
    fb.setupMaxp()
    post_values = _get_post_values(font=fb.font)
    fb.setupPost(**post_values)


def _delete_ttf_tables(font: TTFont) -> None:
    ttf_tables = ["glyf", "cvt ", "loca", "fpgm", "prep", "gasp", "LTSH", "hdmx"]
    for table in ttf_tables:
        if table in font:
            del font[table]


def _get_ps_name(font: TTFont) -> str:
    if T_CFF not in font:
        return font[T_NAME].getDebugName(6)

    cff_table = font[T_CFF]
    return cff_table.cff.fontNames[0]


def _get_font_info_dict(font: TTFont) -> dict[str, Any]:
    if T_CFF not in font:
        return _build_font_info_dict(font)

    cff_table = font[T_CFF]
    return {
        key: value
        for key, value in cff_table.cff.topDictIndex[0].rawDict.items()
        if key not in ("FontBBox", "charset", "Encoding", "Private", "CharStrings")
    }


def _build_font_info_dict(font: TTFont) -> dict[str, Any]:
    font_revision = str(round(font[T_HEAD].fontRevision, 3)).split(".")
    major_version = str(font_revision[0])
    minor_version = str(font_revision[1]).ljust(3, "0")

    name_table = font[T_NAME]
    post_table = font[T_POST]
    return {
        "version": ".".join([major_version, str(int(minor_version))]),
        "FullName": name_table.getBestFullName(),
        "FamilyName": name_table.getBestFamilyName(),
        "ItalicAngle": post_table.italicAngle,
        "UnderlinePosition": post_table.underlinePosition,
        "UnderlineThickness": post_table.underlineThickness,
        "isFixedPitch": bool(post_table.isFixedPitch),
    }


def _get_private_dict(font: TTFont) -> dict[str, Any]:
    if T_CFF not in font:
        return {}

    cff_table = font[T_CFF]
    return {
        key: value
        for key, value in cff_table.cff.topDictIndex[0].Private.rawDict.items()
        if key not in ("Subrs", "defaultWidthX", "nominalWidthX")
    }


def _get_hmtx_values(font: TTFont, charstrings: dict[str, T2CharString]) -> dict[str, tuple[int, int]]:
    glyph_set = font.getGlyphSet()
    advance_widths = {k: v.width for k, v in glyph_set.items()}
    lsb = {}
    for gn, cs in charstrings.items():
        lsb[gn] = cs.calcBounds(None)[0] if cs.calcBounds(None) is not None else 0
    metrics = {}
    for gn, advance_width in advance_widths.items():
        metrics[gn] = (advance_width, lsb[gn])
    return metrics


def _get_post_values(font: TTFont) -> dict[str, Any]:
    post_table = font[T_POST]
    return {
        "italicAngle": round(post_table.italicAngle),
        "underlinePosition": post_table.underlinePosition,
        "underlineThickness": post_table.underlineThickness,
        "isFixedPitch": post_table.isFixedPitch,
        "minMemType42": post_table.minMemType42,
        "maxMemType42": post_table.maxMemType42,
        "minMemType1": post_table.minMemType1,
        "maxMemType1": post_table.maxMemType1,
    }
