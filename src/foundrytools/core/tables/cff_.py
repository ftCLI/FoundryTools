import contextlib
from typing import Any

from fontTools.cffLib import PrivateDict, TopDict
from fontTools.pens.recordingPen import RecordingPen
from fontTools.pens.roundingPen import RoundingPen
from fontTools.pens.t2CharStringPen import T2CharStringPen
from fontTools.ttLib import TTFont
from fontTools.ttLib.tables.C_F_F_ import table_C_F_F_

from foundrytools.constants import T_CFF
from foundrytools.core.tables.default import DefaultTbl
from foundrytools.lib.pathops import correct_cff_contours

HINTING_ATTRS = (
    "BlueValues",
    "OtherBlues",
    "FamilyBlues",
    "FamilyOtherBlues",
    "BlueScale",
    "BlueShift",
    "BlueFuzz",
    "StemSnapH",
    "StemSnapV",
    "StdHW",
    "StdVW",
    "ForceBold",
    "LanguageGroup",
    "ExpansionFactor",
)


class CFFTable(DefaultTbl):
    """
    A class that wraps and manages the CFF table of a font, providing methods to manipulate
    hinting data, font names, and glyph contours.
    """

    def __init__(self, ttfont: TTFont) -> None:
        """
        Initializes the ``CFF`` table wrapper.

        :param ttfont: The ``TTFont`` object.
        :type ttfont: TTFont
        """
        super().__init__(ttfont=ttfont, table_tag=T_CFF)
        self._raw_dict_copy: dict = self.table.cff.topDictIndex[0].Private.rawDict.copy()

    @property
    def table(self) -> table_C_F_F_:
        """
        The wrapped ``table_C_F_F_`` object.
        """
        return self._table

    @table.setter
    def table(self, value: table_C_F_F_) -> None:
        """
        Wraps a new ``table_C_F_F_`` object.
        """
        self._table = value

    @property
    def top_dict(self) -> TopDict:
        """
        Returns the topDictIndex field of the ``CFF`` table.

        :return: The topDictIndex field of the ``CFF`` table.
        :rtype: TopDict
        """
        return self.table.cff.topDictIndex[0]

    @property
    def private_dict(self) -> PrivateDict:
        """
        Returns the private field of the ``CFF`` table.

        :return: The private field of the ``CFF`` table.
        :rtype: PrivateDict
        """
        return self.top_dict.Private

    def get_hinting_data(self) -> dict[str, Any]:
        """
        Returns the hinting data from the ``CFF`` table.

        :return: The hinting data.
        :rtype: dict[str, Any]
        """
        hinting_data = {}
        for attr in HINTING_ATTRS:
            if hasattr(self.private_dict, attr):
                hinting_data[attr] = getattr(self.private_dict, attr)
        return hinting_data

    def set_hinting_data(self, **kwargs: dict[str, Any]) -> None:
        """
        Sets the hinting data in the ``CFF`` table.

        :param kwargs: The hinting data to set.
        :type kwargs: dict[str, Any]
        """
        for attr, value in kwargs.items():
            setattr(self.private_dict, attr, value)

    def _restore_hinting_data(self) -> None:
        """Restore the original hinting data to the ``CFF`` table."""
        for attr in HINTING_ATTRS:
            setattr(self.private_dict, attr, self._raw_dict_copy.get(attr))

    def set_names(self, **kwargs: dict[str, str]) -> None:
        """
        Sets the ``cff.fontNames[0]`` and ``topDictIndex[0]`` values.

        :param kwargs: The values to set in the CFF table.
        :type kwargs: dict[str, str]
        """
        font_name = str(kwargs.get("fontNames"))
        if font_name:
            self._set_cff_font_names(font_name=font_name)
            del kwargs["fontNames"]

        top_dict_names: dict[str, str] = {k: str(v) for k, v in kwargs.items() if v is not None}
        if top_dict_names:
            self._set_top_dict_names(top_dict_names)

    def _set_cff_font_names(self, font_name: str) -> None:
        """
        Sets the ``cff.fontNames`` value.

        :param font_name: The font name to set.
        :type font_name: str
        """
        self.table.cff.fontNames = [font_name]

    def _set_top_dict_names(self, names: dict[str, str]) -> None:
        """
        Sets the names of the ``CFF`` table.

        :param names: The names to set.
        :type names: dict[str, str]
        """
        for attr_name, attr_value in names.items():
            setattr(self.top_dict, attr_name, attr_value)

    def del_names(self, **kwargs: dict[str, str]) -> None:
        """
        Deletes names from ``topDictIndex[0]`` using the provided keyword arguments.

        :param kwargs: The names to delete from the ``CFF`` table ``TopDict``.
        :type kwargs: dict[str, str]
        """
        for k, v in kwargs.items():
            if v is not None:
                with contextlib.suppress(KeyError):
                    del self.top_dict.rawDict[k]

    def find_replace(self, old_string: str, new_string: str) -> None:
        """
        Find and replace a string in the ``CFF`` table.

        :param old_string: The string to find.
        :type old_string: str
        :param new_string: The string to replace the old string with.
        :type new_string: str
        """
        self._find_replace_in_font_names(old_string=old_string, new_string=new_string)
        self._find_replace_in_top_dict(old_string=old_string, new_string=new_string)

    def _find_replace_in_font_names(self, old_string: str, new_string: str) -> None:
        cff_font_names = self.table.cff.fontNames[0]
        self.table.cff.fontNames = [
            cff_font_names.replace(old_string, new_string).replace("  ", " ").strip()
        ]

    def _find_replace_in_top_dict(self, old_string: str, new_string: str) -> None:
        top_dict = self.top_dict
        attr_list = [
            "version",
            "FullName",
            "FamilyName",
            "Weight",
            "Copyright",
            "Notice",
        ]

        for attr_name in attr_list:
            with contextlib.suppress(AttributeError):
                old_value = str(getattr(top_dict, attr_name))
                new_value = old_value.replace(old_string, new_string).replace("  ", " ").strip()
                setattr(top_dict, attr_name, new_value)

    def remove_hinting(self, drop_hinting_data: bool = False) -> None:
        """
        Removes hinting data from a PostScript font.

        :param drop_hinting_data: If True, the hinting data will be removed from the font.
        :type drop_hinting_data: bool
        """
        self.table.cff.remove_hints()
        if not drop_hinting_data:
            self._restore_hinting_data()

    def round_coordinates(self, drop_hinting_data: bool = False) -> set[str]:
        """
        Round the coordinates of the font's glyphs using the ``RoundingPen``.

        :return: A set of glyph names whose coordinates were rounded.
        :rtype: set[str]
        """
        glyph_names = self.ttfont.getGlyphOrder()
        glyph_set = self.ttfont.getGlyphSet()
        charstrings = self.table.cff.topDictIndex[0].CharStrings

        rounded_charstrings = set()
        for glyph_name in glyph_names:
            charstring = charstrings[glyph_name]

            # Record the original charstring and store the value
            rec_pen = RecordingPen()
            glyph_set[glyph_name].draw(rec_pen)
            value = rec_pen.value

            # https://github.com/fonttools/fonttools/commit/40b525c1e3cc20b4b64004b8e3224a67adc2adf1
            # The width argument of `T2CharStringPen()` is inserted directly into the CharString
            # program, so it must be relative to Private.nominalWidthX.
            glyph_width = glyph_set[glyph_name].width
            if glyph_width == charstring.private.defaultWidthX:
                width = None
            else:
                width = glyph_width - charstring.private.nominalWidthX

            # Round the charstring
            t2_pen = T2CharStringPen(width=width, glyphSet=glyph_set)
            rounding_pen = RoundingPen(outPen=t2_pen)
            glyph_set[glyph_name].draw(rounding_pen)
            rounded_charstring = t2_pen.getCharString(private=charstring.private)

            # Record the rounded charstring
            rec_pen_2 = RecordingPen()
            rounded_charstring.draw(rec_pen_2)
            value_2 = rec_pen_2.value

            # Update the charstring only if the rounded charstring is different
            if value != value_2:
                charstrings[glyph_name] = rounded_charstring
                rounded_charstrings.add(glyph_name)

        if not drop_hinting_data:
            self._restore_hinting_data()

        return rounded_charstrings

    def correct_contours(
        self,
        remove_hinting: bool = True,
        ignore_errors: bool = True,
        remove_unused_subroutines: bool = True,
        min_area: int = 25,
        drop_hinting_data: bool = False,
    ) -> set[str]:
        """
        Corrects contours of the CFF table by removing overlaps, correcting the direction of the
        contours, and removing tiny paths.

        :param remove_hinting: Whether to remove hinting from the font if one or more glyphs are
            modified.
        :type remove_hinting: bool
        :param ignore_errors: Whether to ignore skia pathops errors while correcting contours.
        :type ignore_errors: bool
        :param remove_unused_subroutines: Whether to remove unused subroutines from the font.
        :type remove_unused_subroutines: bool
        :param min_area: The minimum area of a contour to be considered. Default is 25.
        :type min_area: int
        :param drop_hinting_data: If True, the hinting data will be removed from the font.
        :type drop_hinting_data: bool
        :return: A set of glyph names that were modified.
        :rtype: set[str]
        """
        fixed_glyphs = correct_cff_contours(
            font=self.ttfont,
            remove_hinting=remove_hinting,
            ignore_errors=ignore_errors,
            remove_unused_subroutines=remove_unused_subroutines,
            min_area=min_area,
        )
        if not drop_hinting_data:
            self._restore_hinting_data()
        return fixed_glyphs
