"""GDEF table."""

from __future__ import annotations

from typing import TYPE_CHECKING

from foundrytools.constants import T_GDEF
from foundrytools.core.tables.default import DefaultTbl

if TYPE_CHECKING:
    from fontTools.ttLib import TTFont
    from fontTools.ttLib.tables.G_D_E_F_ import table_G_D_E_F_


class GdefTable(DefaultTbl):
    """A wrapper for the ``GDEF`` table."""

    def __init__(self, ttfont: TTFont) -> None:
        """
        Initialize the ``GSUB`` table handler.

        :param ttfont: The ``TTFont`` object.
        :type ttfont: TTFont
        """
        super().__init__(ttfont=ttfont, table_tag=T_GDEF)

    @property
    def table(self) -> table_G_D_E_F_:
        """The wrapped ``table_G_D_E_F_`` table object."""
        return self._table

    @table.setter
    def table(self, value: table_G_D_E_F_) -> None:
        """Wrap a new ``table_G_D_E_F_`` object."""
        self._table = value
