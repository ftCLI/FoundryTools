"""Unicode functionality."""

from __future__ import annotations

import json

from fontTools.ttLib import TTFont, newTable
from fontTools.ttLib.tables._c_m_a_p import CmapSubtable

from foundrytools.constants import NAMES_TO_UNICODES_FILE, T_CMAP, UNICODES_TO_NAMES_FILE

_CharacterMap = dict[int, str]
_ReversedCmap = dict[str, set[int]]

NAMES_TO_UNICODES = json.loads(NAMES_TO_UNICODES_FILE.read_text(encoding="utf-8"))
UNICODES_TO_NAMES = json.loads(UNICODES_TO_NAMES_FILE.read_text(encoding="utf-8"))


class UnicodeBlock:  # pylint: disable=too-many-instance-attributes, too-few-public-methods
    """
    A class representing a Unicode block.

    :param bit_number: The bit number of the block.
    :type bit_number: int
    :param first_codepoint: The first codepoint of the block.
    :type first_codepoint: int
    :param last_codepoint: The last codepoint of the block.
    :type last_codepoint: int
    :param name: The name of the block.
    :type name: str
    :param min_os2_version: The minimum OS/2 version required for the block.
    :type min_os2_version: int
    :param sub_blocks: A list of sub-blocks.
    :type sub_blocks: Optional[list["UnicodeBlock"]]
    """

    def __init__(
        self,
        bit_number: int,
        first_codepoint: int,
        last_codepoint: int,
        name: str,
        min_os2_version: int,
        sub_blocks: list[UnicodeBlock] | None = None,
    ) -> None:
        """Initialize the Unicode block."""
        self.bit_number = bit_number
        self.first_codepoint = first_codepoint
        self.last_codepoint = last_codepoint
        self.block_name = name
        self.min_os2_version = min_os2_version
        self.sub_blocks = sub_blocks

        self.found_codepoints = 0
        self.is_supported = False
        self.is_enabled = False

    @property
    def size(self) -> int:
        """Returns the size of the block."""
        return self.last_codepoint - self.first_codepoint + 1


def count_block_codepoints(block: UnicodeBlock, unicodes: set[int]) -> int:
    """
    Count the number of codepoints in a given UnicodeBlock present in the provided set of unicode.

    This function iterates over the range of codepoints defined by the input UnicodeBlock and counts
    how many of them are included in the provided set of unicodes.

    :param block: The UnicodeBlock object that defines the range of codepoints.
    :type block: UnicodeBlock
    :param unicodes: A set of integers representing Unicode codepoints.
    :type unicodes: set[int]
    :return: The number of codepoints in the UnicodeBlock that are present in the set of unicodes.
    :rtype: int
    """
    cp_count = 0
    for unicode_value in range(block.first_codepoint, block.last_codepoint + 1):
        if unicode_value in unicodes:
            cp_count += 1
    return cp_count


def check_block_support(
    block: UnicodeBlock,
    found_codepoints: int,
    min_codepoints: int,
    os2_version: int,
    *,
    has_cmap_32: bool,
) -> bool:
    """
    Validate unicode block.

    Check if a Unicode block is supported based on the following criteria:

    * The number of codepoints found in the block is greater than or equal to the minimum required.
    * The minimum OS/2 version required for the block is satisfied.
    * The block is not block 57 and the font has a cmap format 32 subtable.

    :param block: The Unicode block to check.
    :type block: UnicodeBlock
    :param found_codepoints: The number of codepoints found in the block.
    :type found_codepoints: int
    :param min_codepoints: The minimum number of codepoints required for the block.
    :type min_codepoints: int
    :param os2_version: The current OS/2 version.
    :type os2_version: int
    :param has_cmap_32: Whether the font has a cmap format 32 subtable.
    :type has_cmap_32: bool
    :return: Whether the block is supported.
    :rtype: bool
    """
    is_supported = found_codepoints >= min_codepoints
    if block.min_os2_version > os2_version:
        is_supported = False
    if not has_cmap_32 and block.bit_number == 57:  # noqa: PLR2004
        is_supported = False
    return is_supported


