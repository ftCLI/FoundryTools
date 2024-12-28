from fontTools.ttLib import TTFont
from fontTools.ttLib.tables._f_v_a_r import table__f_v_a_r

from foundrytools.constants import T_FVAR
from foundrytools.core.tables.default import DefaultTbl


class FvarTable(DefaultTbl):  # pylint: disable=too-few-public-methods
    """This class extends the fontTools ``fvar`` table."""

    def __init__(self, ttfont: TTFont) -> None:
        """
        Initializes the ``fvar`` table handler.

        :param ttfont: The ``TTFont`` object
        :type ttfont: TTFont
        """
        super().__init__(ttfont=ttfont, table_tag=T_FVAR)

    @property
    def table(self) -> table__f_v_a_r:
        """
        Thw wrapped ``table__f_v_a_r`` table object.
        """
        return self._table

    @table.setter
    def table(self, value: table__f_v_a_r) -> None:
        """
        Wraps a new ``table__f_v_a_r`` object.
        """
        self._table = value
