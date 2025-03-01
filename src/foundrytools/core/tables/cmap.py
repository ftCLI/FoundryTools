from copy import deepcopy

from fontTools.ttLib import TTFont
from fontTools.ttLib.tables._c_m_a_p import table__c_m_a_p

from foundrytools.constants import T_CMAP
from foundrytools.core.tables.default import DefaultTbl
from foundrytools.lib.unicode import (
    cmap_from_glyph_names,
    setup_character_map,
    update_character_map,
)


class CmapTable(DefaultTbl):  # pylint: disable=too-few-public-methods
    """This class extends the fontTools ``cmap`` table."""

    def __init__(self, ttfont: TTFont) -> None:
        """
        Initializes the ``cmap`` table handler.

        :param ttfont: The ``TTFont`` object.
        :type ttfont: TTFont
        """
        super().__init__(ttfont=ttfont, table_tag=T_CMAP)
        self._copy = deepcopy(self.table)

    @property
    def table(self) -> table__c_m_a_p:
        """
        The wrapped ``table__c_m_a_p`` table object.
        """
        return self._table

    @table.setter
    def table(self, value: table__c_m_a_p) -> None:
        """
        Wraps a new ``table__c_m_a_p`` object.
        """
        self._table = value

    @property
    def is_modified(self) -> bool:
        """
        Returns whether the ``cmap`` table has been modified.

        :return: Whether the ``cmap`` table has been modified.
        :rtype: bool
        """
        return self._copy.compile(self.ttfont) != self.table.compile(self.ttfont)

    def get_all_codepoints(self) -> set[int]:
        """
        Returns all the codepoints in the ``cmap`` table.

        :return: A set of codepoints
        :rtype: set[int]
        """
        codepoints = set()
        for table in self.table.tables:
            if table.isUnicode():
                codepoints.update(table.cmap.keys())
        return codepoints

    def get_unmapped_glyphs(self) -> list[str]:
        """
        Returns all the unmapped glyphs in the ``cmap`` table.

        :return: A set of glyph names
        :rtype: set[str]
        """
        glyph_order = self.ttfont.getGlyphOrder()
        reversed_cmap = self.table.buildReversed()
        unmapped_glyphs = []

        for glyf_name in glyph_order:
            if reversed_cmap.get(glyf_name) is None:
                unmapped_glyphs.append(glyf_name)

        return unmapped_glyphs

    def rebuild_character_map(
        self, remap_all: bool = False
    ) -> tuple[list[tuple[int, str]], list[tuple[int, str, str]]]:
        """
        Rebuild the character map of the font.

        :param remap_all: Whether to remap all glyphs. If ``False``, only the unmapped glyphs will
            be remapped.
        :type remap_all: bool
        :return: A tuple containing the remapped and duplicate glyphs.
        :rtype: tuple[list[tuple[int, str]], list[tuple[int, str, str]]]
        """

        glyph_order = self.ttfont.getGlyphOrder()
        unmapped = self.get_unmapped_glyphs()

        if not remap_all:
            target_cmap = self.table.getBestCmap()
            source_cmap = cmap_from_glyph_names(glyphs_list=unmapped)
        else:
            target_cmap = {}
            source_cmap = cmap_from_glyph_names(glyphs_list=glyph_order)

        updated_cmap, remapped, duplicates = update_character_map(
            source_cmap=source_cmap, target_cmap=target_cmap
        )
        setup_character_map(ttfont=self.ttfont, mapping=updated_cmap)

        return remapped, duplicates

    def add_missing_nbsp(self) -> None:
        """Fixes the missing non-breaking space glyph by double mapping the space glyph."""
        # Get the space glyph
        best_cmap = self.table.getBestCmap()
        space_glyph = best_cmap.get(0x0020)
        if space_glyph is None:
            return

        # Get the non-breaking space glyph
        nbsp_glyph = best_cmap.get(0x00A0)
        if nbsp_glyph is not None:
            return

        # Copy the space glyph to the non-breaking space glyph
        for table in self.table.tables:
            if table.isUnicode():
                table.cmap[0x00A0] = space_glyph