OS_2_UNICODE_RANGES = [
    UnicodeBlock(0, 0x0020, 0x007E, "Basic Latin", 0),
    UnicodeBlock(1, 0x0080, 0x00FF, "Latin-1 Supplement", 0),
    UnicodeBlock(2, 0x0100, 0x017F, "Latin Extended-A", 0),
    UnicodeBlock(3, 0x0180, 0x024F, "Latin Extended-B", 0),
    UnicodeBlock(
        4,
        0x0250,
        0x02AF,
        "IPA Extensions",
        0,
        [
            UnicodeBlock(4, 0x1D00, 0x1D7F, "Phonetic Extensions", 4),
            UnicodeBlock(4, 0x1D80, 0x1DBF, "Phonetic Extensions Supplement", 4),
        ],
    ),
    UnicodeBlock(
        5,
        0x02B0,
        0x02FF,
        "Spacing Modifier Letters",
        0,
        [UnicodeBlock(5, 0xA700, 0xA71F, "Modifier Tone Letters", 4)],
    ),
    UnicodeBlock(
        6,
        0x0300,
        0x036F,
        "Combining Diacritical Marks",
        0,
        [UnicodeBlock(6, 0x1DC0, 0x1DFF, "Combining Diacritical Marks Supplement", 4)],
    ),
    UnicodeBlock(7, 0x0370, 0x03FF, "Greek and Coptic", 0),
    UnicodeBlock(8, 0x2C80, 0x2CFF, "Coptic", 4),
    UnicodeBlock(
        9,
        0x0400,
        0x04FF,
        "Cyrillic",
        0,
        [
            UnicodeBlock(9, 0x0500, 0x052F, "Cyrillic Supplement", 3),
            UnicodeBlock(9, 0x2DE0, 0x2DFF, "Cyrillic Extended-A", 4),
            UnicodeBlock(9, 0xA640, 0xA69F, "Cyrillic Extended-B", 4),
        ],
    ),
    UnicodeBlock(10, 0x0530, 0x058F, "Armenian", 0),
    UnicodeBlock(11, 0x0590, 0x05FF, "Hebrew", 0),
    UnicodeBlock(12, 0xA500, 0xA63F, "Vai", 4),
    UnicodeBlock(13, 0x0600, 0x06FF, "Arabic", 0, [UnicodeBlock(13, 0x0750, 0x077F, "Arabic Supplement", 4)]),
    UnicodeBlock(14, 0x07C0, 0x07FF, "NKo", 4),
    UnicodeBlock(15, 0x0900, 0x097F, "Devanagari", 0),
    UnicodeBlock(16, 0x0980, 0x09FF, "Bangla", 0),
    UnicodeBlock(17, 0x0A00, 0x0A7F, "Gurmukhi", 0),
    UnicodeBlock(18, 0x0A80, 0x0AFF, "Gujarati", 0),
    UnicodeBlock(19, 0x0B00, 0x0B7F, "Odia", 0),
    UnicodeBlock(20, 0x0B80, 0x0BFF, "Tamil", 0),
    UnicodeBlock(21, 0x0C00, 0x0C7F, "Telugu", 0),
    UnicodeBlock(22, 0x0C80, 0x0CFF, "Kannada", 0),
    UnicodeBlock(23, 0x0D00, 0x0D7F, "Malayalam", 0),
    UnicodeBlock(24, 0x0E00, 0x0E7F, "Thai", 0),
    UnicodeBlock(25, 0x0E80, 0x0EFF, "Lao", 0),
    UnicodeBlock(
        26,
        0x10A0,
        0x10FF,
        "Georgian",
        0,
        [UnicodeBlock(26, 0x2D00, 0x2D2F, "Georgian Supplement", 4)],
    ),
    UnicodeBlock(27, 0x1B00, 0x1B7F, "Balinese", 4),
    UnicodeBlock(28, 0x1100, 0x11FF, "Hangul Jamo", 0),
    UnicodeBlock(
        29,
        0x1E00,
        0x1EFF,
        "Latin Extended Additional",
        0,
        [
            UnicodeBlock(29, 0x2C60, 0x2C7F, "Latin Extended-C", 4),
            UnicodeBlock(29, 0xA720, 0xA7FF, "Latin Extended-D", 4),
        ],
    ),
    UnicodeBlock(30, 0x1F00, 0x1FFF, "Greek Extended", 0),
    UnicodeBlock(
        31,
        0x2000,
        0x206F,
        "General Punctuation",
        0,
        [UnicodeBlock(31, 0x2E00, 0x2E7F, "Supplemental Punctuation", 4)],
    ),
    UnicodeBlock(32, 0x2070, 0x209F, "Superscripts And Subscripts", 0),
    UnicodeBlock(33, 0x20A0, 0x20CF, "Currency Symbols", 0),
    UnicodeBlock(34, 0x20D0, 0x20FF, "Combining Diacritical Marks For Symbols", 0),
    UnicodeBlock(35, 0x2100, 0x214F, "Letterlike Symbols", 0),
    UnicodeBlock(36, 0x2150, 0x218F, "Number Forms", 0),
    UnicodeBlock(
        37,
        0x2190,
        0x21FF,
        "Arrows",
        0,
        [
            UnicodeBlock(37, 0x27F0, 0x27FF, "Supplemental Arrows-A", 3),
            UnicodeBlock(37, 0x2900, 0x297F, "Supplemental Arrows-B", 3),
            UnicodeBlock(37, 0x2B00, 0x2BFF, "Miscellaneous Symbols and Arrows", 4),
        ],
    ),
    UnicodeBlock(
        38,
        0x2200,
        0x22FF,
        "Mathematical Operators",
        0,
        [
            UnicodeBlock(38, 0x2A00, 0x2AFF, "Supplemental Mathematical Operators", 3),
            UnicodeBlock(38, 0x27C0, 0x27EF, "Miscellaneous Mathematical Symbols-A", 3),
            UnicodeBlock(38, 0x2980, 0x29FF, "Miscellaneous Mathematical Symbols-B", 3),
        ],
    ),
    UnicodeBlock(39, 0x2300, 0x23FF, "Miscellaneous Technical", 0),
    UnicodeBlock(40, 0x2400, 0x243F, "Control Pictures", 0),
    UnicodeBlock(41, 0x2440, 0x245F, "Optical Character Recognition", 0),
    UnicodeBlock(42, 0x2460, 0x24FF, "Enclosed Alphanumerics", 0),
    UnicodeBlock(43, 0x2500, 0x257F, "Box Drawing", 0),
    UnicodeBlock(44, 0x2580, 0x259F, "Block Elements", 0),
    UnicodeBlock(45, 0x25A0, 0x25FF, "Geometric Shapes", 0),
    UnicodeBlock(46, 0x2600, 0x26FF, "Miscellaneous Symbols", 0),
    UnicodeBlock(47, 0x2700, 0x27BF, "Dingbats", 0),
    UnicodeBlock(48, 0x3000, 0x303F, "CJK Symbols And Punctuation", 0),
    UnicodeBlock(49, 0x3040, 0x309F, "Hiragana", 0),
    UnicodeBlock(
        50,
        0x30A0,
        0x30FF,
        "Katakana",
        0,
        [UnicodeBlock(50, 0x31F0, 0x31FF, "Katakana Phonetic Extensions", 3)],
    ),
    UnicodeBlock(
        51,
        0x3100,
        0x312F,
        "Bopomofo",
        0,
        [UnicodeBlock(51, 0x31A0, 0x31BF, "Bopomofo Extended", 2)],
    ),
    UnicodeBlock(52, 0x3130, 0x318F, "Hangul Compatibility Jamo", 0),
    UnicodeBlock(53, 0xA840, 0xA87F, "Phags-pa", 4),
    UnicodeBlock(54, 0x3200, 0x32FF, "Enclosed CJK Letters And Months", 0),
    UnicodeBlock(55, 0x3300, 0x33FF, "CJK Compatibility", 0),
    UnicodeBlock(56, 0xAC00, 0xD7AF, "Hangul Syllables", 0),
    UnicodeBlock(57, 0x10000, 0x10FFFF, "Non-Plane 0", 2),
    UnicodeBlock(58, 0x10900, 0x1091F, "Phoenician", 4),
    UnicodeBlock(
        59,
        0x4E00,
        0x9FFF,
        "CJK Unified Ideographs",
        0,
        [
            UnicodeBlock(59, 0x2E80, 0x2EFF, "CJK Radicals Supplement", 2),
            UnicodeBlock(59, 0x2F00, 0x2FDF, "Kangxi Radicals", 2),
            UnicodeBlock(59, 0x2FF0, 0x2FFF, "Ideographic Description Characters", 2),
            UnicodeBlock(59, 0x3400, 0x4DBF, "CJK Unified Ideographs Extension A", 2),
            UnicodeBlock(59, 0x20000, 0x2A6DF, "CJK Unified Ideographs Extension B", 3),
            UnicodeBlock(59, 0x3190, 0x319F, "Kanbun", 3),
        ],
    ),
    UnicodeBlock(60, 0xE000, 0xF8FF, "Private Use Area (plane 0)", 0),
    UnicodeBlock(
        61,
        0x31C0,
        0x31EF,
        "CJK Strokes",
        4,
        [
            UnicodeBlock(61, 0xF900, 0xFAFF, "CJK Compatibility Ideographs", 0),
            UnicodeBlock(61, 0x2F800, 0x2FA1F, "CJK Compatibility Ideographs Supplement", 3),
        ],
    ),
    UnicodeBlock(62, 0xFB00, 0xFB4F, "Alphabetic Presentation Forms", 0),
    UnicodeBlock(63, 0xFB50, 0xFDFF, "Arabic Presentation Forms-A", 0),
    UnicodeBlock(64, 0xFE20, 0xFE2F, "Combining Half Marks", 0),
    UnicodeBlock(
        65,
        0xFE10,
        0xFE1F,
        "Vertical Forms",
        4,
        [UnicodeBlock(65, 0xFE30, 0xFE4F, "CJK Compatibility Forms", 0)],
    ),
    UnicodeBlock(66, 0xFE50, 0xFE6F, "Small Form Variants", 0),
    UnicodeBlock(67, 0xFE70, 0xFEFF, "Arabic Presentation Forms-B", 0),
    UnicodeBlock(68, 0xFF00, 0xFFEF, "Halfwidth And Fullwidth Forms", 0),
    UnicodeBlock(69, 0xFFF0, 0xFFFF, "Specials", 0),
    UnicodeBlock(70, 0x0F00, 0x0FFF, "Tibetan", 2),
    UnicodeBlock(71, 0x0700, 0x074F, "Syriac", 2),
    UnicodeBlock(72, 0x0780, 0x07BF, "Thaana", 2),
    UnicodeBlock(73, 0x0D80, 0x0DFF, "Sinhala", 2),
    UnicodeBlock(74, 0x1000, 0x109F, "Myanmar", 2),
    UnicodeBlock(
        75,
        0x1200,
        0x137F,
        "Ethiopic",
        2,
        [
            UnicodeBlock(75, 0x1380, 0x139F, "Ethiopic Supplement", 4),
            UnicodeBlock(75, 0x2D80, 0x2DDF, "Ethiopic Extended", 4),
        ],
    ),
    UnicodeBlock(76, 0x13A0, 0x13FF, "Cherokee", 2),
    UnicodeBlock(77, 0x1400, 0x167F, "Unified Canadian Aboriginal Syllabics", 2),
    UnicodeBlock(78, 0x1680, 0x169F, "Ogham", 2),
    UnicodeBlock(79, 0x16A0, 0x16FF, "Runic", 2),
    UnicodeBlock(80, 0x1780, 0x17FF, "Khmer", 2, [UnicodeBlock(80, 0x19E0, 0x19FF, "Khmer Symbols", 4)]),
    UnicodeBlock(81, 0x1800, 0x18AF, "Mongolian", 2),
    UnicodeBlock(82, 0x2800, 0x28FF, "Braille Patterns", 2),
    UnicodeBlock(83, 0xA000, 0xA48F, "Yi Syllables", 2, [UnicodeBlock(83, 0xA490, 0xA4CF, "Yi Radicals", 2)]),
    UnicodeBlock(
        84,
        0x1700,
        0x171F,
        "Tagalog",
        3,
        [
            UnicodeBlock(84, 0x1730, 0x173F, "Hanunoo", 3),
            UnicodeBlock(84, 0x1740, 0x175F, "Buhid", 3),
            UnicodeBlock(84, 0x1760, 0x177F, "Tagbanwa", 3),
        ],
    ),
    UnicodeBlock(85, 0x10300, 0x1032F, "Old Italic", 3),
    UnicodeBlock(86, 0x10330, 0x1034F, "Gothic", 3),
    UnicodeBlock(87, 0x10400, 0x1044F, "Deseret", 3),
    UnicodeBlock(
        88,
        0x1D000,
        0x1D0FF,
        "Byzantine Musical Symbols",
        3,
        [
            UnicodeBlock(88, 0x1D100, 0x1D1FF, "Musical Symbols", 3),
            UnicodeBlock(88, 0x1D200, 0x1D24F, "Ancient Greek Musical Notation", 4),
        ],
    ),
    UnicodeBlock(89, 0x1D400, 0x1D7FF, "Mathematical Alphanumeric Symbols", 3),
    UnicodeBlock(
        90,
        0xF000,
        0xFFFF,
        "Private Use (plane 15)",
        3,
        [UnicodeBlock(90, 0x10000, 0x10FFFD, "Private Use (plane 16)", 3)],
    ),
    UnicodeBlock(
        91,
        0xFE00,
        0xFE0F,
        "Variation Selectors",
        3,
        [UnicodeBlock(91, 0xE0100, 0xE01EF, "Variation Selectors Supplement", 3)],
    ),
    UnicodeBlock(92, 0xE0000, 0xE007F, "Tags", 3),
    UnicodeBlock(93, 0x1900, 0x194F, "Limbu", 4),
    UnicodeBlock(94, 0x1950, 0x197F, "Tai Le", 4),
    UnicodeBlock(95, 0x1980, 0x19DF, "New Tai Lue", 4),
    UnicodeBlock(96, 0x1A00, 0x1A1F, "Buginese", 4),
    UnicodeBlock(97, 0x2C00, 0x2C5F, "Glagolitic", 4),
    UnicodeBlock(98, 0x2D30, 0x2D7F, "Tifinagh", 4),
    UnicodeBlock(99, 0x4DC0, 0x4DFF, "Yijing Hexagram Symbols", 4),
    UnicodeBlock(100, 0xA800, 0xA82F, "Syloti Nagri", 4),
    UnicodeBlock(
        101,
        0x10000,
        0x1007F,
        "Linear B Syllabary",
        4,
        [
            UnicodeBlock(101, 0x10080, 0x100FF, "Linear B Ideograms", 4),
            UnicodeBlock(101, 0x10100, 0x1013F, "Aegean Numbers", 4),
        ],
    ),
    UnicodeBlock(102, 0x10140, 0x1018F, "Ancient Greek Numbers", 4),
    UnicodeBlock(103, 0x10380, 0x1039F, "Ugaritic", 4),
    UnicodeBlock(104, 0x103A0, 0x103DF, "Old Persian", 4),
    UnicodeBlock(105, 0x10450, 0x1047F, "Shavian", 4),
    UnicodeBlock(106, 0x10480, 0x104AF, "Osmanya", 4),
    UnicodeBlock(107, 0x10800, 0x1083F, "Cypriot Syllabary", 4),
    UnicodeBlock(108, 0x10A00, 0x10A5F, "Kharoshthi", 4),
    UnicodeBlock(109, 0x1D300, 0x1D35F, "Tai Xuan Jing Symbols", 4),
    UnicodeBlock(
        110,
        0x12000,
        0x123FF,
        "Cuneiform",
        4,
        [UnicodeBlock(110, 0x12400, 0x1247F, "Cuneiform Numbers and Punctuation", 4)],
    ),
    UnicodeBlock(111, 0x1D360, 0x1D37F, "Counting Rod Numerals", 4),
    UnicodeBlock(112, 0x1B80, 0x1BBF, "Sundanese", 4),
    UnicodeBlock(113, 0x1C00, 0x1C4F, "Lepcha", 4),
    UnicodeBlock(114, 0x1C50, 0x1C7F, "Ol Chiki", 4),
    UnicodeBlock(115, 0xA880, 0xA8DF, "Saurashtra", 4),
    UnicodeBlock(116, 0xA900, 0xA92F, "Kayah Li", 4),
    UnicodeBlock(117, 0xA930, 0xA95F, "Rejang", 4),
    UnicodeBlock(118, 0xAA00, 0xAA5F, "Cham", 4),
    UnicodeBlock(119, 0x10190, 0x101CF, "Ancient Symbols", 4),
    UnicodeBlock(120, 0x101D0, 0x101FF, "Phaistos Disc", 4),
    UnicodeBlock(
        121,
        0x102A0,
        0x102DF,
        "Carian",
        4,
        [
            UnicodeBlock(121, 0x10280, 0x1029F, "Lycian", 4),
            UnicodeBlock(121, 0x10920, 0x1093F, "Lydian", 4),
        ],
    ),
    UnicodeBlock(
        122,
        0x1F030,
        0x1F09F,
        "Domino Tiles",
        4,
        [UnicodeBlock(122, 0x1F000, 0x1F02F, "Mahjong Tiles", 4)],
    ),
]


