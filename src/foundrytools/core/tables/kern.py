"""Kern table."""

from __future__ import annotations

from typing import TYPE_CHECKING

from foundrytools.constants import T_CMAP, T_KERN
from foundrytools.core.tables.default import DefaultTbl

if TYPE_CHECKING:
    from fontTools.ttLib import TTFont
    from fontTools.ttLib.tables._k_e_r_n import table__k_e_r_n


class KernTable(DefaultTbl):
    """Extend the fontTools ``kern`` table."""

    def __init__(self, ttfont: TTFont) -> None:
        """
        Initialize the ``kern`` table handler.

        :param ttfont: The ``TTFont`` object
        :type ttfont: TTFont
        """
        super().__init__(ttfont=ttfont, table_tag=T_KERN)

    @property
    def table(self) -> table__k_e_r_n:
        """The wrapped ``table__k_e_r_n`` table object."""
        return self._table

    @table.setter
    def table(self, value: table__k_e_r_n) -> None:
        """Wrap a new ``table__k_e_r_n`` object."""
        self._table = value

    def remove_unmapped_glyphs(self) -> bool:
        """Remove unmapped glyphs from the ``kern`` table."""
        if all(kernTable.format != 0 for kernTable in self.table.kernTables):
            return False

        character_glyphs = set()
        for table in self.ttfont[T_CMAP].tables:
            character_glyphs.update(table.cmap.values())

        modified = False

        for table in self.table.kernTables:
            if table.format == 0:
                pairs_to_delete = []
                for left_glyph, right_glyph in table.kernTable:
                    if left_glyph not in character_glyphs or right_glyph not in character_glyphs:
                        pairs_to_delete.append((left_glyph, right_glyph))
                if pairs_to_delete:
                    modified = True
                    for pair in pairs_to_delete:
                        del table.kernTable[pair]

        return modified
