from fontTools.pens.recordingPen import DecomposingRecordingPen
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.ttLib import TTFont
from fontTools.ttLib.tables._g_l_y_f import table__g_l_y_f

from foundrytools.constants import T_FPGM, T_GLYF
from foundrytools.core.tables.default import DefaultTbl
from foundrytools.lib.pathops import correct_glyf_contours


class GlyfTable(DefaultTbl):  # pylint: disable=too-few-public-methods
    """This class extends the fontTools ``glyf`` table."""

    def __init__(self, ttfont: TTFont) -> None:
        """
        Initializes the ``glyf`` table handler.

        :param ttfont: The ``TTFont`` object.
        :type ttfont: TTFont
        """
        super().__init__(ttfont=ttfont, table_tag=T_GLYF)

    @property
    def table(self) -> table__g_l_y_f:
        """
        Thw wrapped ``table__g_l_y_f`` table object.
        """
        return self._table

    @table.setter
    def table(self, value: table__g_l_y_f) -> None:
        """
        Wraps a new ``table__g_l_y_f`` object.
        """
        self._table = value

    def correct_contours(
        self, remove_hinting: bool = True, ignore_errors: bool = True, min_area: int = 25
    ) -> set[str]:
        """
        Corrects contours of the glyf table by removing overlaps, correcting the direction of the
        contours, and removing tiny paths.

        :param remove_hinting: Whether to remove hinting from the font if one or more glyphs are
            modified.
        :type remove_hinting: bool
        :param ignore_errors: Whether to ignore skia pathops errors while correcting contours.
        :type ignore_errors: bool
        :param min_area: The minimum area of a contour to be considered. Default is 25.
        :type min_area: int
        :return: A set of glyph names that were modified.
        :rtype: set[str]
        """
        return correct_glyf_contours(
            font=self.ttfont,
            remove_hinting=remove_hinting,
            ignore_errors=ignore_errors,
            min_area=min_area,
        )

    def decompose_glyph(self, glyph_name: str) -> None:
        """
        Decompose the components of a given glyph name.

        :param glyph_name: The name of the glyph to decompose.
        :type glyph_name: str
        """
        glyph_set = self.ttfont.getGlyphSet()
        dc_pen = DecomposingRecordingPen(glyph_set)
        glyph_set[glyph_name].draw(dc_pen)

        tt_pen = TTGlyphPen(None)
        dc_pen.replay(tt_pen)
        self.table[glyph_name] = tt_pen.glyph()

    def decompose_all(self) -> set[str]:
        """
        Decompose all composite glyphs.

        :return: A set of glyph names that were decomposed
        :rtype: set[str]
        """
        decomposed_glyphs = set()
        for glyph_name in self.ttfont.getGlyphOrder():
            glyph = self.table[glyph_name]
            if not glyph.isComposite():
                continue
            self.decompose_glyph(glyph_name)
            decomposed_glyphs.add(glyph_name)

        return decomposed_glyphs

    def decompose_transformed(self) -> set[str]:
        """Decompose composite glyphs that have transformed components."""
        decomposed_glyphs = set()
        for glyph_name in self.ttfont.getGlyphOrder():
            decompose = False
            glyph = self.table[glyph_name]
            if not glyph.isComposite():
                continue
            for component in glyph.components:
                _, transform = component.getComponentInfo()

                # Font is hinted, decompose glyphs with *any* transformations
                if T_FPGM in self.ttfont:
                    if transform[0:4] != (1, 0, 0, 1):
                        decompose = True
                # Font is unhinted, decompose only glyphs with transformations where only one
                # dimension is flipped while the other isn't. Otherwise, the outline direction
                # is intact and since the font is unhinted, no rendering problems are to be
                # expected
                else:
                    if transform[0] * transform[3] < 0:
                        decompose = True

            if decompose:
                self.decompose_glyph(glyph_name)
                decomposed_glyphs.add(glyph_name)

        return decomposed_glyphs

    def remove_duplicate_components(self) -> set[str]:
        """
        Remove duplicate components from composite glyphs.

        :return: A set of glyph names that were fixed.
        :rtype: set[str]
        """
        fixed_glyphs = set()
        for glyph_name in self.ttfont.getGlyphOrder():
            glyph = self.table[glyph_name]
            if not glyph.isComposite():
                continue

            components = []
            for component in glyph.components:
                if component not in components:
                    components.append(component)
                else:
                    fixed_glyphs.add(glyph_name)

            glyph.components = components
            self.table[glyph_name] = glyph

        return fixed_glyphs