def _uni_str_from_int(codepoint: int) -> str | None:
    """
    Get a Unicode string from an integer.

    :Example:
        >>> _uni_str_from_int(65)
        '0x0041'
        >>> _uni_str_from_int(0x10FFFF)
        '0x10FFFF'

    :param codepoint: The codepoint to convert.
    :type codepoint: int
    :return: The Unicode string of the codepoint.
    :rtype: Optional[str]
    """
    if codepoint < 0 or codepoint > 0x10FFFF:  # noqa: PLR2004
        return None

    if codepoint > 0xFFFF:  # noqa: PLR2004
        return f"0x{codepoint:06x}"

    return f"0x{codepoint:04x}"


def _uni_str_from_glyph_name(glyph_name: str) -> str | None:
    """
    Guess the Unicode value of a glyph from its name.

    If the glyph name is not in the expected format (e.g. "uniXXXX" or "uXXXXXX"), it will return None.

    :Example:
        >>> _uni_str_from_glyph_name("uni0041")
        '0x0041'
        >>> _uni_str_from_glyph_name("u10FFFF")
        '0x10FFFF'
        >>> _uni_str_from_glyph_name("A")
        None

    :param glyph_name: The name of the glyph.
    :type glyph_name: str
    :return: The Unicode string of the glyph.
    :rtype: Optional[str]
    """
    for prefix in ("uni", "u"):
        if glyph_name.startswith(prefix) and len(glyph_name) == 7:  # noqa: PLR2004
            try:
                _ = int(glyph_name.replace(prefix, ""), 16)
                return glyph_name.replace(prefix, "0x")
            except ValueError:
                return None
    return None


