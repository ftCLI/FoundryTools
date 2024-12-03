import contextlib
import math
from collections.abc import Generator
from io import BytesIO
from pathlib import Path
from types import TracebackType
from typing import Any, Literal, Optional, Union

import defcon
from extractor import extractUFO
from fontTools.misc.cliTools import makeOutputFileName
from fontTools.pens.statisticsPen import StatisticsPen
from fontTools.ttLib import TTFont
from fontTools.ttLib.scaleUpem import scale_upem
from fontTools.ttLib.tables._f_v_a_r import Axis, NamedInstance
from ufo2ft.postProcessor import PostProcessor

from foundrytools import constants as const
from foundrytools.core.tables import (
    TABLES_LOOKUP,
    CFFTable,
    CmapTable,
    GdefTable,
    GlyfTable,
    GsubTable,
    HeadTable,
    HheaTable,
    HmtxTable,
    KernTable,
    NameTable,
    OS2Table,
    PostTable,
)
from foundrytools.lib.otf_builder import build_otf
from foundrytools.lib.qu2cu import quadratics_to_cubics
from foundrytools.lib.ttf_builder import build_ttf
from foundrytools.lib.unicode import (
    _cmap_from_glyph_names,
    _prod_name_from_uni_str,
    _ReversedCmap,
    get_mapped_and_unmapped_glyphs,
    get_uni_str,
    setup_character_map,
    update_character_map,
)
from foundrytools.utils.path_tools import get_temp_file_path

__all__ = ["Font", "FontError"]


class FontError(Exception):
    """The ``FontError`` class is a custom exception class for font-related errors."""


class StyleFlags:
    """
    The ``Flags`` class is a helper class for working with font flags (e.g., bold, italic, oblique).

    :Example:

    .. code-block:: python

        from foundrytools import Font, Flags

        font = Font("path/to/font.ttf")
        flags = Flags(font)

        # Check if the font is bold
        if flags.is_bold:
            print("The font is bold.")

        # Set the font as italic
        flags.is_italic = True
    """

    def __init__(self, font: "Font"):
        """
        Initialize the ``Flags`` class.

        :param font: The ``Font`` object.
        :type font: Font
        """
        self._font = font

    def __repr__(self) -> str:
        return (
            f"<Flags is_bold={self.is_bold}, is_italic={self.is_italic}, "
            f"is_oblique={self.is_oblique}, is_regular={self.is_regular}>"
        )

    def __str__(self) -> str:
        return (
            f"Flags(is_bold={self.is_bold}, is_italic={self.is_italic}, "
            f"is_oblique={self.is_oblique}, is_regular={self.is_regular})"
        )

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, StyleFlags):
            return False
        return all(
            getattr(self, attr) == getattr(other, attr)
            for attr in ("is_bold", "is_italic", "is_oblique", "is_regular")
        )

    def __ne__(self, other: Any) -> bool:
        return not self.__eq__(other)

    @property
    def font(self) -> "Font":
        """
        Gets the font used in the instance.

        This property returns the Font object associated with the instance, which can be used to
        modify text displays.

        :return: Font object associated with the instance.
        :rtype: Font
        """
        return self._font

    @font.setter
    def font(self, value: "Font") -> None:
        """
        Sets the font property with a Font object.

        :param value: Font object to set the font property
        :type value: Font
        """
        self._font = value

    @contextlib.contextmanager
    def _update_font_properties(self) -> Generator:
        try:
            yield
        except Exception as e:
            raise FontError("An error occurred while updating font properties") from e

    def _set_font_style(
        self,
        bold: Optional[bool] = None,
        italic: Optional[bool] = None,
        regular: Optional[bool] = None,
    ) -> None:
        if bold is not None:
            self.font.os_2.fs_selection.bold = bold
            self.font.head.mac_style.bold = bold
        if italic is not None:
            self.font.os_2.fs_selection.italic = italic
            self.font.head.mac_style.italic = italic
        if regular is not None:
            self.font.os_2.fs_selection.regular = regular

    @property
    def is_bold(self) -> bool:
        """
        A property for getting and setting the bold bits of the font.

        The font is considered bold if bit 5 of the ``fsSelection`` field in the ``OS/2`` table is
        set to 1 and bit 0 of the ``macStyle`` field in the ``head`` table is set to 1.

        At the same time, bit 0 of the ``fsSelection`` field in the ``OS/2`` table is set to 0.

        :return: ``True`` if the font is bold, ``False`` otherwise.
        :rtype: bool
        """
        try:
            return self.font.os_2.fs_selection.bold and self.font.head.mac_style.bold
        except Exception as e:
            raise FontError("An error occurred while checking if the font is bold") from e

    @is_bold.setter
    def is_bold(self, value: bool) -> None:
        with self._update_font_properties():
            self._set_font_style(bold=value, regular=not value if not self.is_italic else False)

    @property
    def is_italic(self) -> bool:
        """
        A property for getting and setting the italic bits of the font.

        The font is considered italic when bit 0 of the ``fsSelection`` field in the ``OS/2`` table
        is set to 1 and bit 0 of the ``macStyle`` field in the ``head`` table is set to 1.

        At the same time, bit 0 of the ``fsSelection`` field in the ``OS/2`` table is set to 0.

        :return: ``True`` if the font is italic, ``False`` otherwise.
        :rtype: bool
        """
        try:
            return self.font.os_2.fs_selection.italic and self.font.head.mac_style.italic
        except Exception as e:
            raise FontError("An error occurred while checking if the font is italic") from e

    @is_italic.setter
    def is_italic(self, value: bool) -> None:
        with self._update_font_properties():
            self._set_font_style(italic=value, regular=not value if not self.is_bold else False)

    @property
    def is_oblique(self) -> bool:
        """
        A property for getting and setting the oblique bit of the font.

        :return: ``True`` if the font is oblique, ``False`` otherwise.
        :rtype: bool
        """
        try:
            return self.font.os_2.fs_selection.oblique
        except Exception as e:
            raise FontError("An error occurred while checking if the font is oblique") from e

    @is_oblique.setter
    def is_oblique(self, value: bool) -> None:
        """Set the oblique bit in the OS/2 table."""
        try:
            self.font.os_2.fs_selection.oblique = value
        except Exception as e:
            raise FontError("An error occurred while setting the oblique bit") from e

    @property
    def is_regular(self) -> bool:
        """
        A property for getting and setting the regular bit of the font.

        :return: ``True`` if the font is regular, ``False`` otherwise.
        :rtype: bool
        """
        try:
            return self.font.os_2.fs_selection.regular
        except Exception as e:
            raise FontError("An error occurred while checking if the font is regular") from e

    @is_regular.setter
    def is_regular(self, value: bool) -> None:
        """Set the regular bit in the OS/2 table."""
        with self._update_font_properties():
            if value:
                self._set_font_style(regular=True, bold=False, italic=False)
            else:
                # Prevent setting the regular bit if the font is bold or italic
                self.font.os_2.fs_selection.regular = not (self.is_bold or self.is_italic)


