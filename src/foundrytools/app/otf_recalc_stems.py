"""
This module provides functionality to recalculate the standard horizontal and vertical stem widths
(**StdHW** and **StdVW**) and the horizontal and vertical stem snap arrays (**StemSnapH** and
**StemSnapV**) for OpenType font files.

By default, each value is calculated from a sample of glyphs with clean, mostly straight stems,
resolved through the font's cmap. Horizontal and vertical stems, and Std and StemSnap values, have
separate samples (``STD_H_CHARS``, ``STD_V_CHARS``, ``SNAP_H_CHARS`` and ``SNAP_V_CHARS``). A
sample that resolves to fewer than ``MIN_SAMPLE_GLYPHS`` glyphs, or that contains no stems, falls
back to the whole font. Samples can be disabled or replaced through the parameters of **run**.

The module includes the following key functions:

1. **_get_report**:
   Analyzes a font file and returns the AFDKO stem report, together with the options used to build
   it. It uses the `afdko.otfautohint` library to parse the font file and extract stem
   information. The report can optionally include stems formed by curved line segments.

2. **_get_stem_lists**:
   Builds the horizontal and vertical stem lists from a report, optionally restricted to a set of
   glyphs. The counts are aggregated across glyphs, so they are rebuilt from the per-glyph data.

3. **_resolve_glyph_names**:
   Maps a collection of codepoints to the glyph names of the font through its cmap, ignoring
   missing codepoints.

4. **_group_widths_with_neighbors**:
   Groups report entries based on their width and proximity to neighboring widths. Entries are
   grouped together if their widths are within a specified maximum distance from each other. This
   helps in identifying clusters of similar stem widths.

5. **_get_first_n_stems**:
   Extracts a specified number of representative stem values from the grouped stems. It ensures
   that the selected values maintain a minimum difference of five units to provide optimal results,
   as per technical recommendations. Optionally, it ignores groups whose count is below a fraction
   of the most frequent one (``MIN_SNAP_COUNT_RATIO``) and values wider than a maximum width
   (``MAX_SNAP_WIDTH_RATIO`` times StdHW or StdVW), which come from pairings of distant edges
   rather than from real stems.

6. **_sort_groups_by_count_sum and _sort_groups_by_max_count**:
   Sort the groups of stems based on the sum of counts and the maximum count within each group,
   respectively. These sorting functions help in prioritizing the most significant stem groups.

7. **run**:
   Orchestrates the entire recalculation process. It takes the path to the font file and various
   parameters, generates the stem reports, groups the widths, extracts the representative stem
   values, and returns the new StdHW, StdVW, StemSnapH, and StemSnapV values. It raises a
   ``ValueError`` if a parameter is out of range or if no stems are found in a direction.

The module relies on the `afdko.otfautohint` library for font parsing and stem extraction.
"""

import logging
from collections.abc import Collection
from pathlib import Path

from afdko.otfautohint.__main__ import ReportOptions, _validate_path, get_stemhist_options
from afdko.otfautohint.autohint import FontInstance, fontWrapper, openFont
from afdko.otfautohint.hinter import glyphHinter
from afdko.otfautohint.report import Report
from fontTools.ttLib import TTFont

__all__ = ["run"]

logger = logging.getLogger(__name__)

# Minimum number of glyphs a sample must resolve to in the font. Smaller samples fall back to
# the whole font.
MIN_SAMPLE_GLYPHS = 4

# Stem snap values whose group count is below this fraction of the most frequent group are
# discarded as outliers.
MIN_SNAP_COUNT_RATIO = 0.05

# Stem snap values wider than this multiple of the StdHW/StdVW of the same direction are
# discarded: they come from pairings of distant edges, not from real stems.
MAX_SNAP_WIDTH_RATIO: float | None = 3.0

# Default glyph samples, as characters resolved through the cmap. They favor glyphs with clean,
# mostly straight stems: curved segments are ignored by default, so round shapes such as o, c, s
# and g add little to the report. Horizontal and vertical stems come from different shapes, so
# each direction has its own samples. Lowercase letters alone have too few horizontal stems, so
# the horizontal samples include uppercase letters.
STD_H_CHARS = "eftzEFHLTZ"
STD_V_CHARS = "bdhiklmnpqru"
SNAP_H_CHARS = STD_H_CHARS + "BDPR"
SNAP_V_CHARS = STD_V_CHARS + "EFHILT"

# Samples used for StdHW, StdVW, StemSnapH and StemSnapV.
STD_H_CODEPOINTS = frozenset(map(ord, STD_H_CHARS))
STD_V_CODEPOINTS = frozenset(map(ord, STD_V_CHARS))
SNAP_H_CODEPOINTS = frozenset(map(ord, SNAP_H_CHARS))
SNAP_V_CODEPOINTS = frozenset(map(ord, SNAP_V_CHARS))