def _uni_str_from_reversed_cmap(glyph_name: str, reversed_cmap: _ReversedCmap) -> str | None:
    """
    Get the Unicode value of a glyph from the reversed cmap.

    :Example:
        >>> _uni_str_from_reversed_cmap("A", {"A": {65}})
        '0x0041'

    :param glyph_name: The name of the glyph.
    :type glyph_name: str
    :param reversed_cmap: The reversed character map.
    :type reversed_cmap: _ReversedCmap
    :return: The Unicode string of the glyph.
    :rtype: Optional[str]
    """
    codepoints = reversed_cmap.get(glyph_name)
    if not codepoints:
        return None
    return _uni_str_from_int(next(iter(codepoints)))


def _glyph_name_from_uni_str(uni_str: str) -> str | None:
    """
    Guess the name of a glyph from its Unicode value.

    :Example:
        >>> _glyph_name_from_uni_str("0x0041")
        'uni0041'
        >>> _glyph_name_from_uni_str("0x10FFFF")
        'u10FFFF'
        >>> _glyph_name_from_uni_str("0x1F600")
        None

    :param uni_str: The Unicode value of the glyph.
    :type uni_str: str
    :return: The name of the glyph.
    :rtype: Optional[str]
    """
    try:
        codepoint = int(uni_str, 16)
    except ValueError:
        return None

    if 0 <= codepoint <= 0xFFFF:  # noqa: PLR2004
        return f"uni{uni_str.replace('0x', '').upper()}"
    if 0x10000 <= codepoint <= 0x10FFFF:  # noqa: PLR2004
        return f"u{uni_str.replace('0x', '').upper()}"
    return None