class Font:  # pylint: disable=too-many-public-methods, too-many-instance-attributes
    """
    The ``Font`` class is a wrapper around the ``TTFont`` class from ``fontTools``.

    It provides a high-level interface for working with the underlying TTFont object and its
    tables.

    :Example:

    .. code-block:: python

        from foundrytools import Font

        font = Font("path/to/font.ttf")

        # Check if the font is italic
        if font.is_italic:
            print("The font is italic.")

        # Set the font as bold
        font.is_bold = True

        # Save the font
        font.save("path/to/output.ttf")
    """

    def __init__(
        self,
        font_source: Union[str, Path, BytesIO, TTFont],
        lazy: Optional[bool] = None,
        recalc_bboxes: bool = True,
        recalc_timestamp: bool = False,
    ) -> None:
        """
        Initialize a ``Font`` object.

        :param font_source: A path to a font file (``str`` or ``Path`` object), a ``BytesIO`` object
            or a ``TTFont`` object.
        :type font_source: Union[str, Path, BytesIO, TTFont]
        :param lazy: If ``True``, many data structures are loaded lazily, upon access only. If
            ``False``, many data structures are loaded immediately. The default is ``None``
            which is somewhere in between.
        :type lazy: Optional[bool]
        :param recalc_bboxes: If ``True`` (the default), recalculates ``glyf``, ``CFF``, ``head``
            bounding box values and ``hhea``/``vhea`` min/max values on save. Also compiles the
            glyphs on importing, which saves memory consumption and time.
        :type recalc_bboxes: bool
        :param recalc_timestamp: If ``True``, set the ``modified`` timestamp in the ``head`` table
            on save. Defaults to ``False``.
        :type recalc_timestamp: bool
        """

        self._file: Optional[Path] = None
        self._bytesio: Optional[BytesIO] = None
        self._ttfont: Optional[TTFont] = None
        self._temp_file: Path = get_temp_file_path()
        self._init_font(font_source, lazy, recalc_bboxes, recalc_timestamp)
        self._init_tables()  # Ensure tables are initialized before flags
        self.flags = StyleFlags(self)

    def _init_font(
        self,
        font_source: Union[str, Path, BytesIO, TTFont],
        lazy: Optional[bool],
        recalc_bboxes: bool,
        recalc_timestamp: bool,
    ) -> None:
        if isinstance(font_source, (str, Path)):
            self._init_from_file(font_source, lazy, recalc_bboxes, recalc_timestamp)
        elif isinstance(font_source, BytesIO):
            self._init_from_bytesio(font_source, lazy, recalc_bboxes, recalc_timestamp)
        elif isinstance(font_source, TTFont):
            self._init_from_ttfont(font_source, lazy, recalc_bboxes, recalc_timestamp)
        else:
            raise ValueError(
                f"Invalid source type {type(font_source)}. Expected str, Path, BytesIO, or TTFont."
            )

    def _init_from_file(
        self,
        path: Union[str, Path],
        lazy: Optional[bool],
        recalc_bboxes: bool,
        recalc_timestamp: bool,
    ) -> None:
        self._file = Path(path).resolve()
        self._ttfont = TTFont(
            path, lazy=lazy, recalcBBoxes=recalc_bboxes, recalcTimestamp=recalc_timestamp
        )

    def _init_from_bytesio(
        self, bytesio: BytesIO, lazy: Optional[bool], recalc_bboxes: bool, recalc_timestamp: bool
    ) -> None:
        self._bytesio = bytesio
        self._ttfont = TTFont(
            bytesio, lazy=lazy, recalcBBoxes=recalc_bboxes, recalcTimestamp=recalc_timestamp
        )
        bytesio.close()

    def _init_from_ttfont(
        self, ttfont: TTFont, lazy: Optional[bool], recalc_bboxes: bool, recalc_timestamp: bool
    ) -> None:
        self._bytesio = BytesIO()
        ttfont.save(self._bytesio, reorderTables=False)
        self._bytesio.seek(0)
        self._ttfont = TTFont(
            self._bytesio, lazy=lazy, recalcBBoxes=recalc_bboxes, recalcTimestamp=recalc_timestamp
        )

    def _init_tables(self) -> None:
        self._cff: Optional[CFFTable] = None
        self._cmap: Optional[CmapTable] = None
        self._gdef: Optional[GdefTable] = None
        self._glyf: Optional[GlyfTable] = None
        self._gsub: Optional[GsubTable] = None
        self._head: Optional[HeadTable] = None
        self._hhea: Optional[HheaTable] = None
        self._hmtx: Optional[HmtxTable] = None
        self._kern: Optional[KernTable] = None
        self._name: Optional[NameTable] = None
        self._os_2: Optional[OS2Table] = None
        self._post: Optional[PostTable] = None

    def __enter__(self) -> "Font":
        return self

    def __exit__(
        self,
        exc_type: Optional[type],
        exc_value: Optional[BaseException],
        traceback: Optional[TracebackType],
    ) -> None:
        self.close()

    def __repr__(self) -> str:
        return f"<Font file={self.file}, bytesio={self.bytesio}, ttfont={self.ttfont}>"

    def _load_table(self, table_tag: str):  # type: ignore
        """
        Load a table from the font.

        :param table_tag: The table tag.
        :type table_tag: str
        :return: The table object.
        :rtype: Table
        """
        if self.ttfont.get(table_tag) is None:
            raise KeyError(f"The '{table_tag}' table is not present in the font")

        table_attr, table_cls = TABLES_LOOKUP[table_tag]
        if getattr(self, table_attr) is None:
            setattr(self, table_attr, table_cls(self.ttfont))

    def _get_table(self, table_tag: str):  # type: ignore
        table_attr, _ = TABLES_LOOKUP[table_tag]
        if getattr(self, table_attr) is None:
            self._load_table(table_tag)
        table = getattr(self, table_attr)
        if table is None:
            raise KeyError(f"The '{table_tag}' table is not present in the font")
        return table

    @property
    def file(self) -> Optional[Path]:
        """
        A property with both getter and setter methods for the file path of the font. If the font
        was loaded from a file, this property will return the file path. If the font was loaded from
        a ``BytesIO`` object or a ``TTFont`` object, this property will return ``None``.

        :return: The file path of the font, if any.
        :rtype: Optional[Path]
        """
        return self._file

    @file.setter
    def file(self, value: Path) -> None:
        """
        Set the file path of the font.

        :param value: The file path of the font.
        :type value: Path
        """
        self._file = value

    @property
    def bytesio(self) -> Optional[BytesIO]:
        """
        A property with both getter and setter methods for the ``BytesIO`` object of the font. If
        the font was loaded from a ``BytesIO`` object, this property will return the ``BytesIO``
        object. If the font was loaded from a file or a ``TTFont`` object, this property will return
        ``None``.

        :return: The ``BytesIO`` object of the font, if any.
        :rtype: Optional[BytesIO]
        """
        return self._bytesio

    @bytesio.setter
    def bytesio(self, value: BytesIO) -> None:
        """
        Set the ``BytesIO`` object of the font.

        :param value: The ``BytesIO`` object of the font.
        :type value: BytesIO
        """
        self._bytesio = value

    @property
    def ttfont(self) -> TTFont:
        """
        A property with both getter and setter methods for the underlying ``TTFont`` object of the
        font.

        :return: The ``TTFont`` object of the font.
        :rtype: TTFont
        """
        return self._ttfont

    @ttfont.setter
    def ttfont(self, value: TTFont) -> None:
        """
        Set the underlying ``TTFont`` object of the font.

        Args:
            value: The ``TTFont`` object of the font.
        """
        self._ttfont = value

    @property
    def temp_file(self) -> Path:
        """
        A placeholder for the temporary file path of the font, in is needed for some operations.

        :return: The temporary file path of the font.
        :rtype: Path
        """
        return self._temp_file

    @property
    def cff(self) -> CFFTable:
        """
        The ``CFF `` table handler.

        :return: The loaded ``CFFTable``.
        :rtype: CFFTable
        """
        return self._get_table(const.T_CFF)

    @property
    def cmap(self) -> CmapTable:
        """
        The ``cmap`` table handler.

        :return: The loaded ``CmapTable``.
        :rtype: CmapTable
        """
        return self._get_table(const.T_CMAP)

    @property
    def gdef(self) -> GdefTable:
        """
        The ``GDEF`` table handler.

        :return: The loaded ``GdefTable``.
        :rtype: GdefTable
        """
        return self._get_table(const.T_GDEF)

    @property
    def glyf(self) -> GlyfTable:
        """
        The ``glyf`` table handler.

        :return: The loaded ``GlyfTable``.
        :rtype: GlyfTable
        """
        return self._get_table(const.T_GLYF)

    @property
    def gsub(self) -> GsubTable:
        """
        The ``GSUB`` table handler.

        :return: The loaded ``GsubTable``.
        :rtype: GsubTable
        """
        return self._get_table(const.T_GSUB)

    @property
    def head(self) -> HeadTable:
        """
        The ``head`` table handler.

        :return: The loaded ``HeadTable``.
        :rtype: HeadTable
        """
        return self._get_table(const.T_HEAD)

    @property
    def hhea(self) -> HheaTable:
        """
        The ``hhea`` table handler.

        :return: The loaded ``HheaTable``.
        :rtype: HheaTable
        """
        return self._get_table(const.T_HHEA)

    @property
    def hmtx(self) -> HmtxTable:
        """
        The ``hmtx`` table handler.

        :return: The loaded ``HmtxTable``.
        :rtype: HmtxTable
        """
        return self._get_table(const.T_HMTX)

    @property
    def kern(self) -> KernTable:
        """
        The ``kern`` table handler.

        :return: The loaded ``KernTable``.
        :rtype: KernTable
        """
        return self._get_table(const.T_KERN)

    @property
    def name(self) -> NameTable:
        """
        The ``name`` table handler.

        :return: The loaded ``NameTable``.
        :rtype: NameTable
        """
        return self._get_table(const.T_NAME)

    @property
    def os_2(self) -> OS2Table:
        """
        The ``OS/2`` table handler.

        :return: The loaded ``OS2Table``.
        :rtype: OS2Table
        """
        return self._get_table(const.T_OS_2)

    @property
    def post(self) -> PostTable:
        """
        The ``post`` table handler.

        :return: The loaded ``PostTable``.
        :rtype: PostTable
        """
        return self._get_table(const.T_POST)

    @property
    def is_ps(self) -> bool:
        """
        A read-only property for checking if the font has PostScript outlines. The font has
        PostScript outlines if the ``sfntVersion`` attribute of the ``TTFont`` object is equal to
        ``OTTO``.

        :return: ``True`` if the font sfntVersion is ``OTTO``, ``False`` otherwise.
        :rtype: bool
        """
        return self.ttfont.sfntVersion == const.PS_SFNT_VERSION

    @property
    def is_tt(self) -> bool:
        """
        A read-only property for checking if the font has TrueType outlines. The font has TrueType
        outlines if the ``sfntVersion`` attribute of the ``TTFont`` object is equal to ``\0\1\0\0``.

        :return: ``True`` if the font sfntVersion is ``\0\1\0\0``, ``False`` otherwise.
        :rtype: bool
        """
        return self.ttfont.sfntVersion == const.TT_SFNT_VERSION

    @property
    def is_woff(self) -> bool:
        """
        A read-only property for checking if the font is a WOFF font. The font is a WOFF font if the
        ``flavor`` attribute of the ``TTFont`` object is equal to ``woff``.

        :return: ``True`` if the font flavor is ``woff``, ``False`` otherwise.
        :rtype: bool
        """
        return self.ttfont.flavor == const.WOFF_FLAVOR

    @property
    def is_woff2(self) -> bool:
        """
        A read-only property for checking if the font is a WOFF2 font. The font is a WOFF2 font if
        the ``flavor`` attribute of the ``TTFont`` object is equal to ``woff2``.

        :return: ``True`` if the font flavor is ``woff2``, ``False`` otherwise.
        :rtype: bool
        """
        return self.ttfont.flavor == const.WOFF2_FLAVOR

    @property
    def is_sfnt(self) -> bool:
        """
        A read-only property for checking if the font is an SFNT font. The font is an SFNT font if
        the ``flavor`` attribute of the ``TTFont`` object is ``None``.

        :return: ``True`` if the font flavor is ``None``, ``False`` otherwise.
        :rtype: bool
        """
        return self.ttfont.flavor is None

    @property
    def is_static(self) -> bool:
        """
        A read-only property for checking if the font is a static font. The font is a static font if
        the ``TTFont`` object does not have a ``fvar`` table.

        :return: ``True`` if the font does not have a ``fvar`` table, ``False`` otherwise.
        :rtype: bool
        """
        return self.ttfont.get(const.T_FVAR) is None

    @property
    def is_variable(self) -> bool:
        """
        A read-only property for checking if the font is a variable font. The font is a variable
        font if the ``TTFont`` object has a ``fvar`` table.

        :return: ``True`` if the font has a ``fvar`` table, ``False`` otherwise.
        :rtype: bool
        """
        return self.ttfont.get(const.T_FVAR) is not None

    def save(
        self,
        file: Union[str, Path, BytesIO],
        reorder_tables: Optional[bool] = True,
    ) -> None:
        """
        Save the font to a file.

        :param file: The file path or ``BytesIO`` object to save the font to.
        :type file: Union[str, Path, BytesIO]
        :param reorder_tables: If ``True`` (the default), reorder the tables, sorting them by tag
            (recommended by the OpenType specification). If ``False``, retain the original order.
            If ``None``, reorder by table dependency (fastest).
        :type reorder_tables: Optional[bool]
        """
        self.ttfont.save(file, reorderTables=reorder_tables)

    def close(self) -> None:
        """Close the font and delete the temporary file."""
        self.ttfont.close()
        self._temp_file.unlink(missing_ok=True)
        if self.bytesio:
            self.bytesio.close()

    def reload(self) -> None:
        """Reload the font by saving it to a temporary stream and then loading it back."""
        recalc_bboxes = self.ttfont.recalcBBoxes
        recalc_timestamp = self.ttfont.recalcTimestamp
        buf = BytesIO()
        self.ttfont.save(buf)
        buf.seek(0)
        self.ttfont = TTFont(buf, recalcBBoxes=recalc_bboxes, recalcTimestamp=recalc_timestamp)
        self._init_tables()
        self.flags = StyleFlags(self)
        buf.close()

    def get_file_ext(self) -> str:
        """
        Get the real extension of the font (e.g., ``.otf``, ``.ttf``, ``.woff``, ``.woff2``).

        :return: The real extension of the font.
        :rtype: str
        """

        # Order of if statements is important.
        # WOFF and WOFF2 must be checked before OTF and TTF.
        if self.is_woff:
            return const.WOFF_EXTENSION
        if self.is_woff2:
            return const.WOFF2_EXTENSION
        if self.is_ps:
            return const.OTF_EXTENSION
        if self.is_tt:
            return const.TTF_EXTENSION
        raise ValueError("Unknown font type.")

    def get_file_path(
        self,
        file: Optional[Path] = None,
        output_dir: Optional[Path] = None,
        overwrite: bool = True,
        extension: Optional[str] = None,
        suffix: str = "",
    ) -> Path:
        """
        Get the output file for a ``Font`` object. If ``output_dir`` is not specified, the output
        file will be saved in the same directory as the input file. It the output file exists and
        ``overwrite`` is ``False``, file name will be incremented by adding a number preceded by '#'
        before the extension until a non-existing file name is found. If ``suffix`` is specified, it
        will be appended to the file name. If the suffix is already present, it will be removed
        before adding it again.

        :param file: The file name to use for the output file.
        :type file: Optional[Path]
        :param output_dir: The output directory.
        :type output_dir: Optional[Path]
        :param overwrite: If ``True``, overwrite the output file if it exists. If ``False``,
            increment the file name until a non-existing file name is found.
        :type overwrite: bool
        :param extension: The extension of the output file. If not specified, the extension of the
            input file will be used.
        :type extension: Optional[str]
        :param suffix: The suffix to add to the file name.
        :type suffix: str
        :return: The output file.
        :rtype: Path
        """

        if file is None and self.file is None:
            raise ValueError(
                "Cannot get output file for a BytesIO object without providing a file name."
            )

        file = file or self.file
        if not isinstance(file, Path):
            raise ValueError("File must be a Path object.")

        out_dir = output_dir or file.parent
        extension = extension or self.get_file_ext()
        file_name = file.stem + extension

        # Clean up the file name by removing the extensions used as file name suffix as added by
        # possible previous conversions. This is necessary to avoid adding the suffix multiple
        # times, like in the case of a file name like 'font.woff2.ttf.woff2'. It may happen when
        # converting a WOFF2 font to TTF and then to WOFF2 again.
        if suffix != "":
            for ext in [
                const.OTF_EXTENSION,
                const.TTF_EXTENSION,
                const.WOFF2_EXTENSION,
                const.WOFF_EXTENSION,
            ]:
                file_name = file_name.replace(ext, "")

        out_file = Path(
            makeOutputFileName(
                input=file_name,
                outputDir=out_dir,
                extension=extension,
                overWrite=overwrite,
                suffix=suffix,
            )
        )
        return out_file

    def get_axes(self) -> Optional[list[Axis]]:
        """
        Get axes from a variable font.

        :return: A list of ``Axis`` objects.
        """
        if not self.is_variable:
            return None

        # Filter out the 'hidden' axes (flags != 0)
        return [axis for axis in self.ttfont[const.T_FVAR].axes if axis.flags == 0]

    def get_instances(self) -> Optional[list[NamedInstance]]:
        """
        Get named instances from a variable font.

        :return: A list of ``NamedInstance`` objects.
        :rtype: list[NamedInstance]
        """
        if not self.is_variable:
            return None

        return self.ttfont[const.T_FVAR].instances

    def to_woff(self) -> None:
        """Convert a font to WOFF."""
        if self.is_woff:
            raise NotImplementedError("Font is already a WOFF font.")

        self.ttfont.flavor = const.WOFF_FLAVOR

    def to_woff2(self) -> None:
        """Convert a font to WOFF2."""
        if self.is_woff2:
            raise NotImplementedError("Font is already a WOFF2 font.")

        self.ttfont.flavor = const.WOFF2_FLAVOR

    def to_ttf(self, max_err: float = 1.0, reverse_direction: bool = True) -> None:
        """
        Converts a PostScript font to TrueType.

        :param max_err: The maximum error allowed when converting the font to TrueType. Defaults to
            1.0.
        :type max_err: float
        :param reverse_direction: If ``True``, reverse the direction of the contours. Defaults to
            ``True``.
        :type reverse_direction: bool
        """
        if self.is_tt:
            raise NotImplementedError("Font is already a TrueType font.")
        if self.is_variable:
            raise NotImplementedError("Conversion to TrueType is not supported for variable fonts.")

        try:
            build_ttf(font=self.ttfont, max_err=max_err, reverse_direction=reverse_direction)
        except Exception as e:
            raise FontError(e) from e

    def to_otf(self, tolerance: float = 1.0, correct_contours: bool = True) -> None:
        """Converts a TrueType font to PostScript."""
        if self.is_ps:
            raise NotImplementedError("Font is already a PostScript font.")
        if self.is_variable:
            raise NotImplementedError(
                "Conversion to PostScript is not supported for variable fonts."
            )
        try:
            self.glyf.decompose_all()

            charstrings = quadratics_to_cubics(
                font=self.ttfont, tolerance=tolerance, correct_contours=correct_contours
            )
            build_otf(font=self.ttfont, charstrings_dict=charstrings)

            self.os_2.recalc_avg_char_width()
        except Exception as e:
            raise FontError(e) from e

    def to_sfnt(self) -> None:
        """Convert a font to SFNT."""
        if self.is_sfnt:
            raise NotImplementedError("Font is already a SFNT font.")
        self.ttfont.flavor = None

    def scale_upm(self, target_upm: int) -> None:
        """
        Scale the font to the specified Units Per Em (UPM) value.

        :param target_upm: The target UPM value. Must be in the range 16 to 16384.
        :type target_upm: int
        """

        if target_upm < const.MIN_UPM or target_upm > const.MAX_UPM:
            raise ValueError(
                f"units_per_em must be in the range {const.MAX_UPM} to {const.MAX_UPM}."
            )

        if self.head.units_per_em == target_upm:
            return

        try:
            scale_upem(self.ttfont, new_upem=target_upm)
        except Exception as e:
            raise FontError(e) from e

    def correct_contours(
        self,
        remove_hinting: bool = True,
        ignore_errors: bool = True,
        remove_unused_subroutines: bool = True,
        min_area: int = 25,
    ) -> set[str]:
        """
        Correct the contours of a font by removing overlaps and tiny paths and correcting the
        direction of contours.

        This tool is an implementation of the ``removeOverlaps`` function in the ``fontTools``
        library to add support for correcting contours windings and removing tiny paths.

        If one or more contours are modified, the glyf or CFF table will be rebuilt.
        If no contours are modified, the font will remain unchanged and the method will return an
        empty list.

        The minimum area default value, 25, is the same as ``afdko.checkoutlinesufo``. All subpaths
        with a bounding box less than this area will be deleted. To prevent the deletion of small
        subpaths, set this value to 0.

        :param remove_hinting: If ``True``, remove hinting instructions from the font if one or more
            contours are modified. Defaults to ``True``.
        :type remove_hinting: bool
        :param ignore_errors: If ``True``, ignore skia pathops errors during the correction process.
            Defaults to ``True``.
        :type ignore_errors: bool
        :param remove_unused_subroutines: If ``True``, remove unused subroutines from the font.
            Defaults to ``True``.
        :type remove_unused_subroutines: bool
        :param min_area: The minimum area expressed in square units. Subpaths with a bounding box
            less than this area will be deleted. Defaults to 25.
        :type min_area: int
        :return: A set of glyph names that have been modified.
        :rtype: set[str]
        """
        if self.is_variable:
            raise NotImplementedError("Contour correction is not supported for variable fonts.")

        try:
            if self.is_ps:
                return self.cff.correct_contours(
                    remove_hinting=remove_hinting,
                    ignore_errors=ignore_errors,
                    remove_unused_subroutines=remove_unused_subroutines,
                    min_area=min_area,
                )
            if self.is_tt:
                return self.glyf.correct_contours(
                    remove_hinting=remove_hinting,
                    ignore_errors=ignore_errors,
                    min_area=min_area,
                )
            raise FontError("Unknown font type.")
        except Exception as e:
            raise FontError(e) from e

    def calc_italic_angle(self, min_slant: float = 2.0) -> float:
        """
        Calculates the italic angle of a font by measuring the slant of the glyph 'H' or 'uni0048'.

        :param min_slant: The minimum slant value to consider the font italic. Defaults to 2.0.
        :type min_slant: float
        :return: The italic angle of the font.
        :rtype: float
        :raises FontError: If the font does not contain the glyph 'H' or 'uni0048' or if an error
            occurs while calculating the italic angle.
        """

        try:
            glyph_set = self.ttfont.getGlyphSet()
            pen = StatisticsPen(glyphset=glyph_set)
            for g in ("H", "uni0048"):
                with contextlib.suppress(KeyError):
                    glyph_set[g].draw(pen)
                    italic_angle = -1 * math.degrees(math.atan(pen.slant))
                    if abs(italic_angle) >= abs(min_slant):
                        return italic_angle
                    return 0.0
            raise FontError("The font does not contain the glyph 'H' or 'uni0048'.")
        except Exception as e:
            raise FontError(e) from e

    def rebuild_cmap(self, remap_all: bool = False) -> list[tuple[int, str]]:
        """
        Rebuild the character map of a font.

        :param remap_all: If ``True``, remap all glyphs in the font. Defaults to ``False``.
        """

        try:
            glyph_order = self.ttfont.getGlyphOrder()
            _, unmapped = get_mapped_and_unmapped_glyphs(ttfont=self.ttfont)
            if not remap_all:
                target_cmap = self.ttfont.getBestCmap()  # We can also use cmap_from_reversed_cmap
                source_cmap = _cmap_from_glyph_names(glyphs_list=unmapped)
            else:
                target_cmap = {}
                source_cmap = _cmap_from_glyph_names(glyphs_list=glyph_order)

            updated_cmap, remapped, _ = update_character_map(
                source_cmap=source_cmap, target_cmap=target_cmap
            )
            setup_character_map(ttfont=self.ttfont, mapping=updated_cmap)
            return remapped
        except Exception as e:
            raise FontError(e) from e

    def rename_glyph(self, old_name: str, new_name: str) -> bool:
        """
        Rename a single glyph in the font.

        :param old_name: The old glyph name.
        :type old_name: str
        :param new_name: The new glyph name.
        :type new_name: str
        :return: ``True`` if the glyph was renamed, ``False`` otherwise.
        :rtype: bool
        """
        try:
            old_glyph_order = self.ttfont.getGlyphOrder()
            new_glyph_order = []

            if old_name not in old_glyph_order:
                raise ValueError(f"Glyph '{old_name}' not found in the font.")

            if new_name in old_glyph_order:
                raise ValueError(f"Glyph '{new_name}' already exists in the font.")

            for glyph_name in old_glyph_order:
                if glyph_name == old_name:
                    new_glyph_order.append(new_name)
                else:
                    new_glyph_order.append(glyph_name)

            rename_map = dict(zip(old_glyph_order, new_glyph_order))
            PostProcessor.rename_glyphs(otf=self.ttfont, rename_map=rename_map)
            self.rebuild_cmap(remap_all=True)

            return new_glyph_order != old_glyph_order
        except Exception as e:
            raise FontError(e) from e

    def rename_glyphs(self, new_glyph_order: list[str]) -> bool:
        """
        Rename the glyphs in the font based on the new glyph order.

        :param new_glyph_order: The new glyph order.
        :type new_glyph_order: List[str]
        :return: ``True`` if the glyphs were renamed, ``False`` otherwise.
        :rtype: bool
        """
        try:
            old_glyph_order = self.ttfont.getGlyphOrder()
            if new_glyph_order == old_glyph_order:
                return False
            rename_map = dict(zip(old_glyph_order, new_glyph_order))
            PostProcessor.rename_glyphs(otf=self.ttfont, rename_map=rename_map)
            self.rebuild_cmap(remap_all=True)
            return True
        except Exception as e:
            raise FontError(e) from e

    def set_production_names(self) -> list[tuple[str, str]]:
        """
        Set the production names for the glyphs in the font.

        The method iterates through each glyph in the old glyph order and determines its production
        name based on its assigned or calculated Unicode value. If the production name is already
        assigned, the glyph is skipped. If the production name is different from the original glyph
        name and is not yet assigned, the glyph is renamed and added to the new glyph order list.
        Finally, the font is updated with the new glyph order, the cmap table is rebuilt, and the
        list of renamed glyphs is returned.

        :return: A list of tuples containing the old and new glyph names.
        :rtype: List[Tuple[str, str]]
        """

        try:
            old_glyph_order: list[str] = self.ttfont.getGlyphOrder()
            reversed_cmap: _ReversedCmap = self.ttfont[const.T_CMAP].buildReversed()
            new_glyph_order: list[str] = []
            renamed_glyphs: list[tuple[str, str]] = []

            for glyph_name in old_glyph_order:
                uni_str = get_uni_str(glyph_name, reversed_cmap)
                # If still no uni_str, the glyph name is unmodified.
                if not uni_str:
                    new_glyph_order.append(glyph_name)
                    continue

                # In case the production name could not be found, the glyph is already named with
                # the production name, or the production name is already assigned, we skip the
                # renaming process.
                production_name = _prod_name_from_uni_str(uni_str)
                if (
                    not production_name
                    or production_name == glyph_name
                    or production_name in old_glyph_order
                ):
                    new_glyph_order.append(glyph_name)
                    continue

                new_glyph_order.append(production_name)
                renamed_glyphs.append((glyph_name, production_name))

            if not renamed_glyphs:
                return []

            rename_map = dict(zip(old_glyph_order, new_glyph_order))
            PostProcessor.rename_glyphs(otf=self.ttfont, rename_map=rename_map)
            self.rebuild_cmap(remap_all=True)
            return renamed_glyphs
        except Exception as e:
            raise FontError(e) from e

    def sort_glyphs(
        self,
        sort_by: Literal["unicode", "alphabetical", "cannedDesign"] = "unicode",
    ) -> bool:
        """
        Reorder the glyphs based on the Unicode values, alphabetical order, or canned design order.

        :param sort_by: The sorting method. Can be one of the following values: 'unicode',
            'alphabetical', or 'cannedDesign'. Defaults to 'unicode'.
        :type sort_by: Literal['unicode', 'alphabetical', 'cannedDesign']
        :return: ``True`` if the glyphs were reordered, ``False`` otherwise.
        :rtype: bool
        """
        try:
            ufo = defcon.Font()
            extractUFO(self.file, destination=ufo, doFeatures=False, doInfo=False, doKerning=False)
            old_glyph_order = self.ttfont.getGlyphOrder()
            new_glyph_order = ufo.unicodeData.sortGlyphNames(
                glyphNames=old_glyph_order,
                sortDescriptors=[{"type": sort_by}],
            )

            # Ensure that the '.notdef' glyph is always the first glyph in the font as required by
            # the OpenType specification. If the '.notdef' glyph is not the first glyph, compiling
            # the CFF table will fail.
            # https://learn.microsoft.com/en-us/typography/opentype/spec/recom#glyph-0-the-notdef-glyph
            if ".notdef" in new_glyph_order:
                new_glyph_order.remove(".notdef")
                new_glyph_order.insert(0, ".notdef")

            if old_glyph_order == new_glyph_order:
                return False

            self.ttfont.reorderGlyphs(new_glyph_order=new_glyph_order)

            # Remove this block when the new version of fontTools is released.
            if self.is_ps:
                cff_table = self.ttfont[const.T_CFF]
                top_dict = cff_table.cff.topDictIndex[0]
                charstrings = top_dict.CharStrings.charStrings
                sorted_charstrings = {k: charstrings.get(k) for k in new_glyph_order}
                top_dict.charset = new_glyph_order
                top_dict.CharStrings.charStrings = sorted_charstrings

            return True
        except Exception as e:
            raise FontError(e) from e
