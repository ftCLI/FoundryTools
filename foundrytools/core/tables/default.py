from typing import Generic, TypeVar

from fontTools.ttLib import TTFont
from fontTools.ttLib.tables.DefaultTable import DefaultTable

from foundrytools.utils.bits_tools import update_bit

T = TypeVar("T", bound=DefaultTable)


class DefaultTbl(Generic[T]):
    """
    Manages font table data with functionality for detecting modifications and setting bits.

    This class allows you to interact with a specific table in a font's data to determine if the
    table has been modified and to set specific bits within the table's fields.
    """

    def __init__(self, ttfont: TTFont, table_tag: str):
        """
        Initializes the table.

        :param ttfont: The ``TTFont`` object.
        :type ttfont: TTFont
        :param table_tag: The table tag.
        :type table_tag: str
        """
        if table_tag not in ttfont:
            raise KeyError(f"Table {table_tag} not found in font")
        self._ttfont: TTFont = ttfont
        self._table: T = ttfont.get(table_tag)

    @property
    def ttfont(self) -> TTFont:
        """
        Returns the ``TTFont`` object to which the table belongs.

        :return: The TTFont object.
        :rtype: TTFont
        """
        return self._ttfont

    @property
    def table(self) -> T:
        """
        Thw wrapped table object.
        """
        return self._table

    @table.setter
    def table(self, value: T) -> None:
        """
        Wraps a new table object.
        """
        self._table = value

    @property
    def is_modified(self) -> bool:
        """
        Checks if the table has been modified.

        By default, we assume that when the table has been accessed, it has been modified.
        Subclasses should override this method to provide a more accurate check.

        :return: True
        :rtype: bool
        """
        return True

    def set_bit(self, field_name: str, pos: int, value: bool) -> None:
        """
        Sets a specific bit in a field of the table.

        :param field_name: The field name.
        :type field_name: str
        :param pos: The position of the bit to set.
        :type pos: int
        :param value: The value to set.
        :type value: bool
        """
        field_value = getattr(self._table, field_name)
        new_field_value = update_bit(field_value, pos, value)
        setattr(self._table, field_name, new_field_value)