def production_name_from_unicode(uni_str: str) -> str | None:
    """
    Get the production name of a glyph from its Unicode value.

    :Example:
        >>> production_name_from_unicode("0x0041")
        'A'
        >>> production_name_from_unicode("0x10FFFF")
        'u10FFFF'
        >>> production_name_from_unicode("0x1F600")
        None

    :param uni_str: The Unicode value of the glyph.
    :type uni_str: str
    :return: The production name of the glyph.
    :rtype: Optional[str]
    """
    return UNICODES_TO_NAMES.get(uni_str, {}).get("production", None)


def prod_name_from_glyph_name(glyph_name: str) -> str | None:
    """
    Get the production name of a glyph from its name.

    :Example:
        >>> prod_name_from_glyph_name("uni0041")
        'A'
        >>> prod_name_from_glyph_name("u10FFFF")
        'u10FFFF'

    :param glyph_name: The name of the glyph.
    :type glyph_name: str
    :return: The production name of the glyph.
    :rtype: Optional[str]
    """
    uni_str = NAMES_TO_UNICODES.get(glyph_name)
    if not uni_str:
        uni_str = _uni_str_from_glyph_name(glyph_name)
    if not uni_str:
        return None
    return production_name_from_unicode(uni_str)


def friendly_name_from_uni_str(uni_str: str) -> str | None:
    """
    Get the friendly name of a glyph from its Unicode value.

    :param uni_str: The Unicode value of the glyph.
    :type uni_str: str
    :return: The friendly name of the glyph.
    :rtype: Optional[str]
    """
    return UNICODES_TO_NAMES.get(uni_str, {}).get("friendly", [None])[0]


