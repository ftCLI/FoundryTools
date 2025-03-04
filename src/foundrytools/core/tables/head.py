"""Head table."""

from __future__ import annotations

from copy import deepcopy
from typing import TYPE_CHECKING

from fontTools.misc.textTools import num2binary

from foundrytools.constants import T_HEAD
from foundrytools.core.tables.default import DefaultTbl
from foundrytools.utils.bits_tools import is_nth_bit_set

if TYPE_CHECKING:
    from fontTools.ttLib import TTFont
    from fontTools.ttLib.tables._h_e_a_d import table__h_e_a_d

BOLD_BIT = 0
ITALIC_BIT = 1


class MacStyle:
    """A wrapper class for the ``macStyle`` field of the ``head`` table."""

    def __init__(self, head_table: HeadTable) -> None:
        """
        Initialize the ``macStyle`` field of the ``head`` table.

        :param head_table: The ``head`` table.
        :type head_table: HeadTable
        """
        self.head_table = head_table

    def __repr__(self) -> str:
        """Debug info."""
        return f"macStyle({num2binary(self.head_table.table.macStyle)})"

    @property
    def bold(self) -> bool:
        """
        A property with getter and setter for bit 0 (BOLD) in the ``macStyle`` field of the ``head`` table.

        :return: True if bit 0 is set, False otherwise.
        :rtype: bool
        """
        return is_nth_bit_set(self.head_table.table.macStyle, BOLD_BIT)

    @bold.setter
    def bold(self, value: bool) -> None:
        """Set bit 0 (BOLD_BIT) in the ``head.macStyle`` field."""
        self.head_table.set_bit(field_name="macStyle", pos=BOLD_BIT, value=value)

    @property
    def italic(self) -> bool:
        """
        A property with getter and setter for bit 1 (ITALIC) in the ``macStyle`` field of the ``head`` table.

        :return: True if bit 1 is set, False otherwise.
        :rtype: bool
        """
        return is_nth_bit_set(self.head_table.table.macStyle, ITALIC_BIT)

    @italic.setter
    def italic(self, value: bool) -> None:
        """Set the bit 1 (ITALIC_BIT) in the ``head.macStyle`` field."""
        self.head_table.set_bit(field_name="macStyle", pos=ITALIC_BIT, value=value)


class HeadTable(DefaultTbl):
    """Extend the fontTools ``head`` table."""

    def __init__(self, ttfont: TTFont) -> None:
        """
        Initialize the ``head`` table handler.

        :param ttfont: The ``TTFont`` object.
        :type ttfont: TTFont
        """
        super().__init__(ttfont=ttfont, table_tag=T_HEAD)
        self.mac_style = MacStyle(head_table=self)
        self._copy = deepcopy(self.table)

    @property
    def table(self) -> table__h_e_a_d:
        """The wrapped ``table__h_e_a_d`` table object."""
        return self._table

    @table.setter
    def table(self, value: table__h_e_a_d) -> None:
        """Wrap a new ``table__h_e_a_d`` object."""
        self._table = value

    @property
    def is_modified(self) -> bool:
        """
        A property that returns True if the ``head`` table has been modified, False otherwise.

        :return: True if the ``head`` table has been modified, False otherwise.
        :rtype: bool
        """
        return self._copy.compile(self.ttfont) != self.table.compile(self.ttfont)

    @property
    def font_revision(self) -> float:
        """
        A property with getter and setter for the ``fontRevision`` field of the ``head`` table.

        :return: The font revision value.
        :rtype: float
        """
        return self.table.fontRevision

    @font_revision.setter
    def font_revision(self, value: float) -> None:
        """Set the ``fontRevision`` field of the ``head`` table."""
        self.table.fontRevision = value

    @property
    def units_per_em(self) -> int:
        """
        A read-only property for the ``unitsPerEm`` field of the ``head`` table.

        :return: The units per em value.
        :rtype: int
        """
        return self.table.unitsPerEm

    @property
    def created_timestamp(self) -> int:
        """
        A property with getter and setter for the ``created`` field of the ``head`` table.

        :return: The created timestamp.
        :rtype: int
        """
        return self.table.created

    @created_timestamp.setter
    def created_timestamp(self, value: int) -> None:
        """Set ``created`` field of the ``head`` table."""
        self.table.created = value

    @property
    def modified_timestamp(self) -> int:
        """
        A property with getter and setter for the ``modified`` field of the ``head`` table.

        :return: The modified timestamp.
        :rtype: int
        """
        return self.table.modified

    @modified_timestamp.setter
    def modified_timestamp(self, value: int) -> None:
        """Set the ``modified`` field of the ``head`` table."""
        self.table.modified = value

    @property
    def x_min(self) -> int:
        """
        A property with getter and setter for the ``xMin`` field of the ``head`` table.

        :return: The ``xMin`` value.
        :rtype: int
        """
        return self.table.xMin

    @x_min.setter
    def x_min(self, value: int) -> None:
        """Set the ``xMin`` field of the ``head`` table."""
        self.table.xMin = value

    @property
    def y_min(self) -> int:
        """
        A property with getter and setter for the ``yMin`` field of the ``head`` table.

        :return: The ``yMin`` value.
        :rtype: int
        """
        return self.table.yMin

    @y_min.setter
    def y_min(self, value: int) -> None:
        """Set the ``yMin`` field of the ``head`` table."""
        self.table.yMin = value

    @property
    def x_max(self) -> int:
        """
        A property with getter and setter for the ``xMax`` field of the ``head`` table.

        :return: The ``xMax`` value.
        :rtype: int
        """
        return self.table.xMax

    @x_max.setter
    def x_max(self, value: int) -> None:
        """Set the ``xMax`` field of the ``head`` table."""
        self.table.xMax = value

    @property
    def y_max(self) -> int:
        """
        A property with getter and setter for the ``yMax`` field of the ``head`` table.

        :return: The ``yMax`` value.
        :rtype: int
        """
        return self.table.yMax

    @y_max.setter
    def y_max(self, value: int) -> None:
        """Set the ``yMax`` field of the ``head`` table."""
        self.table.yMax = value
