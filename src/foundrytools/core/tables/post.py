"""Post table."""

from __future__ import annotations

from copy import deepcopy
from typing import TYPE_CHECKING

from foundrytools.constants import T_POST
from foundrytools.core.tables.default import DefaultTbl

if TYPE_CHECKING:
    from fontTools.ttLib import TTFont
    from fontTools.ttLib.tables._p_o_s_t import table__p_o_s_t


class PostTable(DefaultTbl):
    """Extends the fontTools ``post`` table."""

    def __init__(self, ttfont: TTFont) -> None:
        """
        Initialize the ``post`` table handler.

        :param ttfont: The ``TTFont`` object.
        :type ttfont: TTFont
        """
        super().__init__(ttfont=ttfont, table_tag=T_POST)
        self._copy = deepcopy(self.table)

    @property
    def table(self) -> table__p_o_s_t:
        """The wrapped ``table__p_o_s_t`` table object."""
        return self._table

    @table.setter
    def table(self, value: table__p_o_s_t) -> None:
        """Wrap a new ``table__p_o_s_t`` object."""
        self._table = value

    @property
    def is_modified(self) -> bool:
        """
        Checks if the table has been modified.

        :return: True if the table has been modified, False otherwise.
        :rtype: bool
        """
        return self._copy.compile(self.ttfont) != self.table.compile(self.ttfont)

    @property
    def italic_angle(self) -> float:
        """
        A property with getter and setter for the ``post.italicAngle`` field.

        :return: The italic angle value.
        :rtype: float
        """
        return self.table.italicAngle

    @italic_angle.setter
    def italic_angle(self, value: float) -> None:
        """
        Set the ``post.italicAngle`` value.

        :param value: The new italic angle value.
        :type value: float
        """
        self.table.italicAngle = value

    @property
    def underline_position(self) -> int:
        """
        A property with getter and setter for the ``post.underlinePosition`` field.

        :return: The underline position value.
        :rtype: int
        """
        return self.table.underlinePosition

    @underline_position.setter
    def underline_position(self, value: int) -> None:
        """
        Set the ``post.underlinePosition`` value.

        :param value: The new underline position value.
        :type value: int
        """
        self.table.underlinePosition = value

    @property
    def underline_thickness(self) -> int:
        """
        A property with getter and setter for the ``post.underlineThickness`` field.

        :return: The underline thickness value.
        :rtype: int
        """
        return self.table.underlineThickness

    @underline_thickness.setter
    def underline_thickness(self, value: int) -> None:
        """
        Set the ``post.underlineThickness`` value.

        :param value: The new underline thickness value.
        :type value: int
        """
        self.table.underlineThickness = value

    @property
    def fixed_pitch(self) -> bool:
        """
        A property with getter and setter for the ``post.isFixedPitch`` field.

        :return: The isFixedPitch value.
        :rtype: bool
        """
        return bool(self.table.isFixedPitch)

    @fixed_pitch.setter
    def fixed_pitch(self, value: bool) -> None:
        """
        Set the ``post.isFixedPitch`` value.

        :param value: The new isFixedPitch value.
        :type value: bool
        """
        self.table.isFixedPitch = abs(int(value))
