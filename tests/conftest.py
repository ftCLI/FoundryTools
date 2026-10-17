from pathlib import Path

import pytest
from fontTools.fontBuilder import FontBuilder
from fontTools.pens.t2CharStringPen import T2CharStringPen

STEM = 80
BAR = 50

# Clean "E" (a vertical stem and three horizontal bars) followed by two plain vertical stems, so
# that STEM is the most frequent vertical width and BAR the most frequent horizontal one.
CONTOURS = [
    [
        (100, 0),
        (400, 0),
        (400, BAR),
        (100 + STEM, BAR),
        (100 + STEM, 325),
        (380, 325),
        (380, 325 + BAR),
        (100 + STEM, 325 + BAR),
        (100 + STEM, 700 - BAR),
        (400, 700 - BAR),
        (400, 700),
        (100, 700),
    ],
    [(450, 0), (450 + STEM, 0), (450 + STEM, 700), (450, 700)],
    [(560, 0), (560 + STEM, 0), (560 + STEM, 700), (560, 700)],
]


def build_font(path: Path, chars: str) -> Path:
    glyph_order = [".notdef", *chars]
    pen = T2CharStringPen(800, None)
    for contour in CONTOURS:
        pen.moveTo(contour[0])
        for point in contour[1:]:
            pen.lineTo(point)
        pen.closePath()
    charstring = pen.getCharString()
    notdef = T2CharStringPen(800, None).getCharString()

    fb = FontBuilder(1000, isTTF=False)
    fb.setupGlyphOrder(glyph_order)
    fb.setupCharacterMap({ord(c): c for c in chars})
    fb.setupCFF(
        "SyntheticStems-Regular",
        {"FullName": "Synthetic Stems Regular"},
        {name: notdef if name == ".notdef" else charstring for name in glyph_order},
        {},
    )
    fb.setupHorizontalMetrics(dict.fromkeys(glyph_order, (800, 100)))
    fb.setupHorizontalHeader(ascent=800, descent=-200)
    fb.setupNameTable({"familyName": "Synthetic Stems", "styleName": "Regular"})
    fb.setupOS2()
    fb.setupPost()
    fb.save(path)
    return path


@pytest.fixture(scope="session")
def full_font(tmp_path_factory: pytest.TempPathFactory) -> Path:
    from foundrytools.app import otf_recalc_stems

    chars = otf_recalc_stems.SNAP_H_CHARS + otf_recalc_stems.SNAP_V_CHARS
    return build_font(tmp_path_factory.mktemp("fonts") / "full.otf", "".join(sorted(set(chars))))


@pytest.fixture(scope="session")
def small_font(tmp_path_factory: pytest.TempPathFactory) -> Path:
    return build_font(tmp_path_factory.mktemp("fonts") / "small.otf", "HIL")