def cmap_from_glyph_names(glyphs_list: list[str]) -> _CharacterMap:
    """
    Get the Unicode values for the given list of glyph names.

    :param glyphs_list: The list of glyph names.
    :type glyphs_list: list[str]
    :return: The character map.
    :rtype: _CharacterMap
    """
    new_mapping: _CharacterMap = {}
    for glyph_name in glyphs_list:
        uni_str = NAMES_TO_UNICODES.get(glyph_name)
        if not uni_str:
            uni_str = _uni_str_from_glyph_name(glyph_name)
        if uni_str:
            codepoint = int(uni_str, 16)
            new_mapping.setdefault(codepoint, glyph_name)

    return new_mapping


def _cmap_from_reversed_cmap(reversed_cmap: dict[str, set[int]]) -> _CharacterMap:
    """
    Rebuild the cmap from the reversed cmap. Alternative to getBestCmap.

    :param reversed_cmap: The reversed character map.
    :type reversed_cmap: dict[str, set[int]]
    :return: The character map.
    :rtype: _CharacterMap
    """
    cmap_dict: _CharacterMap = {}

    for glyph_name, codepoints in reversed_cmap.items():
        for codepoint in codepoints:
            cmap_dict[codepoint] = glyph_name

    # Sort the dictionary by codepoint
    return dict(sorted(cmap_dict.items(), key=lambda item: item[0]))


