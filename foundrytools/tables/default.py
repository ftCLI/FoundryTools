from copy import deepcopy
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

    :ivar ttfont: The TTFont object representing the font.
    :type ttfont: TTFont :ivar table: The table within the font corresponding to the specified table
        tag.
    :type table: Any :ivar _copy: A deep copy of the original table to check for modifications.
    :type _copy: Any
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
        self.ttfont: TTFont = ttfont
        self._table: T = ttfont.get(table_tag)
        self._copy: T = deepcopy(self._table)

    @property
    def table(self) -> T:
        """
        Returns the table object.

        :return: The table object.
        :rtype: Any
        """
        return self._table

    @table.setter
    def table(self, value: T) -> None:
        """
        Sets the table object.

        :param value: The table object.
        :type value: Any
        """
        self._table = value

    @property
    def is_modified(self) -> bool:
        """
        Returns the modified status of the table by comparing it with the original table.

        :return: ``True`` if the table is modified, ``False`` otherwise.
        :rtype: bool
        """
        return self._table.compile(self.ttfont) != self._copy.compile(self.ttfont)

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
