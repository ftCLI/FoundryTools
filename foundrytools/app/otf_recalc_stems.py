from pathlib import Path

from afdko.otfautohint.__main__ import ReportOptions, _validate_path, get_stemhist_options
from afdko.otfautohint.autohint import FontInstance, fontWrapper, openFont
from afdko.otfautohint.hinter import glyphHinter
from afdko.otfautohint.report import Report


LATIN_UPPERCASE = [chr(i) for i in range(65, 91)]
LATIN_LOWERCASE = [chr(i) for i in range(97, 123)]

CURVED_UC = ["C", "G", "O", "Q", "S"]
CURVED_LC = ["a", "c", "e", "g", "o", "s"]


def get_report(
    file_path: Path, glyph_list: list[str], report_all_stems: bool = False
) -> tuple[list[tuple[int, int, list[str]]], list[tuple[int, int, list[str]]]]:
    """
    Retrieves stem data from a font file for a given list of glyphs.

    :param file_path: The path to the font file.
    :type file_path: Path
    :param glyph_list: A list of glyphs to use for stem data.
    :type glyph_list: list
    :param report_all_stems: Include stems formed by curved line segments; by default, includes only
        stems formed by straight line segments.
    :return: A tuple containing the horizontal and vertical stem data.
    :rtype: tuple[list[tuple[int, int, list[str]]], list[tuple[int, int, list[str]]]]
    """
    file_path = _validate_path(file_path)
    _, parsed_args = get_stemhist_options(args=[file_path])
    options = ReportOptions(parsed_args)
    options.report_all_stems = report_all_stems
    options.report_zones = False
    options.glyphList = glyph_list

    font = openFont(file_path, options=options)
    font_instance = FontInstance(font=font, inpath=file_path, outpath=file_path)

    fw = fontWrapper(options=options, fil=[font_instance])
    dict_record = fw.dictManager.getDictRecord()

    hinter = glyphHinter(options=options, dictRecord=dict_record)
    hinter.initialize(options=options, dictRecord=dict_record)
    gmap = map(hinter.hint, fw)

    report = Report()
    for name, r in gmap:
        report.glyphs[name] = r

    h_stems, v_stems, _, _ = report._get_lists(options)
    h_stems.sort(key=report._sort_count)
    v_stems.sort(key=report._sort_count)

    return h_stems, v_stems


def run(
    file_path: Path,
) -> tuple[int, int, list[int], list[int]]:
    """
    Recalculates the StdHW, StdVW, StemSnapH, and StemSnapV values for a font file.

    :param file_path: The path to the font file.
    :type file_path: Path
    :return: A tuple containing the new StdHW, StdVW, StemSnapH, and StemSnapV values.
    :rtype: tuple[int, int, list[int], list[int]]
    """

    uc_horizontal_straight, _ = get_report(file_path, LATIN_UPPERCASE, report_all_stems=False)
    lc_horizontal_straight, _ = get_report(file_path, LATIN_LOWERCASE, report_all_stems=False)
    _, uc_vertical_straight = get_report(file_path, LATIN_UPPERCASE, report_all_stems=False)
    _, lc_vertical_straight = get_report(file_path, LATIN_LOWERCASE, report_all_stems=False)

    uc_horizontal_curved, _ = get_report(file_path, CURVED_UC, report_all_stems=True)
    lc_horizontal_curved, _ = get_report(file_path, CURVED_LC, report_all_stems=True)
    _, uc_vertical_curved = get_report(file_path, CURVED_UC, report_all_stems=True)
    _, lc_vertical_curved = get_report(file_path, CURVED_LC, report_all_stems=True)

    straight_uc_h_stem = uc_horizontal_straight[0]
    straight_lc_h_stem = lc_horizontal_straight[0]
    straight_uc_v_stem = uc_vertical_straight[0]
    straight_lc_v_stem = lc_vertical_straight[0]

    curved_uc_h_stem = uc_horizontal_curved[0]
    curved_lc_h_stem = lc_horizontal_curved[0]
    curved_uc_v_stem = uc_vertical_curved[0]
    curved_lc_v_stem = lc_vertical_curved[0]

    horizontal_stems = [straight_uc_h_stem, straight_lc_h_stem, curved_uc_h_stem, curved_lc_h_stem]
    std_h_w = max(horizontal_stems, key=lambda x: x[0])[1]
    stem_snap_h = sorted([x[1] for x in horizontal_stems])

    vertical_stems = [straight_uc_v_stem, straight_lc_v_stem, curved_uc_v_stem, curved_lc_v_stem]
    std_v_w = max(vertical_stems, key=lambda x: x[0])[1]
    stem_snap_v = sorted([x[1] for x in vertical_stems])

    return std_h_w, std_v_w, stem_snap_h, stem_snap_v
