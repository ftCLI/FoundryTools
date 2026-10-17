import logging
from pathlib import Path
from typing import Any

import pytest

from foundrytools.app import otf_recalc_stems as m

from .conftest import BAR, STEM


def test_group_widths_with_neighbors_groups_close_widths() -> None:
    report = [(10, 80, ["a"]), (4, 81, ["b"]), (3, 120, ["c"])]
    groups = m._group_widths_with_neighbors(report, max_distance=1)
    assert groups[0] == [(10, 80), (4, 81)]
    assert groups[2] == [(3, 120)]


def test_get_first_n_stems_keeps_values_five_units_apart() -> None:
    groups = [[(10, 80)], [(8, 83)], [(5, 120)]]
    assert m._get_first_n_stems(groups, 3) == [80, 120]


def test_get_first_n_stems_discards_rare_groups() -> None:
    groups = [[(100, 80)], [(2, 214)]]
    assert m._get_first_n_stems(groups, 2, min_count_ratio=0.05) == [80]
    assert m._get_first_n_stems(groups, 2) == [80, 214]


def test_get_first_n_stems_discards_values_wider_than_max_width() -> None:
    groups = [[(100, 48)], [(40, 245)], [(30, 60)]]
    assert m._get_first_n_stems(groups, 2, max_width=144) == [48, 60]
    assert m._get_first_n_stems(groups, 2) == [48, 245]


def test_default_samples_are_resolved_through_the_cmap(full_font: Path) -> None:
    names = m._resolve_glyph_names(full_font, m.STD_H_CODEPOINTS)
    assert names == set(m.STD_H_CHARS)


def test_run_returns_expected_values_with_samples(full_font: Path) -> None:
    std_h, std_v, snap_h, snap_v = m.run(full_font)
    assert (std_h, std_v) == (BAR, STEM)
    assert snap_h is not None and BAR in snap_h
    assert snap_v is not None and STEM in snap_v


def test_run_without_samples_matches_samples_on_clean_font(full_font: Path) -> None:
    assert m.run(full_font, use_samples=False) == m.run(full_font)


def test_run_without_snap_returns_none(full_font: Path) -> None:
    _, _, snap_h, snap_v = m.run(full_font, max_h_stems=1, max_v_stems=1)
    assert snap_h is None
    assert snap_v is None


def test_run_falls_back_to_whole_font_for_small_samples(
    small_font: Path, caplog: pytest.LogCaptureFixture
) -> None:
    with caplog.at_level(logging.WARNING, logger=m.logger.name):
        result = m.run(small_font)
    assert result[:2] == (BAR, STEM)
    assert "using the whole font" in caplog.text


def test_run_accepts_custom_codepoints(full_font: Path) -> None:
    codepoints = {ord(c) for c in "HELT"}
    result = m.run(
        full_font,
        std_h_codepoints=codepoints,
        std_v_codepoints=codepoints,
        snap_h_codepoints=codepoints,
        snap_v_codepoints=codepoints,
    )
    assert result[:2] == (BAR, STEM)


@pytest.mark.parametrize(
    "kwargs",
    [{"max_distance": -1}, {"max_h_stems": 0}, {"max_v_stems": -2}],
)
def test_run_rejects_invalid_parameters(full_font: Path, kwargs: dict[str, Any]) -> None:
    with pytest.raises(ValueError):
        m.run(full_font, **kwargs)