def update_character_map(
    source_cmap: _CharacterMap, target_cmap: _CharacterMap
) -> tuple[_CharacterMap, list[tuple[int, str]], list[tuple[int, str, str]]]:
    """
    Update the target character map with the source character map.

    :param source_cmap: The source character map.
    :type source_cmap: _CharacterMap
    :param target_cmap: The target character map.
    :type target_cmap: _CharacterMap
    :return: A tuple containing the updated character map, remapped and duplicate glyphs.
    :rtype: tuple[_CharacterMap, list[tuple[int, str]], list[tuple[int, str, str]]]
    """
    updated_cmap = target_cmap.copy()
    duplicates: list[tuple[int, str, str]] = []
    remapped: list[tuple[int, str]] = []

    for codepoint, glyph_name in source_cmap.items():
        if codepoint in updated_cmap:
            duplicates.append((codepoint, glyph_name, updated_cmap[codepoint]))
        else:
            remapped.append((codepoint, glyph_name))
            updated_cmap[codepoint] = glyph_name

    return updated_cmap, remapped, duplicates


def create_cmap_tables(subtable_format: int, platform_id: int, plat_enc_id: int, cmap: _CharacterMap) -> CmapSubtable:
    """
    Create a cmap subtable with the given parameters.

    :param subtable_format: The subtable format.
    :type subtable_format: int
    :param platform_id: The platform ID.
    :type platform_id: int
    :param plat_enc_id: The platform encoding ID.
    :type plat_enc_id: int
    :param cmap: The character map.
    :type cmap: _CharacterMap
    :return: The cmap subtable.
    :rtype: CmapSubtable
    """
    cmap_table = CmapSubtable.newSubtable(subtable_format)
    cmap_table.platformID = platform_id
    cmap_table.platEncID = plat_enc_id
    cmap_table.language = 0
    cmap_table.cmap = cmap
    return cmap_table


