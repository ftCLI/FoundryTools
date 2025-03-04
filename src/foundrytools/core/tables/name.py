"""Name table."""

from __future__ import annotations

from copy import deepcopy
from typing import TYPE_CHECKING

from fontTools.misc.timeTools import timestampToString
from fontTools.ttLib.tables._n_a_m_e import (
    _MAC_LANGUAGE_CODES,
    _WINDOWS_LANGUAGE_CODES,
    NameRecord,
    table__n_a_m_e,
)

from foundrytools.constants import T_HEAD, T_NAME, T_OS_2, NameIds
from foundrytools.core.tables.default import DefaultTbl

if TYPE_CHECKING:
    from collections.abc import Iterable

    from fontTools.ttLib import TTFont


class NameTable(DefaultTbl):
    """Extend the fontTools ``name`` table."""

    def __init__(self, ttfont: TTFont) -> None:
        """
        Initialize the ``name`` table handler.

        :param ttfont: The ``TTFont`` object.
        :type ttfont: TTFont
        """
        super().__init__(ttfont=ttfont, table_tag=T_NAME)
        self._copy = deepcopy(self.table)
        self._is_modified = False

    @property
    def table(self) -> table__n_a_m_e:
        """The wrapped ``table__n_a_m_e`` table object."""
        return self._table

    @table.setter
    def table(self, value: table__n_a_m_e) -> None:
        """Wrap a new ``table__n_a_m_e`` object."""
        self._table = value

    @property
    def is_modified(self) -> bool:
        """
        Compile the original and current ``name`` tables.

        Compare them to determine if the table has been modified.

        :return: Whether the ``name`` table has been modified.
        :rtype: bool
        """
        return self._copy.compile(self.ttfont) != self.table.compile(self.ttfont)

    def set_name(
        self,
        name_id: int,
        name_string: str,
        platform_id: int | None = None,
        language_string: str = "en",
    ) -> None:
        """
        Add a NameRecord to the ``name`` table of a font.

        :param name_id: The NameID of the NameRecord.
        :type name_id: int
        :param name_string: The string to add to the NameRecord.
        :type name_string: str
        :param platform_id: The platform ID of the NameRecord. Defaults to None. If None, the
            NameRecord is added to both platforms. If 1, the NameRecord is added to the Macintosh
            platform. If 3, the NameRecord is added to the Windows platform.
        :type platform_id: Optional[int]
        :param language_string: The language of the NameRecord. Defaults to "en".
        :type language_string: str
        """
        # Remove the NameRecord before writing it to avoid duplicates
        self.remove_names(name_ids=(name_id,), platform_id=platform_id, language_string=language_string)

        if platform_id == 1:
            mac, windows = True, False
        elif platform_id == 3:  # noqa: PLR2004
            mac, windows = False, True
        else:
            mac, windows = True, True

        names = {language_string: name_string}
        self.table.addMultilingualName(names, ttFont=self.ttfont, nameID=name_id, windows=windows, mac=mac)

    def remove_names(
        self,
        name_ids: Iterable[int],
        platform_id: int | None = None,
        language_string: str | None = None,
    ) -> None:
        """
        Delete the specified NameRecords from the ``name`` table of a font.

        :param name_ids: A list of NameIDs to remove.
        :type name_ids: Iterable[int]
        :param platform_id: The platform ID of the NameRecords to remove. Defaults to None, which
            means that NameRecords from all platforms are removed. If 1, only NameRecords with
            platformID 1 (Macintosh) are removed. If 3, only NameRecords with platformID 3 (Windows)
            are removed.
        :type platform_id: Optional[int]
        :param language_string: The language of the NameRecords to remove. Defaults to None, which
            means that NameRecords in all languages are removed.
        :type language_string: Optional[str]
        """
        names = self.filter_names(name_ids=set(name_ids), platform_id=platform_id, lang_string=language_string)
        for name in names:
            self.table.removeNames(name.nameID, name.platformID, name.platEncID, name.langID)

    def remove_unused_names(self) -> set[int]:
        """Remove unused NameRecords from the ``name`` table."""
        return self.table.removeUnusedNames(self.ttfont)

    def find_replace(
        self,
        old_string: str,
        new_string: str,
        name_ids_to_process: tuple[int] | None = None,
        name_ids_to_skip: tuple[int] | None = None,
        platform_id: int | None = None,
    ) -> None:
        """
        Find and replaces occurrences of a string in the specified NameRecords of the ``name`` table of a font.

        :param old_string: The string to find.
        :type old_string: str
        :param new_string: The string to replace the old string with.
        :type new_string: str
        :param name_ids_to_process: A tuple of name IDs to process. Defaults to None, which means
            that all name IDs are processed.
        :type name_ids_to_process: Optional[tuple[int]]
        :param name_ids_to_skip: A tuple of name IDs to skip. Defaults to None, which means that no
            name IDs are skipped.
        :type name_ids_to_skip: Optional[tuple[int]]
        :param platform_id: The platform ID of the name records to process. Defaults to None, which
            means that NameRecords from all platforms are processed. If 1, only NameRecords with
            platformID 1 (Macintosh) are processed. If 3, only NameRecords with platformID 3
            (Windows) are processed.
        :type platform_id: Optional[int]
        """
        name_ids = self._get_name_ids_for_filter(
            name_ids_to_process=name_ids_to_process, name_ids_to_skip=name_ids_to_skip
        )
        names = self.filter_names(name_ids=name_ids, platform_id=platform_id)
        for name in names:
            if old_string in str(name):
                string = str(name).replace(old_string, new_string).replace("  ", " ").strip()
                self.table.setName(
                    string,
                    name.nameID,
                    name.platformID,
                    name.platEncID,
                    name.langID,
                )

    def append_prefix_suffix(
        self,
        name_ids: tuple[int],
        platform_id: int | None = None,
        language_string: str | None = None,
        prefix: str | None = None,
        suffix: str | None = None,
    ) -> None:
        """
        Append a prefix, a suffix, or both to the NameRecords that match the nameID, platformID, and language string.

        :param name_ids: A tuple of name IDs to process.
        :type name_ids: tuple[int]
        :param platform_id: The platform ID of the name records to process. Defaults to None, which
            means that NameRecords from all platforms are processed. If 1, only NameRecords with
            platformID 1 (Macintosh) are processed. If 3, only NameRecords with platformID 3
            (Windows) are processed.
        :type platform_id: Optional[int]
        :param language_string: The language of the name records to process. Defaults to None, which
            means that NameRecords in all languages are processed.
        :type language_string: Optional[str]
        :param prefix: The prefix to append to the NameRecords. Defaults to None.
        :type prefix: Optional[str]
        :param suffix: The suffix to append to the NameRecords. Defaults to None.
        """
        names = self.filter_names(name_ids=set(name_ids), platform_id=platform_id, lang_string=language_string)

        for name in names:
            string = name.toUnicode()
            if prefix is not None:
                string = f"{prefix}{string}"
            if suffix is not None:
                string = f"{string}{suffix}"

            self.table.setName(
                string=string,
                nameID=name.nameID,
                platformID=name.platformID,
                platEncID=name.platEncID,
                langID=name.langID,
            )

    def strip_names(self) -> None:
        """Remove leading and trailing spaces from all NameRecords in the ``name`` table."""
        for name in self.table.names:
            self.table.setName(
                str(name).strip(),
                name.nameID,
                name.platformID,
                name.platEncID,
                name.langID,
            )

    def remove_empty_names(self) -> None:
        """Remove all empty NameRecords from the ``name`` table."""
        for name in self.table.names:
            if str(name).strip() == "":
                self.table.removeNames(
                    nameID=name.nameID,
                    platformID=name.platformID,
                    platEncID=name.platEncID,
                    langID=name.langID,
                )

    def _get_name_ids_for_filter(
        self,
        name_ids_to_process: Iterable | None = None,
        name_ids_to_skip: Iterable | None = None,
    ) -> set[int]:
        """Return a set of name IDs to be used for filtering."""
        all_name_ids = {name.nameID for name in self.table.names}
        if name_ids_to_process:
            all_name_ids.intersection_update(name_ids_to_process)
        if name_ids_to_skip:
            all_name_ids.difference(name_ids_to_skip)
        return all_name_ids

    def filter_names(
        self,
        name_ids: set[int] | None = None,
        platform_id: int | None = None,
        plat_enc_id: int | None = None,
        lang_id: int | None = None,
        lang_string: str | None = None,
    ) -> list[NameRecord]:
        """
        Filter NameRecords based on the given parameters.

        :param name_ids: A set of NameIDs to filter. Defaults to None, which means that all NameIDs
            are filtered.
        :type name_ids: Optional[set[int]]
        :param platform_id: The platform ID of the NameRecords to filter. Defaults to None, which
            means that NameRecords from all platforms are filtered. If 1, only NameRecords with
            platformID 1 (Macintosh) are filtered. If 3, only NameRecords with platformID 3
            (Windows) are filtered.
        :type platform_id: Optional[int]
        :param plat_enc_id: The platform encoding ID of the NameRecords to filter. Defaults to None,
            which means that NameRecords from all platform encoding IDs are filtered.
        :type plat_enc_id: Optional[int]
        :param lang_id: The language ID of the NameRecords to filter. Defaults to None, which means
            that NameRecords from all languages are filtered.
        :type lang_id: Optional[int]
        :param lang_string: The language string of the NameRecords to filter. Defaults to None,
            which means that NameRecords from all languages are filtered.
        :type lang_string: Optional[str]
        :return: The filtered NameRecords.
        :rtype: list[NameRecord]
        """
        return [
            name
            for name in self.table.names
            if (name_ids is None or name.nameID in name_ids)
            and (platform_id is None or name.platformID == platform_id)
            and (plat_enc_id is None or name.platEncID == plat_enc_id)
            and (lang_id is None or name.langID == lang_id)
            and (
                lang_string is None
                or name.langID
                in (
                    _MAC_LANGUAGE_CODES.get(lang_string.lower()),
                    _WINDOWS_LANGUAGE_CODES.get(lang_string.lower()),
                )
            )
        ]

    def get_best_family_name(self) -> str:
        """
        Return the best family name from the ``name`` table.

        The best family name is converted to string to handle cases where the family name is None.

        :return: The best family name.
        :rtype: str
        """
        return str(self.table.getBestFamilyName())

    def get_best_subfamily_name(self) -> str:
        """
        Return the best subfamily name from the ``name`` table.

        The best subfamily name is converted to string to handle cases where the subfamily name is None.

        :return: The best subfamily name.
        :rtype: str
        """
        return str(self.table.getBestSubFamilyName())

    def get_debug_name(self, name_id: int) -> str:
        """
        Return the NameRecord string with the specified NameID.

        The NameRecord is converted to string to handle cases where the NameRecord is None.

        :param name_id: The NameID of the NameRecord.
        :type name_id: int
        :return: The debug name of the NameRecord.
        :rtype: str
        """
        return str(self.table.getDebugName(name_id))

    def build_unique_identifier(self, *, platform_id: int | None = None, alternate: bool = False) -> None:
        """
        Build the NameID 3 (Unique Font Identifier) record based on the font revision, vendor ID, and PostScript name.

        :param platform_id: The platform ID of the name record. Defaults to None. If None, the
            NameRecord is added to both platforms. If 1, the NameRecord is added to the Macintosh
            platform. If 3, the NameRecord is added to the Windows platform.
        :type platform_id: Optional[int]
        :param alternate: Whether to build an alternate unique identifier. Defaults to False. If
            False, the unique identifier is built based on the font revision, vendor ID, and
            PostScript name. If True, the unique identifier is built based on the manufacturer name,
            family name, subfamily name, and year created.
        :type alternate: bool
        """
        if not alternate:
            font_revision = round(self.ttfont[T_HEAD].fontRevision, 3)
            vendor_id = self.ttfont[T_OS_2].achVendID
            postscript_name = self.get_debug_name(NameIds.POSTSCRIPT_NAME)
            unique_id = f"{font_revision};{vendor_id};{postscript_name}"
        else:
            year_created = timestampToString(self.ttfont[T_HEAD].created).split(" ")[-1]
            family_name = self.get_best_family_name()
            subfamily_name = self.get_best_subfamily_name()
            manufacturer_name = self.get_debug_name(NameIds.MANUFACTURER_NAME)
            unique_id = f"{manufacturer_name}: {family_name}-{subfamily_name}: {year_created}"

        self.set_name(name_id=NameIds.UNIQUE_FONT_IDENTIFIER, name_string=unique_id, platform_id=platform_id)

    def build_full_font_name(self, platform_id: int | None = None) -> None:
        """
        Build the NameID 4 (Full Font Name) record based on the family name and subfamily name.

        :param platform_id: The platform ID of the name record. Defaults to None. If None, the
            NameRecord is added to both platforms. If 1, the NameRecord is added to the Macintosh
            platform. If 3, the NameRecord is added to the Windows platform.
        :type platform_id: Optional[int]
        """
        family_name = self.get_best_family_name()
        subfamily_name = self.get_best_subfamily_name()
        full_font_name = f"{family_name} {subfamily_name}"

        self.set_name(name_id=NameIds.FULL_FONT_NAME, name_string=full_font_name, platform_id=platform_id)

    def build_version_string(self, platform_id: int | None = None) -> None:
        """
        Build the NameID 5 (Version String) record based on the font revision.

        :param platform_id: The platform ID of the name record. Defaults to None. If None, the
            NameRecord is added to both platforms. If 1, the NameRecord is added to the Macintosh
            platform. If 3, the NameRecord is added to the Windows platform.
        :type platform_id: Optional[int]
        """
        font_revision = round(self.ttfont[T_HEAD].fontRevision, 3)
        version_string = f"Version {font_revision}"

        self.set_name(name_id=NameIds.VERSION_STRING, name_string=version_string, platform_id=platform_id)

    def build_postscript_name(self, platform_id: int | None = None) -> None:
        """
        Build the NameID 6 (PostScript Name) record based on the PostScript name.

        :param platform_id: The platform ID of the name record. Defaults to None. If None, the
            NameRecord is added to both platforms. If 1, the NameRecord is added to the Macintosh
            platform. If 3, the NameRecord is added to the Windows platform.
        :type platform_id: Optional[int]
        """
        family_name = self.get_best_family_name()
        subfamily_name = self.get_best_subfamily_name()
        postscript_name = f"{family_name}-{subfamily_name}".replace(" ", "").replace(".", "_")

        self.set_name(name_id=NameIds.POSTSCRIPT_NAME, name_string=postscript_name, platform_id=platform_id)

    def build_mac_names(self) -> None:
        """
        Build the Macintosh-specific NameRecords.

        1 (Font Family Name),
        2 (Font Subfamily Name),
        4 (Full Font Name),
        5 (Version String), and
        6 (PostScript Name).
        """
        name_ids = {1, 2, 4, 5, 6}
        names = self.filter_names(name_ids=name_ids, platform_id=3)
        for name in names:
            try:
                string = str(self.table.getDebugName(name.nameID))
                self.set_name(name_id=name.nameID, name_string=string, platform_id=1)
            except AttributeError:  # noqa: PERF203
                continue

    def remove_mac_names(self) -> None:
        """Remove all Macintosh-specific NameRecords from the ``name`` table."""
        self.table.removeNames(platformID=1)

    def remap_name_ids(self) -> dict[int, int]:
        """Remap the NameIDs of the NameRecords in the ``name`` table."""
        names_to_remap = {name for name in self.table.names if name.nameID >= 256}  # noqa: PLR2004
        name_ids_map: dict[int, int] = {}

        for name_id, name in enumerate(names_to_remap, start=256):
            name_ids_map[name.nameID] = name_id
            name.nameID = name_id

        return name_ids_map
