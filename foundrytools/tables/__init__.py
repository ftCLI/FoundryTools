from typing import Optional, TypeVar

from fontTools.ttLib import TTFont

from foundrytools import constants
from foundrytools.tables.cff_ import CFFTable
from foundrytools.tables.cmap import CmapTable
from foundrytools.tables.default import DefaultTbl
from foundrytools.tables.gdef import GdefTable
from foundrytools.tables.glyf import GlyfTable
from foundrytools.tables.gsub import GsubTable
from foundrytools.tables.head import HeadTable
from foundrytools.tables.hhea import HheaTable
from foundrytools.tables.hmtx import HmtxTable
from foundrytools.tables.kern import KernTable
from foundrytools.tables.name import NameTable
from foundrytools.tables.os_2 import OS2Table
from foundrytools.tables.post import PostTable


T = TypeVar("T", bound=DefaultTbl)

TABLE_CLASSES_MAPPING = {
    constants.T_CFF: ("_cff", CFFTable),
    constants.T_CMAP: ("_cmap", CmapTable),
    constants.T_GDEF: ("_gdef", GdefTable),
    constants.T_GLYF: ("_glyf", GlyfTable),
    constants.T_GSUB: ("_gsub", GsubTable),
    constants.T_HEAD: ("_head", HeadTable),
    constants.T_HHEA: ("_hhea", HheaTable),
    constants.T_KERN: ("_kern", KernTable),
    constants.T_HMTX: ("_hmtx", HmtxTable),
    constants.T_NAME: ("_name", NameTable),
    constants.T_OS_2: ("_os_2", OS2Table),
    constants.T_POST: ("_post", PostTable),
}


class TableError(Exception):
    """The ``TableError`` class is a custom exception class for table-related errors."""


class FontTables:  # pylint: disable=too-many-instance-attributes
    """
    The ``Tables`` class is responsible for managing and accessing various font tables.

    :param font: The ``Font`` object to which the tables belong.
    :type font: Font
    """

    def __init__(self, font: TTFont):
        self.font: TTFont = font
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

    def load_table(self, table_tag: str) -> None:
        """
        Load a font table based on the provided table tag.

        :param table_tag: The tag of the table to load (e.g., 'CFF ', 'cmap').
        :type table_tag: str
        :raises TableError: If the table is not present in the font or if an unknown table tag is
            provided.
        """

        try:
            if table_tag not in self.font:
                raise TableError(f"Table '{table_tag}' is not present in the font")

            class_entry = TABLE_CLASSES_MAPPING.get(table_tag)
            if class_entry is None:
                raise TableError(f"Unknown table tag '{table_tag}'")

            table_attribute, table_class = class_entry
            setattr(self, table_attribute, table_class(self.font))
        except Exception as e:
            raise TableError(f"An error occurred while loading the '{table_tag}' table: {e}") from e

    def _get_table(self, table_attr: str, table_tag: str) -> T:
        if getattr(self, table_attr) is None:
            self.load_table(table_tag)
        table = getattr(self, table_attr)
        if table is None:
            raise KeyError(f"The '{table_tag}' table is not present in the font")
        return table

    @property
    def cff(self) -> CFFTable:
        """
        The ``CFFTable`` property of the ``Tables`` class. The ``CFFTable`` class is used to
        interact with the ``CFF`` table of the font.

        :return: The loaded ``CFFTable``.
        :rtype: tables.CFFTable
        """
        return self._get_table("_cff", constants.T_CFF)

    @property
    def cmap(self) -> CmapTable:
        """
        The ``CmapTable`` property of the ``Tables`` class. The ``CmapTable`` class is used to
        interact with the ``cmap`` table of the font.

        :return: The loaded ``CmapTable``.
        :rtype: tables.CmapTable
        """
        return self._get_table("_cmap", constants.T_CMAP)

    @property
    def gdef(self) -> GdefTable:
        """
        The ``GdefTable`` property of the ``Tables`` class. The ``GdefTable`` class is used to
        interact with the ``GDEF`` table of the font.

        :return: The loaded ``GdefTable``.
        :rtype: tables.GdefTable
        """
        return self._get_table("_gdef", constants.T_GDEF)

    @property
    def glyf(self) -> GlyfTable:
        """
        The ``GlyfTable`` property of the ``Tables`` class. The ``GlyfTable`` class is used to
        interact with the ``glyf`` table of the font.

        :return: The loaded ``GlyfTable``.
        :rtype: tables.GlyfTable
        """
        return self._get_table("_glyf", constants.T_GLYF)

    @property
    def gsub(self) -> GsubTable:
        """
        The ``GsubTable`` property of the ``Tables`` class. The ``GsubTable`` class is used to
        interact with the ``GSUB`` table of the font.

        :return: The loaded ``GsubTable``.
        :rtype: tables.GsubTable
        """
        return self._get_table("_gsub", constants.T_GSUB)

    @property
    def head(self) -> HeadTable:
        """
        The ``HeadTable`` property of the ``Tables`` class. The ``HeadTable`` class is used to
        interact with the ``head`` table of the font.

        :return: The loaded ``HeadTable``.
        :rtype: tables.HeadTable
        """
        return self._get_table("_head", constants.T_HEAD)

    @property
    def hhea(self) -> HheaTable:
        """
        The ``HheaTable`` property of the ``Tables`` class. The ``HheaTable`` class is used to
        interact with the ``hhea`` table of the font.

        :return: The loaded ``HheaTable``.
        :rtype: tables.HheaTable
        """
        return self._get_table("_hhea", constants.T_HHEA)

    @property
    def hmtx(self) -> HmtxTable:
        """
        The ``HmtxTable`` property of the ``Tables`` class. The ``HmtxTable`` class is used to
        interact with the ``hmtx`` table of the font.

        :return: The loaded ``HmtxTable``.
        :rtype: tables.HmtxTable
        """
        return self._get_table("_hmtx", constants.T_HMTX)

    @property
    def kern(self) -> KernTable:
        """
        The ``KernTable`` property of the ``Tables`` class. The ``KernTable`` class is used to
        interact with the ``kern`` table of the font.

        :return: The loaded ``KernTable``.
        :rtype: tables.KernTable
        """
        return self._get_table("_kern", constants.T_KERN)

    @property
    def name(self) -> NameTable:
        """
        The ``NameTable`` property of the ``Tables`` class. The ``NameTable`` class is used to
        interact with the ``name`` table of the font.

        :return: The loaded ``NameTable``.
        :rtype: tables.NameTable
        """
        return self._get_table("_name", constants.T_NAME)

    @property
    def os_2(self) -> OS2Table:
        """
        The ``OS2Table`` property of the ``Tables`` class. The ``OS2Table`` class is used to
        interact with the ``OS/2`` table of the font.

        :return: The loaded ``OS2Table``.
        :rtype: tables.OS2Table
        """
        return self._get_table("_os_2", constants.T_OS_2)

    @property
    def post(self) -> PostTable:
        """
        The ``PostTable`` property of the ``Tables`` class. The ``PostTable`` class is used to
        interact with the ``post`` table of the font.

        :return: The loaded ``PostTable``.
        :rtype: tables.PostTable
        """
        return self._get_table("_post", constants.T_POST)


__all__ = [
    "CFFTable",
    "CmapTable",
    "GdefTable",
    "GlyfTable",
    "GsubTable",
    "HeadTable",
    "HheaTable",
    "HmtxTable",
    "NameTable",
    "OS2Table",
    "PostTable",
    "TableError",
    "FontTables",
]