def setup_character_map(ttfont: TTFont, mapping: _CharacterMap) -> None:
    """
    Set up the character map for the given ``TTFont`` object.

    :param ttfont: The ``TTFont`` object.
    :type ttfont: TTFont
    :param mapping: The character map.
    :type mapping: _CharacterMap
    """
    out_tables: list[CmapSubtable] = []

    max_unicode = max(mapping, default=0)  # Avoid max() error on empty dict
    if max_unicode > 0xFFFF:  # noqa: PLR2004
        cmap_3_1 = {k: v for k, v in mapping.items() if k <= 0xFFFF}  # noqa: PLR2004
        cmap_3_10 = mapping
    else:
        cmap_3_1 = mapping
        cmap_3_10 = {}

    if cmap_3_1:
        out_tables.append(create_cmap_tables(4, 3, 1, cmap_3_1))
        out_tables.append(create_cmap_tables(4, 0, 3, cmap_3_1))

    if cmap_3_10:
        out_tables.append(create_cmap_tables(12, 3, 10, cmap_3_10))
        out_tables.append(create_cmap_tables(12, 0, 4, cmap_3_10))

    cmap_table = newTable(T_CMAP)
    cmap_table.tableVersion = 0
    cmap_table.tables = out_tables

    ttfont[T_CMAP] = cmap_table


def _get_multi_mapped_glyphs(
    reversed_cmap: dict[str, set[int]],
) -> list[tuple[str, list[int]]]:
    """
    Get the glyphs that are mapped to multiple Unicode values.

    :param reversed_cmap: The reversed character map.
    :type reversed_cmap: dict[str, set[int]]
    :return: The multi-mapped glyphs.
    :rtype: list[tuple[str, list[int]]]
    """
    multi_mapped = []
    for glyph_name, codepoints in reversed_cmap.items():
        if len(codepoints) > 1:
            multi_mapped.append((glyph_name, list(codepoints)))
    return multi_mapped


def unicode_from_glyph_name(glyph_name: str, reversed_cmap: _ReversedCmap) -> str | None:
    """
    Attempt to retrieve a Unicode string, using various fallback mechanisms.

    It will try to:
        * check if the glyph is present in the reversed cmap;
        * check if the Unicode value is present in the JSON file;
        * calculate the Unicode value from the glyph name;

    :param glyph_name: The name of the glyph.
    :type glyph_name: str
    :param reversed_cmap: The reversed character map.
    :type reversed_cmap: _ReversedCmap
    :return: The Unicode string of the glyph.
    :rtype: Optional[str]
    """
    unicode_string = _uni_str_from_reversed_cmap(glyph_name, reversed_cmap)
    if not unicode_string:
        unicode_string = NAMES_TO_UNICODES.get(glyph_name)
    if not unicode_string:
        unicode_string = _uni_str_from_glyph_name(glyph_name)
    return unicode_string
