from copy import deepcopy
from typing import Optional

from fontTools.misc.roundTools import otRound
from fontTools.misc.textTools import num2binary
from fontTools.otlLib.maxContextCalc import maxCtxFont
from fontTools.pens.boundsPen import BoundsPen
from fontTools.ttLib import TTFont
from fontTools.ttLib.tables.O_S_2f_2 import table_O_S_2f_2

from foundrytools.constants import (
    MAX_US_WEIGHT_CLASS,
    MAX_US_WIDTH_CLASS,
    MIN_US_WEIGHT_CLASS,
    MIN_US_WIDTH_CLASS,
    T_CMAP,
    T_OS_2,
)
from foundrytools.core.tables.default import DefaultTbl
from foundrytools.lib.unicode import (
    OS_2_UNICODE_RANGES,
    check_block_support,
    count_block_codepoints,
)
from foundrytools.utils.bits_tools import is_nth_bit_set

ITALIC_BIT = 0
UNDERSCORE_BIT = 1
NEGATIVE_BIT = 2
OUTLINED_BIT = 3
STRIKEOUT_BIT = 4
BOLD_BIT = 5
REGULAR_BIT = 6
USE_TYPO_METRICS_BIT = 7
WWS_BIT = 8
OBLIQUE_BIT = 9
NO_SUBSETTING_BIT = 8
BITMAP_EMBED_ONLY_BIT = 9

MIN_OS2_VERSION = 0
MAX_OS2_VERSION = 5


class InvalidOS2VersionError(Exception):
    """
    Exception raised when trying to access a field that is not defined in the current OS/2 table
    version.
    """


