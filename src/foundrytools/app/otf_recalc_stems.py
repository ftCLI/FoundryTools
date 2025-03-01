"""
TTF dehint.

Provides functionality to recalculate the standard horizontal and vertical stem widths
(**StdHW** and **StdVW**) and the horizontal and vertical stem snap arrays (**StemSnapH** and
**StemSnapV**) for OpenType font files.

The module includes the following key functions:

1. **_get_report**:
   Generates a report of horizontal and vertical stems for a given font file. It uses the
   `afdko.otfautohint` library to parse the font file and extract stem information. The report
   can optionally include stems formed by curved line segments.

2. **_group_widths_with_neighbors**:
   Groups report entries based on their width and proximity to neighboring widths. Entries are
   grouped together if their widths are within a specified maximum distance from each other. This
   helps in identifying clusters of similar stem widths.

3. **_get_first_n_stems**:
   Extracts a specified number of representative stem values from the grouped stems. It ensures
   that the selected values maintain a minimum difference of five units to provide optimal results,
   as per technical recommendations.

4. **_sort_groups_by_count_sum and _sort_groups_by_max_count**:
   Sort the groups of stems based on the sum of counts and the maximum count within each group,
   respectively. These sorting functions help in prioritizing the most significant stem groups.

5. **run**:
   Orchestrates the entire recalculation process. It takes the path to the font file and various
   parameters, generates the stem reports, groups the widths, extracts the representative stem
   values, and returns the new StdHW, StdVW, StemSnapH, and StemSnapV values.

The module relies on the `afdko.otfautohint` library for font parsing and stem extraction.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from afdko.otfautohint.__main__ import ReportOptions, _validate_path, get_stemhist_options
from afdko.otfautohint.autohint import FontInstance, fontWrapper, openFont
from afdko.otfautohint.hinter import glyphHinter
from afdko.otfautohint.report import Report

if TYPE_CHECKING:
    from pathlib import Path

__all__ = ["run"]


def _get_report(
    file_path: Path, glyph_list: list[str] | None, *, report_all_stems: bool = False
) -> tuple[list[tuple[int, int, list[str]]], list[tuple[int, int, list[str]]]]:
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

    h_stems, v_stems, _, _ = report._get_lists(options)  # noqa: SLF001
    h_stems.sort(key=report._sort_count)  # noqa: SLF001
    v_stems.sort(key=report._sort_count)  # noqa: SLF001

    return h_stems, v_stems


def _group_widths_with_neighbors(  # noqa: D417
    report: list[tuple[int, int, list[str]]], max_distance: int = 2
) -> list[list[tuple[int, int]]]:
    """
    Group report entries based on their width and proximity to neighboring widths.

    This function takes a report containing tuples of a unique identifier, a width,
    and a list of associated strings. It groups entries together based on their widths
    and their proximity to neighboring widths within a specified maximum distance.
    Neighboring widths in the range `[width - max_distance, width + max_distance]`
    are identified, and groups are sorted by an identifier in descending order.

    Parameters
    ----------
        report: list of tuples, where each tuple contains:
            - A unique identifier (int)
            - A width value (int)
            - Associated strings (list of str)
        max_distance: (int, optional) Maximum proximity range to consider neighbors.
            Defaults to 2.

    Returns
    -------
        list of lists: Nested list where each sub-list contains tuples representing
        grouped width-proximity neighbors. Each tuple contains:
            - A unique identifier (int)
            - A width value (int)

    """
    groups = []  # This will store the resulting groups

    # Create a mapping of widths to their respective entries
    width_map = {entry[1]: (entry[0], entry[1]) for entry in report}

    # Iterate over each entry in the report
    for _, width, _ in report:
        # Find all widths within the range [width - max_distance, width + max_distance]
        group = [
            width_map[neighbor_width]
            for neighbor_width in range(width - max_distance, width + max_distance + 1)
            if neighbor_width in width_map
        ]
        # Sort the group by width
        group.sort(key=lambda x: x[0], reverse=True)
        groups.append(group)  # Append the built group to the result

    return groups


def _sort_groups_by_count_sum(groups: list[list[tuple[int, int]]]) -> list[list[tuple[int, int]]]:
    return sorted(groups, key=lambda x: sum(e[0] for e in x), reverse=True)


def _sort_groups_by_max_count(groups: list[list[tuple[int, int]]]) -> list[list[tuple[int, int]]]:
    return sorted(groups, key=lambda x: max(e[0] for e in x), reverse=True)


def _get_first_n_stems(
    groups: list[list[tuple[int, int]]],
    number_of_stems: int,
) -> list[int]:
    """
    Extract a specified number of representative stem values from groups of stems.

    Ensures that selected values maintain a minimum difference of five units
    to provide optimal results as per technical recommendations.

    From: https://adobe-type-tools.github.io/font-tech-notes/pdfs/5049.StemSnap.pdf

    "It is important that only the mean value of groups of stems be entered in the array. Entering
    values that are too close together, such as [ 121, 122, ... 172, 174...] might produce
    undesirable results. Hence, it is recommended that values be a minimum of five units apart."

    :param groups: A list of grouped stems, where each group contains a list of tuples comprising
        stem value and count.
    :type groups: list
    :param number_of_stems: The number of stem values to extract from the groups.
    :type number_of_stems: int
    :return: A list of representative stem values.
    :rtype: list[int]
    """
    stem_snap: list[int] = []
    for group in _sort_groups_by_count_sum(groups):
        max_value = max(group, key=lambda x: x[0])[1]
        if any(abs(max_value - used) < 5 for used in stem_snap):  # noqa: PLR2004
            continue
        stem_snap.append(max_value)
    return sorted(stem_snap[:number_of_stems])


def run(
    file_path: Path,
    *,
    report_all_stems: bool = False,
    max_distance: int = 1,
    max_h_stems: int = 2,
    max_v_stems: int = 2,
) -> tuple[int, int, list[int] | None, list[int] | None]:
    """
    Recalculates the StdHW, StdVW, StemSnapH, and StemSnapV values for a font file.

    :param file_path: The path to the font file.
    :type file_path: Path
    :param report_all_stems: Include stems formed by curved line segments; by default, includes only
        stems formed by straight line segments.
    :type report_all_stems: bool
    :param max_distance: The maximum distance between widths to consider as part of the same group.
    :type max_distance: int
    :param max_h_stems: The number of horizontal stem values to extract.
    :type max_h_stems: int
    :param max_v_stems: The number of vertical stem values to extract.
    :type max_v_stems: int
    :return: A tuple containing the new StdHW, StdVW, StemSnapH, and StemSnapV values.
    :rtype: tuple[int, int, list[int], list[int]]
    """
    horizontal_report, vertical_report = _get_report(file_path, None, report_all_stems=report_all_stems)

    h_groups = _group_widths_with_neighbors(horizontal_report, max_distance=max_distance)
    v_groups = _group_widths_with_neighbors(vertical_report, max_distance=max_distance)

    std_h_w = _get_first_n_stems(h_groups, 1)[0]
    stem_snap_h = _get_first_n_stems(h_groups, max_h_stems) if max_h_stems > 1 else None
    std_v_w = _get_first_n_stems(v_groups, 1)[0]
    stem_snap_v = _get_first_n_stems(v_groups, max_v_stems) if max_v_stems > 1 else None

    return std_h_w, std_v_w, stem_snap_h, stem_snap_v
