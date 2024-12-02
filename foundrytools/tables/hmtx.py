from fontTools.ttLib import TTFont
from fontTools.ttLib.tables._h_m_t_x import table__h_m_t_x

from foundrytools.constants import T_HMTX
from foundrytools.tables.default import DefaultTbl


class HmtxTable(DefaultTbl):  # pylint: disable=too-few-public-methods
    """This class extends the fontTools ``hmtx`` table."""

    def __init__(self, ttfont: TTFont) -> None:
        """
        Initializes the ``hmtx`` table handler.

        :param ttfont: The ``TTFont`` object.
        :type ttfont: TTFont
        """
        super().__init__(ttfont=ttfont, table_tag=T_HMTX)

    @property
    def table(self) -> table__h_m_t_x:
        """
        Returns the ``hmtx`` table object.

        :return: The ``hmtx`` table object.
        :rtype: table__h_m_t_x
        """
        return self._table

    @table.setter
    def table(self, value: table__h_m_t_x) -> None:
        """
        Sets the ``hmtx`` table object.

        :param value: The ``hmtx`` table object.
        :type value: table__h_m_t_x
        """
        self._table = value

    def fix_non_breaking_space_width(self) -> bool:
        """
        Sets the width of the non-breaking space glyph to be the same as the space glyph.

        :raises ValueError: If the space or non-breaking space glyphs do not exist.
        """
        best_cmap = self.ttfont.getBestCmap()
        space_glyph = best_cmap.get(0x0020)
        nbsp_glyph = best_cmap.get(0x00A0)
        if nbsp_glyph is None or space_glyph is None:
            raise ValueError("Both the space and non-breaking space glyphs must exist.")

        # Set the width of the non-breaking space glyph
        if self.table.metrics[nbsp_glyph] != self.table.metrics[space_glyph]:
            self.table.metrics[nbsp_glyph] = self.table.metrics[space_glyph]
            return True

        return False
