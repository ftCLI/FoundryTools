from collections import Counter
from typing import Literal, Optional

from foundrytools import Font

UPPERCASE_LETTERS = [chr(i) for i in range(65, 91)]  # A-Z
UPPERCASE_DESCENDERS = ["J", "Q"]
LOWERCASE_LETTERS = [chr(i) for i in range(97, 123)]  # a-z
LOWERCASE_DESCENDERS = ["f", "g", "j", "p", "q", "y"]
LOWERCASE_ASCENDERS = ["b", "d", "f", "h", "k", "l", "t"]

DESCENDER_GLYPHS = list(set(LOWERCASE_DESCENDERS) - {"f", "j"})
BASELINE_GLYPHS = list(
    set(UPPERCASE_LETTERS + LOWERCASE_LETTERS)
    - set(LOWERCASE_DESCENDERS)
    - set(UPPERCASE_DESCENDERS)
)
X_HEIGHT_GLYPHS = list(set(LOWERCASE_LETTERS) - set(LOWERCASE_ASCENDERS + ["i", "j"]))
UPPERCASE_GLYPHS = UPPERCASE_LETTERS
ASCENDER_GLYPHS = list(set(LOWERCASE_ASCENDERS) - {"t"})


def _get_pair(counter: Counter) -> list[float]:
    """
    Get the two most common elements from the given counter.

    :param counter: The counter object containing elements and their counts.
    :type counter: Counter
    :return: List containing the pair of most common elements.
    :rtype: list[float]
    """

    most_common = counter.most_common(2)
    if len(counter) == 1:
        return [most_common[0][0], most_common[0][0]]
    return sorted([most_common[0][0], most_common[1][0]])


def _lists_overlaps(lists: list[list[float]]) -> bool:
    """
    Check if there are overlapping intervals in a list of lists.

    :param lists: A list of lists, where each inner list represents an interval.
    :type lists: list[list[float]]
    :return: True if there are overlapping intervals, False otherwise.
    :rtype: bool
    """

    return any(lists[i][1] > lists[i + 1][0] for i in range(len(lists) - 1))


def _fix_lists_overlaps(lists: list[list[float]]) -> list[list[float]]:
    """
    Fixes overlaps in a list of lists of floats.

    :param lists: A list of lists of floats.
    :type lists: list[list[float]]
    :return: The input list with the overlaps fixed.
    :rtype: list[list[float]]
    """
    for i in range(len(lists) - 1):
        if lists[i][1] > lists[i + 1][0]:
            lists[i + 1][0] = lists[i][1]
            lists[i + 1] = sorted(lists[i + 1])
    return lists


def _fix_min_separation_limits(lists: list[list[float]], limit: int) -> list[list[float]]:
    """
    Fixes the minimum separation between zones.

    :param lists: A list of lists of floats.
    :type lists: list[list[float]]
    :param limit: The minimum separation between zones.
    :type limit: int
    :return: The input list with the minimum separation fixed.
    :rtype: list[list[float]]
    """

    for i in range(len(lists) - 1):
        if lists[i + 1][0] - lists[i][1] < limit:
            # If the difference between the two values is less than 3, then
            # set the second value to the first value
            if lists[i + 1][1] - lists[i][1] > limit:
                lists[i + 1][0] = lists[i + 1][1]
            else:
                # Remove the second list
                lists.pop(i + 1)
    return lists


def _calculate_zone(
    font: Font, glyph_names: list[str], min_or_max: Literal["y_min", "y_max"]
) -> list[float]:
    """
    Calculates the minimum and maximum vertical values for a given zone.

    :param font: The Font object.
    :type font: Font
    :param glyph_names: A list of glyph names to use for calculating the zone.
    :type glyph_names: list[str]
    :param min_or_max: Whether to calculate the minimum or maximum value.
    :type min_or_max: Literal["y_min", "y_max"]
    :return: A list containing the minimum and maximum values for the zone.
    :rtype: list[float]
    """

    data = font.get_glyph_bounds_many(glyph_names=set(glyph_names))
    counter = Counter([v[min_or_max] for v in data.values()])
    return _get_pair(counter)


def run(
    font: Font,
    descender_glyphs: Optional[list[str]] = None,
    baseline_glyphs: Optional[list[str]] = None,
    x_height_glyphs: Optional[list[str]] = None,
    uppercase_glyphs: Optional[list[str]] = None,
    ascender_glyphs: Optional[list[str]] = None,
) -> tuple[list[int], list[int]]:
    """
    Recalculates the zones for a given TTFont object.

    :param font: The Font object.
    :type font: Font
    :param descender_glyphs: A list of glyph names to use for calculating the descender zone.
    :type descender_glyphs: Optional[list[str]]
    :param baseline_glyphs: A list of glyph names to use for calculating the baseline zone.
    :type baseline_glyphs: Optional[list[str]]
    :param x_height_glyphs: A list of glyph names to use for calculating the x-height zone.
    :type x_height_glyphs: Optional[list[str]]
    :param uppercase_glyphs: A list of glyph names to use for calculating the uppercase zone.
    :type uppercase_glyphs: Optional[list[str]]
    :param ascender_glyphs: A list of glyph names to use for calculating the ascender zone.
    :type ascender_glyphs: Optional[list[str]]
    :return: A tuple containing the recalculated OtherBlues and BlueValues values.
    :rtype: tuple[list[int], list[int]]
    """

    if descender_glyphs is None:
        descender_glyphs = DESCENDER_GLYPHS
    if baseline_glyphs is None:
        baseline_glyphs = BASELINE_GLYPHS
    if x_height_glyphs is None:
        x_height_glyphs = X_HEIGHT_GLYPHS
    if uppercase_glyphs is None:
        uppercase_glyphs = UPPERCASE_GLYPHS
    if ascender_glyphs is None:
        ascender_glyphs = ASCENDER_GLYPHS

    descender_zone = _calculate_zone(font=font, glyph_names=descender_glyphs, min_or_max="y_min")
    baseline_zone = _calculate_zone(font=font, glyph_names=baseline_glyphs, min_or_max="y_min")
    x_height_zone = _calculate_zone(font=font, glyph_names=x_height_glyphs, min_or_max="y_max")
    uppercase_zone = _calculate_zone(font=font, glyph_names=uppercase_glyphs, min_or_max="y_max")
    ascender_zone = _calculate_zone(font=font, glyph_names=ascender_glyphs, min_or_max="y_max")

    zones = sorted([descender_zone, baseline_zone, x_height_zone, uppercase_zone, ascender_zone])
    if _lists_overlaps(zones):
        zones = _fix_lists_overlaps(zones)

    min_separation = font.t_cff_.table.cff.topDictIndex[0].Private.BlueFuzz * 2 + 1
    zones = _fix_min_separation_limits(zones, limit=min_separation)

    other_blues = [int(v) for v in zones[0]]

    blue_values = []
    for zone in zones[1:]:
        blue_values.extend([int(v) for v in zone])

    return other_blues, blue_values