class FsSelection:
    """A wrapper class for the ``fsSelection`` field of the ``OS/2`` table."""

    def __init__(self, os_2_table: "OS2Table"):
        """
        Initializes the ``fsSelection`` field of the ``OS/2`` table.

        :param os_2_table: The ``OS/2`` table.
        :type os_2_table: OS2Table
        """
        self.os_2_table = os_2_table

    def __repr__(self) -> str:
        return f"fsSelection({num2binary(self.os_2_table.table.fsSelection)})"

    @property
    def italic(self) -> bool:
        """
        A property with getter and setter for bit 0 (ITALIC) in the ``OS/2.fsSelection`` field.

        :return: True if bit 0 is set, False otherwise.
        :rtype: bool
        """
        return is_nth_bit_set(self.os_2_table.table.fsSelection, ITALIC_BIT)

    @italic.setter
    def italic(self, value: bool) -> None:
        """Sets bit 0 (ITALIC) of the ``OS/2.fsSelection`` field."""
        self.os_2_table.set_bit(field_name="fsSelection", pos=ITALIC_BIT, value=value)

    @property
    def underscore(self) -> bool:
        """
        A property with getter and setter for bit 1 (UNDERSCORE) in the ``OS/2.fsSelection`` field.

        :return: True if bit 1 is set, False otherwise.
        :rtype: bool
        """
        return is_nth_bit_set(self.os_2_table.table.fsSelection, UNDERSCORE_BIT)

    @underscore.setter
    def underscore(self, value: bool) -> None:
        """
        Sets bit 1 (UNDERSCORE) of the ``OS/2.fsSelection`` field.

        :param value: The value to set.
        :type value: bool
        """
        self.os_2_table.set_bit(field_name="fsSelection", pos=UNDERSCORE_BIT, value=value)

    @property
    def negative(self) -> bool:
        """
        A property with getter and setter for bit 2 (NEGATIVE) in the ``OS/2.fsSelection`` field.

        :return: True if bit 2 is set, False otherwise.
        :rtype: bool
        """
        return is_nth_bit_set(self.os_2_table.table.fsSelection, NEGATIVE_BIT)

    @negative.setter
    def negative(self, value: bool) -> None:
        """Sets bit 2 (NEGATIVE) of the ``OS/2.fsSelection`` field."""
        self.os_2_table.set_bit(field_name="fsSelection", pos=NEGATIVE_BIT, value=value)

    @property
    def outlined(self) -> bool:
        """
        A property with getter and setter for bit 3 (OUTLINED) in the ``OS/2.fsSelection`` field.

        :return: True if bit 3 is set, False otherwise.
        :rtype: bool
        """
        return is_nth_bit_set(self.os_2_table.table.fsSelection, OUTLINED_BIT)

    @outlined.setter
    def outlined(self, value: bool) -> None:
        """Sets bit 3 (OUTLINED) of the ``OS/2.fsSelection`` field."""
        self.os_2_table.set_bit(field_name="fsSelection", pos=OUTLINED_BIT, value=value)

    @property
    def strikeout(self) -> bool:
        """
        A property with getter and setter for bit 4 (STRIKEOUT) in the ``OS/2.fsSelection`` field.

        :return: True if bit 4 is set, False otherwise.
        :rtype: bool
        """
        return is_nth_bit_set(self.os_2_table.table.fsSelection, STRIKEOUT_BIT)

    @strikeout.setter
    def strikeout(self, value: bool) -> None:
        """Sets bit 4 (STRIKEOUT) of the ``OS/2.fsSelection`` field."""
        self.os_2_table.set_bit(field_name="fsSelection", pos=STRIKEOUT_BIT, value=value)

    @property
    def bold(self) -> bool:
        """
        A property with getter and setter for bit 5 (BOLD) in the ``OS/2.fsSelection`` field.

        :return: True if bit 5 is set, False otherwise.
        :rtype: bool
        """
        return is_nth_bit_set(self.os_2_table.table.fsSelection, BOLD_BIT)

    @bold.setter
    def bold(self, value: bool) -> None:
        """Sets the bit 5 (BOLD) of the ``OS/2.fsSelection`` field."""
        self.os_2_table.set_bit(field_name="fsSelection", pos=BOLD_BIT, value=value)

    @property
    def regular(self) -> bool:
        """
        A property with getter and setter for bit 6 (REGULAR) in the ``OS/2.fsSelection`` field.

        :return: True if bit 6 is set, False otherwise.
        :rtype: bool
        """
        return is_nth_bit_set(self.os_2_table.table.fsSelection, REGULAR_BIT)

    @regular.setter
    def regular(self, value: bool) -> None:
        """Sets bit 6 (REGULAR) of the ``OS/2.fsSelection`` field."""
        self.os_2_table.set_bit(field_name="fsSelection", pos=REGULAR_BIT, value=value)

    @property
    def use_typo_metrics(self) -> bool:
        """
        A property with getter and setter for bit 7 (USE_TYPO_METRICS) in the ``OS/2.fsSelection``

        :return: True if bit 7 is set, False otherwise.
        :rtype: bool
        """
        return is_nth_bit_set(self.os_2_table.table.fsSelection, USE_TYPO_METRICS_BIT)

    @use_typo_metrics.setter
    def use_typo_metrics(self, value: bool) -> None:
        """Sets bit 7 (USE_TYPO_METRICS) of the ``OS/2.fsSelection`` field."""
        if self.os_2_table.version < 4 and value is True:
            raise InvalidOS2VersionError(
                "fsSelection bit 7 (USE_TYPO_METRICS) is only defined in OS/2 table versions 4 and "
                "up."
            )
        self.os_2_table.set_bit(field_name="fsSelection", pos=USE_TYPO_METRICS_BIT, value=value)

    @property
    def wws_consistent(self) -> bool:
        """
        A property with getter and setter for bit 8 (WWS) in the ``OS/2.fsSelection`` field.

        :return: True if bit 8 is set, False otherwise.
        :rtype: bool
        """
        return is_nth_bit_set(self.os_2_table.table.fsSelection, WWS_BIT)

    @wws_consistent.setter
    def wws_consistent(self, value: bool) -> None:
        """Sets bit 8 (WWS) of the ``OS/2.fsSelection`` field."""
        if self.os_2_table.version < 4 and value is True:
            raise InvalidOS2VersionError(
                "fsSelection bit 8 (WWS) is only defined in OS/2 table versions 4 and up."
            )
        self.os_2_table.set_bit(field_name="fsSelection", pos=WWS_BIT, value=value)

    @property
    def oblique(self) -> bool:
        """
        A property with getter and setter for bit 9 (OBLIQUE) in the ``OS/2.fsSelection`` field.

        :return: True if bit 9 is set, False otherwise.
        :rtype: bool
        """
        return is_nth_bit_set(self.os_2_table.table.fsSelection, OBLIQUE_BIT)

    @oblique.setter
    def oblique(self, value: bool) -> None:
        """Sets the bit 9 (OBLIQUE) of the ``OS/2.fsSelection`` field."""
        if self.os_2_table.version < 4:
            raise InvalidOS2VersionError(
                "fsSelection bit 9 (OBLIQUE) is only defined in OS/2 table versions 4 and up."
            )
        self.os_2_table.set_bit(field_name="fsSelection", pos=OBLIQUE_BIT, value=value)


