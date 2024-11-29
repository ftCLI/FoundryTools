import contextlib
import math

from io import BytesIO
from pathlib import Path
from types import TracebackType
from typing import Optional, Union, Any, Literal

from collections.abc import Generator

import defcon
from cffsubr import subroutinize as subr, desubroutinize as desubr
from dehinter.font import dehint
from extractor import extractUFO
from fontTools.misc.cliTools import makeOutputFileName
from fontTools.misc.roundTools import otRound
from fontTools.pens.statisticsPen import StatisticsPen
from fontTools.subset import Options, Subsetter
from fontTools.ttLib import TTFont
from fontTools.ttLib.scaleUpem import scale_upem
from fontTools.ttLib.tables._f_v_a_r import Axis, NamedInstance
from ttfautohint import ttfautohint
from ufo2ft.postProcessor import PostProcessor

from foundrytools import constants as const, tables
from foundrytools.beziers_tools import add_extremes
from foundrytools.otf_builder import build_otf
from foundrytools.t2_charstrings import quadratics_to_cubics
from foundrytools.tables import FontTables
from foundrytools.ttf_builder import build_ttf
from foundrytools.utils.path_tools import get_temp_file_path
from foundrytools.utils.unicode_tools import (
    _cmap_from_glyph_names,
    _prod_name_from_uni_str,
    _ReversedCmap,
    get_mapped_and_unmapped_glyphs,
    get_uni_str,
    setup_character_map,
    update_character_map,
)

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

    def _set_font_style(self, bold: bool = None, italic: bool = None, regular: bool = None) -> None:
        if bold is not None:
            self.font.tables.os_2.fs_selection.bold = bold
            self.font.tables.head.mac_style.bold = bold
        if italic is not None:
            self.font.tables.os_2.fs_selection.italic = italic
            self.font.tables.head.mac_style.italic = italic
        if regular is not None:
            self.font.tables.os_2.fs_selection.regular = regular

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
            return self.font.tables.os_2.fs_selection.bold and self.font.tables.head.mac_style.bold
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
            return (
                self.font.tables.os_2.fs_selection.italic and self.font.tables.head.mac_style.italic
            )
        except Exception as e:
            raise FontError("An error occurred while checking if the font is italic") from e

    @is_italic.setter
    def is_italic(self, value: bool) -> None:
        with self._update_font_properties():
            self._set_font_style(italic=value, regular=not value if not self.is_bold else False)

    @property
    def is_oblique(self) -> bool:
        try:
            return self.font.tables.os_2.fs_selection.oblique
        except Exception as e:
            raise FontError("An error occurred while checking if the font is oblique") from e

    @is_oblique.setter
    def is_oblique(self, value: bool) -> None:
        """Set the oblique bit in the OS/2 table."""
        try:
            self.font.tables.os_2.fs_selection.oblique = value
        except Exception as e:
            raise FontError("An error occurred while setting the oblique bit") from e

    @property
    def is_regular(self) -> bool:
        try:
            return self.font.tables.os_2.fs_selection.regular
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
                self.font.tables.os_2.fs_selection.regular = not (self.is_bold or self.is_italic)


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
        self._is_modified = False
        self._init_font(font_source, lazy, recalc_bboxes, recalc_timestamp)
        self.tables: FontTables = FontTables(self.ttfont)
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
        A property with a getter method for the temporary file path of the font. The temporary file
        can be used, for example, to store the font file when it is loaded from a ``BytesIO`` object
        or a ``TTFont`` object and not from a file.

        :return: The temporary file path of the font.
        :rtype: Path
        """
        return self._temp_file

    @property
    def is_modified(self) -> bool:
        """
        A property with both getter and setter methods for the modified flag of the font.

        The ``Font`` class itself does not have a method to check if the underlying ``TTFont``
        object has been modified. Instead, the ``is_modified`` attribute of the individual tables
        (e.g., ``NameTable``, ``OS2Table``) should be used to determine if any modifications have
        been made.

        :return: A boolean indicating whether the font has been modified.
        :rtype: Bool
        """
        return self._is_modified

    @is_modified.setter
    def is_modified(self, value: bool) -> None:
        """
        Set the modified flag of the font.

        :param value: A boolean indicating whether the font has been modified.
        :type value: bool
        """
        self._is_modified = value

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
        self.tables = FontTables(self.ttfont)
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
            self.tt_decomponentize()

            charstrings = quadratics_to_cubics(
                font=self.ttfont, tolerance=tolerance, correct_contours=correct_contours
            )
            build_otf(font=self.ttfont, charstrings_dict=charstrings)

            self.tables.os_2.recalc_avg_char_width()
        except Exception as e:
            raise FontError(e) from e

    def to_sfnt(self) -> None:
        """Convert a font to SFNT."""
        if self.is_sfnt:
            raise NotImplementedError("Font is already a SFNT font.")
        self.ttfont.flavor = None

    def tt_autohint(self) -> None:
        """Autohint a TrueType font."""
        if not self.is_tt:
            raise NotImplementedError("TTF auto-hinting is only supported for TrueType fonts.")

        try:
            with BytesIO() as buffer:
                flavor = self.ttfont.flavor
                self.ttfont.flavor = None
                self.save(buffer, reorder_tables=None)
                data = ttfautohint(in_buffer=buffer.getvalue(), no_info=True)
                hinted_font = TTFont(BytesIO(data), recalcTimestamp=False)
                hinted_font[const.T_HEAD].modified = self.ttfont[const.T_HEAD].modified
                self.ttfont = hinted_font
                self.ttfont.flavor = flavor
        except Exception as e:
            raise FontError(e) from e

    def tt_dehint(self) -> None:
        """Dehint a TrueType font."""
        if not self.is_tt:
            raise NotImplementedError(
                "TrueType dehinting is only supported for TrueType flavored fonts."
            )

        try:
            dehint(self.ttfont, verbose=False)
        except Exception as e:
            raise FontError(e) from e

    def tt_decomponentize(self) -> Optional[set[str]]:
        """Decomposes all composite glyphs of a TrueType font."""
        if not self.is_tt:
            raise NotImplementedError("Decomponentization is only supported for TrueType fonts.")

        try:
            return self.tables.glyf.decompose_all()
        except Exception as e:
            raise FontError(e) from e

    def tt_scale_upem(self, target_upm: int) -> None:
        """
        Scale the Units Per Em (UPM) of a TrueType font.

        :param target_upm: The target UPM value. Must be in the range 16 to 16384.
        :type target_upm: int
        """
        if not self.is_tt:
            raise NotImplementedError("Scaling upem is only supported for TrueType fonts.")

        if target_upm < const.MIN_UPM or target_upm > const.MAX_UPM:
            raise ValueError(
                f"units_per_em must be in the range {const.MAX_UPM} to {const.MAX_UPM}."
            )

        if self.tables.head.units_per_em == target_upm:
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
                return self.tables.cff.correct_contours(
                    remove_hinting=remove_hinting,
                    ignore_errors=ignore_errors,
                    remove_unused_subroutines=remove_unused_subroutines,
                    min_area=min_area,
                )
            if self.is_tt:
                return self.tables.glyf.correct_contours(
                    remove_hinting=remove_hinting,
                    ignore_errors=ignore_errors,
                    min_area=min_area,
                )
            raise FontError("Unknown font type.")
        except Exception as e:
            raise FontError(e) from e

    def _restore_hinting_data(
        self, cff_table: tables.CFFTable, private_dict: dict[str, Any]
    ) -> None:
        """
        Restore hinting data to a PostScript font.

        :param cff_table: The CFF table of the font.
        :type cff_table: CFFTable
        :param private_dict: The private dictionary of the font.
        :type private_dict: dict[str, Any]
        """

        if not self.is_ps:
            raise NotImplementedError("Not a PostScript flavored font.")

        hinting_attributes = (
            "BlueValues",
            "OtherBlues",
            "FamilyBlues",
            "FamilyOtherBlues",
            "StdHW",
            "StdVW",
            "StemSnapH",
            "StemSnapV",
        )

        try:
            for attr in hinting_attributes:
                setattr(cff_table.private_dict, attr, private_dict.get(attr))
        except Exception as e:
            raise FontError(e) from e

    def ps_autohint(self, **kwargs: dict[str, Any]) -> None:
        """
        Autohint a PostScript font.

        :param kwargs: Additional options to pass to the autohinting process.
        :type kwargs: dict[str, Any]
        """
        if not self.is_ps:
            raise NotImplementedError(
                "OTF autohinting is only supported for PostScript flavored fonts."
            )

        try:
            self.tables.cff.autohint(**kwargs)
        except Exception as e:
            raise FontError(e) from e

    def ps_dehint(self, drop_hinting_data: bool = False) -> None:
        """
        Dehint a PostScript font.

        :param drop_hinting_data: If ``True``, drop hinting data from the CFF table. Defaults to
            ``False``.
        :type drop_hinting_data: bool
        :return: A boolean indicating whether the ``CFF`` table has been modified.
        :rtype: bool
        """
        if not self.is_ps:
            raise NotImplementedError(
                "PostScript dehinting is only supported for PostScript flavored fonts."
            )

        try:
            self.tables.cff.remove_hinting(drop_hinting_data=drop_hinting_data)
        except Exception as e:
            raise FontError(e) from e

    def ps_subroutinize(self) -> None:
        """Subroutinize a PostScript font."""
        if not self.is_ps:
            raise NotImplementedError(
                "Subroutinization is only supported for PostScript flavored fonts."
            )
        try:
            subr(self.ttfont)
        except Exception as e:
            raise FontError(e) from e

    def ps_desubroutinize(self) -> None:
        """Desubroutinize a PostScript font."""
        if not self.is_ps:
            raise NotImplementedError(
                "Desubroutinization is only supported for PostScript flavored fonts."
            )
        try:
            desubr(self.ttfont)
        except Exception as e:
            raise FontError(e) from e

    def ps_check_outlines(self) -> None:
        """Check the outlines of a PostScript font."""
        if not self.is_ps:
            raise NotImplementedError("Checking outlines is only supported for PostScript fonts.")

        try:
            self.tables.cff.check_outlines()
        except Exception as e:
            raise FontError(e) from e

    def ps_add_extremes(self, drop_hinting_data: bool = False) -> None:
        """
        Add extrema to the outlines of a PostScript font.

        :param drop_hinting_data: If ``True``, drop hinting data from the CFF table. Defaults to
            ``False``.
        :type drop_hinting_data: bool
        """
        if not self.is_ps:
            raise NotImplementedError("Adding extrema is only supported for PostScript fonts.")

        try:
            cff_table = tables.CFFTable(self.ttfont)
            data = cff_table.private_dict.rawDict
            charstrings = add_extremes(self.ttfont)
            build_otf(font=self.ttfont, charstrings_dict=charstrings)

            # Reload the font before correcting contours, otherwise the CFF top dict entries will be
            # deleted.
            self.reload()
            self.correct_contours(remove_hinting=True, ignore_errors=True)

            if not drop_hinting_data:
                # The font has been reloaded, so we need to instantiate the CFFTable again.
                cff_table = tables.CFFTable(self.ttfont)
                self._restore_hinting_data(cff_table, data)
        except Exception as e:
            raise FontError(e) from e

    def ps_round_coordinates(self) -> set[str]:
        """
        Round the outlines coordinates of a PostScript font.

        :return: A set of glyph names that have been modified.
        :rtype: set[str]
        """
        if not self.is_ps:
            raise NotImplementedError(
                "Rounding coordinates is only supported for PostScript fonts."
            )

        try:
            return self.tables.cff.round_coordinates()
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

    def fix_italic_angle(
        self, min_slant: float = 2.0, italic: bool = True, oblique: bool = False
    ) -> dict[str, dict[str, Any]]:
        """
        Fix the italic angle of the font.

        This method calculates the italic angle of the font and updates the ``post`` and ``hhea``
        tables with the new values if they differ from the current values. If the font is a
        PostScript font, the ``cff`` table is also updated. The method also updates the italic and
        oblique bits in the ``OS/2`` and `head` tables.

        :param min_slant: The minimum slant value to consider the font italic. Defaults to 2.0.
        :type min_slant: float
        :param italic: If ``True``, set the font to italic when the italic angle is not zero.
            Defaults to ``True``.
        :type italic: bool
        :param oblique: If ``True``, set the font to oblique when the italic angle is not zero.
            Defaults to ``False``.
        :return: A dictionary containing the old and new values of the italic angle and the run/rise
                 values, along with a check result indicating whether the values were updated.
        :rtype: dict[str, dict[str, Any]]
        """

        result: dict[str, dict[str, Any]] = {}
        try:
            is_italic = self.flags.is_italic
            is_oblique = self.flags.is_oblique
            post_italic_angle = self.tables.post.italic_angle
            hhea_run_rise = (self.tables.hhea.caret_slope_run, self.tables.hhea.caret_slope_rise)
            run_rise_angle = self.tables.hhea.run_rise_angle

            # Calculate the italic angle and the caret slope run and rise values.
            calculated_slant = self.calc_italic_angle(min_slant=min_slant)
            calculated_run = self.tables.hhea.calc_caret_slope_run(italic_angle=calculated_slant)
            calculated_rise = self.tables.hhea.calc_caret_slope_rise(italic_angle=calculated_slant)

            # Check if the ``is_italic`` attribute is correctly set.
            should_be_italic = italic and calculated_slant != 0.0
            italic_bits_check = is_italic == should_be_italic
            if not italic_bits_check:
                self.flags.is_italic = should_be_italic
            result["is_italic"] = {
                "old": is_italic,
                "new": should_be_italic,
                "pass": italic_bits_check,
            }

            # Check if the ``is_oblique`` attribute is correctly set. The oblique bit is only
            # defined in ``OS/2`` table version 4 and later.
            should_be_oblique = (
                oblique and calculated_slant != 0.0 and self.tables.os_2.version >= 4
            )
            oblique_bit_check = is_oblique == should_be_oblique
            if not oblique_bit_check:
                self.flags.is_oblique = should_be_oblique
            result["is_oblique"] = {
                "old": is_oblique,
                "new": should_be_oblique,
                "pass": oblique_bit_check,
            }

            # Check if the italic is correctly set in the ``post`` table.
            italic_angle_check = otRound(post_italic_angle) == otRound(calculated_slant)
            if not italic_angle_check:
                self.tables.post.italic_angle = calculated_slant
            result["italic_angle"] = {
                "old": post_italic_angle,
                "new": calculated_slant,
                "pass": italic_angle_check,
            }

            # Check if the run/rise values are correctly set in the ``hhea`` table.
            run_rise_check = otRound(run_rise_angle) == otRound(calculated_slant)
            if not run_rise_check:
                self.tables.hhea.caret_slope_run = calculated_run
                self.tables.hhea.caret_slope_rise = calculated_rise
            result["run_rise"] = {
                "old": hhea_run_rise,
                "new": (calculated_run, calculated_rise),
                "pass": run_rise_check,
            }

            if self.is_ps:
                cff_italic_angle = self.tables.cff.top_dict.ItalicAngle
                cff_italic_angle_check = otRound(cff_italic_angle) == otRound(calculated_slant)
                if not cff_italic_angle_check:
                    self.tables.cff.top_dict.ItalicAngle = otRound(calculated_slant)
                result["cff_italic_angle"] = {
                    "old": cff_italic_angle,
                    "new": calculated_slant,
                    "pass": cff_italic_angle_check,
                }

            return result

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

    def remove_glyphs(
        self,
        glyph_names_to_remove: Optional[set[str]],
        glyph_ids_to_remove: Optional[set[int]],
    ) -> set[str]:
        """
        Removes glyphs from the font object.

        :param glyph_names_to_remove: A set of glyph names to remove.
        :type glyph_names_to_remove: Optional[set[str]]
        :param glyph_ids_to_remove: A set of glyph IDs to remove.
        :type glyph_ids_to_remove: Optional[set[int]]
        :return: A set of glyph names that were removed.
        :rtype: set[str]
        """
        try:
            old_glyph_order = self.ttfont.getGlyphOrder()
            if not glyph_names_to_remove and not glyph_ids_to_remove:
                raise ValueError("No glyph names or glyph IDs provided to remove.")

            glyph_names_to_remove = glyph_names_to_remove or set()

            # Convert glyph IDs to glyph names to populate the subsetter with only one parameter.
            if glyph_ids_to_remove:
                for glyph_id in glyph_ids_to_remove:
                    if glyph_id < 0 or glyph_id >= len(old_glyph_order):
                        continue
                    glyph_names_to_remove.add(old_glyph_order[glyph_id])

            if not glyph_names_to_remove:
                return set()

            remaining_glyphs = {gn for gn in old_glyph_order if gn not in glyph_names_to_remove}
            options = Options(**const.SUBSETTER_DEFAULTS)
            options.recalc_timestamp = self.ttfont.recalcTimestamp

            subsetter = Subsetter(options=options)
            subsetter.populate(glyphs=remaining_glyphs)
            subsetter.subset(self.ttfont)

            new_glyph_order = self.ttfont.getGlyphOrder()
            return set(old_glyph_order).difference(new_glyph_order)
        except Exception as e:
            raise FontError(e) from e

    def remove_unused_glyphs(self) -> set[str]:
        """
        Remove glyphs that are not reachable by Unicode values or by substitution rules in the font.

        :return: A set of glyph names that were removed.
        :rtype: set[str]
        """
        try:
            options = Options(**const.SUBSETTER_DEFAULTS)
            options.recalc_timestamp = self.ttfont.recalcTimestamp
            old_glyph_order = self.ttfont.getGlyphOrder()
            unicodes = self.tables.cmap.get_codepoints()
            subsetter = Subsetter(options=options)
            subsetter.populate(unicodes=unicodes)
            subsetter.subset(self.ttfont)
            new_glyph_order = self.ttfont.getGlyphOrder()

            return set(old_glyph_order) - set(new_glyph_order)
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
