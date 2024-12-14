from pathlib import Path
from typing import Optional

from afdko.otfautohint.__main__ import ReportOptions, _validate_path, get_stemhist_options
from afdko.otfautohint.autohint import FontInstance, fontWrapper, openFont
from afdko.otfautohint.hinter import glyphHinter
from afdko.otfautohint.report import Report

H_STEM_GLYPHS = ["A", "H", "T", "S", "C", "O"]
V_STEM_GLYPHS = ["E", "H", "I", "K", "L", "M", "N", "T", "U"]


def get_report(
    file_path: Path, glyph_list: list[str], report_all_stems: bool = True
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
    h_stems_glyphs: Optional[list[str]] = None,
    v_stems_glyphs: Optional[list[str]] = None,
) -> tuple[int, int]:
    """
    Recalculates the StdHW and StdVW values.

    :param file_path: The path to the font file.
    :type file_path: Path
    :param h_stems_glyphs: A list of glyphs to use for horizontal stems.
    :type h_stems_glyphs: list
    :param v_stems_glyphs: A list of glyphs to use for vertical stems.
    :type v_stems_glyphs: list
    :return: A tuple containing the new StdHW and StdVW values.
    :rtype: tuple[int, int]
    """

    h_stems_glyphs = h_stems_glyphs or H_STEM_GLYPHS
    v_stems_glyphs = v_stems_glyphs or V_STEM_GLYPHS

    h_stems, _ = get_report(file_path=file_path, glyph_list=h_stems_glyphs)
    _, v_stems = get_report(file_path=file_path, glyph_list=v_stems_glyphs)

    if not h_stems:
        raise RuntimeError("No horizontal stems found")
    if not v_stems:
        raise RuntimeError("No vertical stems found")

    return int(h_stems[0][1]), int(v_stems[0][1])
