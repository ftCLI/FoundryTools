from fontTools.ttLib import TTFont
from fontTools.ttLib.tables.G_D_E_F_ import table_G_D_E_F_

from foundrytools.constants import T_GDEF
from foundrytools.core.tables.default import DefaultTbl


class GdefTable(DefaultTbl):  # pylint: disable=too-few-public-methods
    """This class is a wrapper for the ``GDEF`` table."""

    def __init__(self, ttfont: TTFont) -> None:
        """
        Initializes the ``GSUB`` table handler.

        :param ttfont: The ``TTFont`` object.
        :type ttfont: TTFont
        """
        super().__init__(ttfont=ttfont, table_tag=T_GDEF)

    @property
    def table(self) -> table_G_D_E_F_:
        """
        The wrapped ``table_G_D_E_F_`` table object.
        """
        return self._table

    @table.setter
    def table(self, value: table_G_D_E_F_) -> None:
        """
        Wraps a new ``table_G_D_E_F_`` object.
        """
        self._table = value