class OS2Table(DefaultTbl):  # pylint: disable=too-many-public-methods, too-many-instance-attributes
    """This class extends the fontTools ``OS/2`` table."""

    def __init__(self, ttfont: TTFont):
        """
        Initializes the ``OS/2`` table handler.

        :param ttfont: The ``TTFont`` object.
        :type ttfont: TTFont
        """
        super().__init__(ttfont=ttfont, table_tag=T_OS_2)
        self.fs_selection = FsSelection(self)
        self._copy = deepcopy(self.table)

    @property
    def table(self) -> table_O_S_2f_2:
        """
        The wrapped ``table_O_S_2f_2`` table object.
        """
        return self._table

    @table.setter
    def table(self, value: table_O_S_2f_2) -> None:
        """
        Wraps a new ``table_O_S_2f_2`` object.
        """
        self._table = value

    @property
    def is_modified(self) -> bool:
        """
        A property that returns True if the OS/2 table has been modified.

        :return: True if the OS/2 table has been modified, False otherwise.
        :rtype: bool
        """
        return self._copy.compile(self.ttfont) != self.table.compile(self.ttfont)

    @property
    def version(self) -> int:
        """
        A property with getter and setter for the ``OS/2.version`` field.

        Valid values are between 0 and 5.

        :return: The ``OS/2.version`` value.
        :rtype: int
        """
        return self.table.version

    @version.setter
    def version(self, value: int) -> None:
        """
        Sets the ``OS/2.version`` value.

        :param value: The value to set.
        :type value: int
        :raises: ValueError: If the value is not between 0 and 5.
        """
        if value < MIN_OS2_VERSION or value > MAX_OS2_VERSION:
            raise ValueError(
                f"Invalid value for version: {value}. "
                f"Expected a value between {MIN_OS2_VERSION} and {MAX_OS2_VERSION}."
            )
        self.table.version = value

    @property
    def weight_class(self) -> int:
        """
        A property with getter and setter for the ``OS/2.usWeightClass`` field.

        The value can be an integer between 1 and 1000.

        :return: The ``OS/2.usWeightClass`` value.
        :rtype: int
        """
        return self.table.usWeightClass

    @weight_class.setter
    def weight_class(self, value: int) -> None:
        """
        Sets the ``OS/2.usWeightClass`` value.

        :param value: The value to set.
        :type value: int
        """
        if value < MIN_US_WEIGHT_CLASS or value > MAX_US_WEIGHT_CLASS:
            raise ValueError(
                f"Invalid value for usWeightClass: {value}. "
                f"Expected a value between {MIN_US_WEIGHT_CLASS} and {MAX_US_WEIGHT_CLASS}."
            )
        self.table.usWeightClass = value

    @property
    def width_class(self) -> int:
        """
        A property with getter and setter for the ``OS/2.usWidthClass`` field.

        The value can be an integer between 1 and 9.

        :return: The ``OS/2.usWidthClass`` value.
        :rtype: int
        """
        return self.table.usWidthClass

    @width_class.setter
    def width_class(self, value: int) -> None:
        """
        Sets the ``OS/2.usWidthClass`` value.

        :param value: The value to set.
        :type value: int
        """
        if value < MIN_US_WIDTH_CLASS or value > MAX_US_WIDTH_CLASS:
            raise ValueError(
                f"Invalid value for usWidthClass: {value}. "
                f"Expected a value between {MIN_US_WIDTH_CLASS} and {MAX_US_WIDTH_CLASS}."
            )
        self.table.usWidthClass = value

    @property
    def embed_level(self) -> int:
        """
        A property with getter and setter for the embedding level of the ``OS/2.fsType`` field.

        The value can be 0, 2, 4 or 8.

        * 0: Installable Embedding
        * 2: Restricted License Embedding
        * 4: Preview & Print Embedding
        * 8: Editable Embedding
        """
        return int(num2binary(self.table.fsType, 16)[9:17], 2)

    @embed_level.setter
    def embed_level(self, value: int) -> None:
        """
        Sets the embedding level of the ``OS/2.fsType`` field.

        :param value: The value to set.
        :type value: int
        """
        bit_operands = {
            0: ([0, 1, 2, 3], None),
            2: ([0, 2, 3], 1),
            4: ([0, 1, 3], 2),
            8: ([0, 1, 2], 3),
        }

        if value not in bit_operands:
            raise ValueError("Invalid value: embed_level must be 0, 2, 4 or 8.")

        bits_to_unset, bit_to_set = bit_operands[value]

        for b in bits_to_unset:
            self.set_bit(field_name="fsType", pos=b, value=False)

        if bit_to_set is not None:
            self.set_bit(field_name="fsType", pos=bit_to_set, value=True)

    @property
    def no_subsetting(self) -> bool:
        """
        A property with getter and setter for bit 8 (NO_SUBSETTING) in the ``OS/2.fsType`` field.

        :return: True if bit 8 is set, False otherwise.
        :rtype: bool
        """
        return is_nth_bit_set(self.table.fsType, NO_SUBSETTING_BIT)

    @no_subsetting.setter
    def no_subsetting(self, value: bool) -> None:
        """
        Sets bit 8 (NO_SUBSETTING) of the ``OS/2.fsType`` field.

        :param value: The value to set.
        :type value: bool
        """
        self.set_bit(field_name="fsType", pos=NO_SUBSETTING_BIT, value=value)

    @property
    def bitmap_embed_only(self) -> bool:
        """
        A property with getter and setter for bit 9 (BITMAP_EMBED_ONLY) in the ``OS/2.fsType``
        field.

        :return: True if bit 9 is set, False otherwise.
        :rtype: bool
        """
        return is_nth_bit_set(self.table.fsType, BITMAP_EMBED_ONLY_BIT)

    @bitmap_embed_only.setter
    def bitmap_embed_only(self, value: bool) -> None:
        """
        Sets bit 9 (BITMAP_EMBED_ONLY) of the ``OS/2.fsType`` field.

        :param value: The value to set.
        :type value: bool
        """
        self.set_bit(field_name="fsType", pos=BITMAP_EMBED_ONLY_BIT, value=value)

    @property
    def vendor_id(self) -> str:
        """
        A property with getter and setter for the ``OS/2.achVendID`` field.

        When setting the property value, it is padded with spaces to a length of 4.

        :return: The ``OS/2.achVendID`` value.
        :rtype: str
        """
        return self.table.achVendID

    @vendor_id.setter
    def vendor_id(self, value: str) -> None:
        """
        Sets the ``OS/2.achVendID`` value.

        :param value: The value to set.
        :type value: str
        """
        value = value.ljust(4, " ") if len(value) < 4 else value[:4]
        self.table.achVendID = value

    @property
    def typo_ascender(self) -> int:
        """
        A property with getter and setter for the ``OS/2.sTypoAscender`` field.

        :return: The ``OS/2.sTypoAscender`` value.
        :rtype: int
        """
        return self.table.sTypoAscender

    @typo_ascender.setter
    def typo_ascender(self, value: int) -> None:
        """
        Sets the ``OS/2.sTypoAscender`` value.

        :param value: The value to set.
        :type value: int
        """
        self.table.sTypoAscender = value

    @property
    def typo_descender(self) -> int:
        """
        A property with getter and setter for the ``OS/2.sTypoDescender`` field.

        :return: The ``OS/2.sTypoDescender`` value.
        :rtype: int
        """
        return self.table.sTypoDescender

    @typo_descender.setter
    def typo_descender(self, value: int) -> None:
        """
        Sets the ``OS/2.sTypoDescender`` value.

        :param value: The value to set.
        :type value: int
        """
        self.table.sTypoDescender = value

    @property
    def typo_line_gap(self) -> int:
        """
        A property with getter and setter for the ``OS/2.sTypoLineGap`` field.

        :return: The ``OS/2.sTypoLineGap`` value.
        :rtype: int
        """
        return self.table.sTypoLineGap

    @typo_line_gap.setter
    def typo_line_gap(self, value: int) -> None:
        """
        Sets the ``OS/2.sTypoLineGap`` value.

        :param value: The value to set.
        :type value: int
        """
        self.table.sTypoLineGap = value

    @property
    def win_ascent(self) -> int:
        """
        A property with getter and setter for the ``OS/2.usWinAscent`` field.

        :return: The ``OS/2.usWinAscent`` value.
        :rtype: int
        """
        return self.table.usWinAscent

    @win_ascent.setter
    def win_ascent(self, value: int) -> None:
        """
        Sets the ``OS/2.usWinAscent`` value.

        :param value: The value to set.
        :type value: int
        """
        self.table.usWinAscent = value

    @property
    def win_descent(self) -> int:
        """
        A property with getter and setter for the ``OS/2.usWinDescent`` field.

        :return: The ``OS/2.usWinDescent`` value.
        :rtype: int
        """
        return self.table.usWinDescent

    @win_descent.setter
    def win_descent(self, value: int) -> None:
        """
        Sets the ``OS/2.usWinDescent`` value.

        :param value: The value to set.
        :type value: int
        """
        self.table.usWinDescent = value

    @property
    def x_height(self) -> Optional[int]:
        """
        A property with getter and setter for the ``OS/2.sxHeight`` field.

        ``sxHeight`` is only defined in ``OS/2`` table versions 2 and up.

        :return: The ``OS/2.sxHeight`` value.
        :rtype: int
        """
        if self.version < 2:
            return None
        return self.table.sxHeight

    @x_height.setter
    def x_height(self, value: int) -> None:
        """
        Sets the ``OS/2.sxHeight`` value.

        :param value: The value to set.
        :type value: int
        :raises: InvalidOS2VersionError: If the ``OS/2`` table version is less than 2.
        """
        if self.version < 2:
            raise InvalidOS2VersionError(
                "sxHeight is only defined in OS/2 table versions 2 and up."
            )
        self.table.sxHeight = value

    @property
    def cap_height(self) -> Optional[int]:
        """
        A property with getter and setter for the ``OS/2.sCapHeight`` field.

        ``sCapHeight`` is only defined in OS/2 table versions 2 and up.

        :return: The ``OS/2.sCapHeight`` value.
        :rtype: int
        """
        if self.version < 2:
            return None
        return self.table.sCapHeight

    @cap_height.setter
    def cap_height(self, value: int) -> None:
        """
        Sets the ``OS/2.sCapHeight`` value.

        :param value: The value to set.
        :type value: int
        :raises: InvalidOS2VersionError: If the OS/2 table version is less than 2.
        """
        if self.version < 2:
            raise InvalidOS2VersionError(
                "sCapHeight is only defined in OS/2 table versions 2 and up."
            )
        self.table.sCapHeight = value

    @property
    def max_context(self) -> Optional[int]:
        """
        A property with getter and setter for the ``OS/2.usMaxContext`` field.

        ``usMaxContext`` is only defined in OS/2 table versions 2 and up.

        :return: The ``OS/2.usMaxContext`` value.
        :rtype: int
        """
        if self.version < 2:
            return None
        return self.table.usMaxContext

    @max_context.setter
    def max_context(self, value: int) -> None:
        """
        Sets the ``OS/2.usMaxContext`` value.

        :param value: The value to set.
        :type value: int
        :raises: InvalidOS2VersionError: If the OS/2 table version is less than 2.
        """
        if self.version < 2:
            raise InvalidOS2VersionError(
                "usMaxContext is only defined in OS/2 table versions 2 and up."
            )
        self.table.usMaxContext = value

    @property
    def unicode_ranges(self) -> set[int]:
        """
        A property with getter and setter for the ``OS/2.ulUnicodeRange(1-4)`` fields.

        :return: The Unicode ranges of the ``OS/2`` table.
        :rtype: set[int]
        """
        return self.table.getUnicodeRanges()

    @unicode_ranges.setter
    def unicode_ranges(self, bits: set[int]) -> None:
        """
        Sets the ``OS/2.ulUnicodeRange(1-4)`` fields.

        :param bits: The Unicode ranges to set.
        :type bits: set[int]
        """
        self.table.setUnicodeRanges(bits)

    @property
    def codepage_ranges(self) -> set[int]:
        """
        A property with getter and setter for the ``OS/2.ulCodePageRange(1-2)`` fields.

        :return: The code page ranges of the ``OS/2`` table.
        :rtype: set[int]
        """
        return self.table.getCodePageRanges()

    @codepage_ranges.setter
    def codepage_ranges(self, bits: set[int]) -> None:
        """
        Sets the ``OS/2.ulCodePageRange(1-2)`` fields.

        :param bits: The code page ranges to set.
        :type bits: set[int]
        """
        self.table.setCodePageRanges(bits)

    def recalc_avg_char_width(self) -> int:
        """
        Recalculates the ``OS/2.xAvgCharWidth`` value.

        :return: The new ``OS/2.xAvgCharWidth`` value.
        :rtype: int
        """
        return self.table.recalcAvgCharWidth(ttFont=self.ttfont)

    def recalc_max_context(self) -> None:
        """Recalculates the ``OS/2.usMaxContext`` value."""
        self.max_context = maxCtxFont(self.ttfont)

    def recalc_unicode_ranges(self, percentage: float = 33.0) -> set[tuple[int, str, str]]:
        """
        Recalculates the ``OS/2.ulUnicodeRange(1-4)`` fields.

        :param percentage: The percentage of codepoints that must be present in a Unicode block for
            it to be enabled. Default is 33.0.
        :type percentage: float
        :return: A set of tuples with the modified Unicode ranges.
        :rtype: set[tuple[int, str, str]]
        :raises: KeyError: If the font does not have a cmap table.
        """
        if T_CMAP not in self.ttfont:
            raise KeyError("Font does not have a cmap table")

        cmap_table = self.ttfont[T_CMAP]
        unicodes = set()
        has_cmap_32 = False

        for table in cmap_table.tables:
            if table.isUnicode():
                unicodes.update(table.cmap.keys())
            if table.platformID == 3 and table.platEncID == 10:
                has_cmap_32 = True

        new_unicode_ranges = set()
        modified_unicode_ranges = set()

        for block in OS_2_UNICODE_RANGES:
            min_codepoints = otRound(block.size / 100 * percentage) if block.bit_number != 57 else 1
            found_codepoints = count_block_codepoints(block, unicodes)
            is_enabled = block.bit_number in self.unicode_ranges
            is_supported = check_block_support(
                block, found_codepoints, min_codepoints, self.version, has_cmap_32
            )

            if is_supported:
                new_unicode_ranges.add(block.bit_number)
                if not is_enabled:
                    modified_unicode_ranges.add((block.bit_number, block.block_name, "enabled"))
            else:
                if is_enabled:
                    modified_unicode_ranges.add((block.bit_number, block.block_name, "disabled"))

        self.unicode_ranges = new_unicode_ranges
        return modified_unicode_ranges

    def recalc_code_page_ranges(self) -> None:
        """Recalculates the code page ranges of the ``OS/2`` table."""
        self.table.recalcCodePageRanges(self.ttfont)

    def upgrade(self, target_version: int) -> None:
        """
        Upgrades the ``OS/2`` table to a more recent version.

        :param target_version: The target version to upgrade to.
        :type target_version: int
        :raises: InvalidOS2VersionError: If the target version is less than the current version.
        """
        current_version = self.version
        if target_version <= current_version:
            raise InvalidOS2VersionError(
                f"The target version must be greater than the current version ({current_version})."
            )

        # Used to recalc xHeight and capHeight
        def _get_glyph_height(glyph_name: str) -> int:
            glyph_set = self.ttfont.getGlyphSet()
            if glyph_name not in glyph_set:
                return 0
            bounds_pen = BoundsPen(glyphSet=glyph_set)
            glyph_set[glyph_name].draw(bounds_pen)
            return otRound(bounds_pen.bounds[3])

        self.version = target_version

        if current_version < 1:
            self.recalc_code_page_ranges()

        if target_version == 1:
            return

        if current_version < 2:
            self.x_height = _get_glyph_height("x")
            self.cap_height = _get_glyph_height("H")
            self.table.usDefaultChar = 0
            self.table.usBreakChar = 32
            self.recalc_max_context()

        if target_version == 5:
            self.table.usLowerOpticalPointSize = 0
            self.table.usUpperOpticalPointSize = 65535 / 20

        if target_version < 4:
            self.fs_selection.use_typo_metrics = False
            self.fs_selection.wws_consistent = False
            self.fs_selection.oblique = False