def _get_report(
    file_path: Path, glyph_list: list[str] | None, report_all_stems: bool = False
) -> tuple[Report, ReportOptions]:
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

    return report, options


def _get_stem_lists(
    report: Report, options: ReportOptions, glyph_names: Collection[str] | None = None
) -> tuple[list[tuple[int, int, list[str]]], list[tuple[int, int, list[str]]]]:
    """
    Builds the horizontal and vertical stem lists, optionally restricted to some glyphs.

    The counts of a report are aggregated across glyphs, so they must be rebuilt from the
    per-glyph data to restrict them to a sample.
    """
    sub_report = Report()
    sub_report.glyphs = {
        name: glyph
        for name, glyph in report.glyphs.items()
        if glyph_names is None or name in glyph_names
    }
    h_stems, v_stems, _, _ = sub_report._get_lists(options)
    h_stems.sort(key=sub_report._sort_count)
    v_stems.sort(key=sub_report._sort_count)
    return h_stems, v_stems


def _resolve_glyph_names(file_path: Path, codepoints: Collection[int]) -> set[str]:
    with TTFont(file_path, lazy=True) as ttfont:
        cmap = ttfont.getBestCmap()
    return {cmap[cp] for cp in codepoints if cp in cmap}


def _group_widths_with_neighbors(
    report: list[tuple[int, int, list[str]]], max_distance: int = 2
) -> list[list[tuple[int, int]]]:
    """
    Groups report entries based on their width and proximity to neighboring widths.

    This function takes a report containing tuples of a unique identifier, a width,
    and a list of associated strings. It groups entries together based on their widths
    and their proximity to neighboring widths within a specified maximum distance.
    Neighboring widths in the range `[width - max_distance, width + max_distance]`
    are identified, and groups are sorted by an identifier in descending order.

    Parameters:
        report: list of tuples, where each tuple contains:
            - A unique identifier (int)
            - A width value (int)
            - Associated strings (list of str)
        max_distance: (int, optional) Maximum proximity range to consider neighbors.
            Defaults to 2.

    Returns:
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
        group = []
        # Find all widths within the range [width - max_distance, width + max_distance]
        for neighbor_width in range(width - max_distance, width + max_distance + 1):
            if neighbor_width in width_map:
                group.append(width_map[neighbor_width])
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
    min_count_ratio: float = 0.0,
    max_width: float | None = None,
) -> list[int]:
    """
    Extracts a specified number of representative stem values from groups of stems, ensuring that
    selected values maintain a minimum difference of five units to provide optimal results as per
    technical recommendations.

    From: https://adobe-type-tools.github.io/font-tech-notes/pdfs/5049.StemSnap.pdf

    "It is important that only the mean value of groups of stems be entered in the array. Entering
    values that are too close together, such as [ 121, 122, ... 172, 174...] might produce
    undesirable results. Hence, it is recommended that values be a minimum of five units apart."

    :param groups: A list of grouped stems, where each group contains a list of tuples comprising
        stem value and count.
    :type groups: list
    :param number_of_stems: The number of stem values to extract from the groups.
    :type number_of_stems: int
    :param min_count_ratio: Groups whose count sum is below this fraction of the highest one are
        ignored.
    :type min_count_ratio: float
    :param max_width: Groups whose representative value is wider than this are ignored.
    :type max_width: float | None
    :return: A list of representative stem values.
    :rtype: list[int]
    """

    stem_snap: list[int] = []
    sorted_groups = _sort_groups_by_count_sum(groups)
    min_count = sum(e[0] for e in sorted_groups[0]) * min_count_ratio
    for group in sorted_groups:
        if sum(e[0] for e in group) < min_count:
            break
        max_value = max(group, key=lambda x: x[0])[1]
        if max_width is not None and max_value > max_width:
            continue
        if any(abs(max_value - used) < 5 for used in stem_snap):
            continue
        stem_snap.append(max_value)
    return sorted(stem_snap[:number_of_stems])


def run(
    file_path: Path,
    report_all_stems: bool = False,
    max_distance: int = 1,
    max_h_stems: int = 2,
    max_v_stems: int = 2,
    use_samples: bool = True,
    std_h_codepoints: Collection[int] | None = None,
    std_v_codepoints: Collection[int] | None = None,
    snap_h_codepoints: Collection[int] | None = None,
    snap_v_codepoints: Collection[int] | None = None,
) -> tuple[int, int, list[int] | None, list[int] | None]:
    """
    Recalculates the StdHW, StdVW, StemSnapH, and StemSnapV values for a font file.

    By default, each value is calculated from a sample of glyphs with clean stems. A sample that
    resolves to fewer than ``MIN_SAMPLE_GLYPHS`` glyphs, or that contains no stems, falls back to
    the whole font. To use a single sample, pass the same codepoints for the Std and Snap values.

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
    :param use_samples: If False, all values are calculated from the whole font.
    :type use_samples: bool
    :param std_h_codepoints: Codepoints of the glyphs used for StdHW. Defaults to
        ``STD_H_CODEPOINTS``.
    :type std_h_codepoints: Collection[int] | None
    :param std_v_codepoints: Codepoints of the glyphs used for StdVW. Defaults to
        ``STD_V_CODEPOINTS``.
    :type std_v_codepoints: Collection[int] | None
    :param snap_h_codepoints: Codepoints of the glyphs used for StemSnapH. Defaults to
        ``SNAP_H_CODEPOINTS``.
    :type snap_h_codepoints: Collection[int] | None
    :param snap_v_codepoints: Codepoints of the glyphs used for StemSnapV. Defaults to
        ``SNAP_V_CODEPOINTS``.
    :type snap_v_codepoints: Collection[int] | None
    :return: A tuple containing the new StdHW, StdVW, StemSnapH, and StemSnapV values.
    :rtype: tuple[int, int, list[int] | None, list[int] | None]
    :raises ValueError: If a parameter is out of range, or if no stems are found in one of the
        two directions.
    """
    if max_distance < 0:
        raise ValueError(f"max_distance must be >= 0, got {max_distance}")
    if max_h_stems < 1:
        raise ValueError(f"max_h_stems must be >= 1, got {max_h_stems}")
    if max_v_stems < 1:
        raise ValueError(f"max_v_stems must be >= 1, got {max_v_stems}")

    samples: dict[str, set[str] | None] = {
        "std_h": None,
        "std_v": None,
        "snap_h": None,
        "snap_v": None,
    }
    if use_samples:
        codepoints = {
            "std_h": STD_H_CODEPOINTS if std_h_codepoints is None else std_h_codepoints,
            "std_v": STD_V_CODEPOINTS if std_v_codepoints is None else std_v_codepoints,
            "snap_h": SNAP_H_CODEPOINTS if snap_h_codepoints is None else snap_h_codepoints,
            "snap_v": SNAP_V_CODEPOINTS if snap_v_codepoints is None else snap_v_codepoints,
        }
        for key, cps in codepoints.items():
            names = _resolve_glyph_names(file_path, cps)
            if len(names) < MIN_SAMPLE_GLYPHS:
                logger.warning(
                    "Sample '%s' resolves to %d glyphs (minimum %d): using the whole font",
                    key,
                    len(names),
                    MIN_SAMPLE_GLYPHS,
                )
                continue
            samples[key] = names

    # Hinting only the glyphs that are needed; a sample without stems triggers a full report.
    names_to_hint = None if None in samples.values() else set().union(*samples.values())  # type: ignore[arg-type]
    report, options = _get_report(
        file_path, sorted(names_to_hint) if names_to_hint else None, report_all_stems
    )
    full_report = report if names_to_hint is None else None

    def get_report(key: str, direction: int) -> list[tuple[int, int, list[str]]]:
        nonlocal full_report
        names = samples[key]
        stems = _get_stem_lists(report, options, names)[direction]
        if stems:
            return stems
        if names is not None:
            logger.warning("Sample '%s' contains no stems: using the whole font", key)
            if full_report is None:
                full_report, _ = _get_report(file_path, None, report_all_stems)
            stems = _get_stem_lists(full_report, options)[direction]
        if not stems:
            direction_name = "horizontal" if direction == 0 else "vertical"
            raise ValueError(f"No {direction_name} stems found in font: {file_path}")
        return stems

    def get_groups(key: str, direction: int) -> list[list[tuple[int, int]]]:
        return _group_widths_with_neighbors(get_report(key, direction), max_distance=max_distance)

    std_h_w = _get_first_n_stems(get_groups("std_h", 0), 1)[0]
    std_v_w = _get_first_n_stems(get_groups("std_v", 1), 1)[0]
    max_h_width = None if MAX_SNAP_WIDTH_RATIO is None else std_h_w * MAX_SNAP_WIDTH_RATIO
    max_v_width = None if MAX_SNAP_WIDTH_RATIO is None else std_v_w * MAX_SNAP_WIDTH_RATIO
    stem_snap_h = (
        _get_first_n_stems(get_groups("snap_h", 0), max_h_stems, MIN_SNAP_COUNT_RATIO, max_h_width)
        if max_h_stems > 1
        else None
    )
    stem_snap_v = (
        _get_first_n_stems(get_groups("snap_v", 1), max_v_stems, MIN_SNAP_COUNT_RATIO, max_v_width)
        if max_v_stems > 1
        else None
    )

    return std_h_w, std_v_w, stem_snap_h, stem_snap_v
