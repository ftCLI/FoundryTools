from fontTools.ttLib import TTFont
from fontTools.ttLib.tables.G_D_E_F_ import table_G_D_E_F_

from foundrytools.constants import T_GDEF
from foundrytools.tables.default import DefaultTbl


class GdefTable(DefaultTbl):  # pylint: disable=too-few-public-methods
    """This class extends the fontTools ``GDEF`` table."""

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
        Returns the ``GDEF`` table object.

        :return: The ``GDEF`` table object.
        :rtype: table_G_D_E_F_
        """
        return self._table

    @table.setter
    def table(self, value: table_G_D_E_F_) -> None:
        """
        Sets the ``GDEF`` table object.

        :param value: The ``GDEF`` table object.
        :type value: table_G_D_E_F_
        """
        self._table = value
