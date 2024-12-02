from foundrytools import constants
from foundrytools.tables.cff_ import CFFTable
from foundrytools.tables.cmap import CmapTable
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

TABLES_LOOKUP = {
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

__all__ = [
    "CFFTable",
    "CmapTable",
    "GdefTable",
    "GlyfTable",
    "GsubTable",
    "HeadTable",
    "HheaTable",
    "HmtxTable",
    "KernTable",
    "NameTable",
    "OS2Table",
    "PostTable",
    "TABLES_LOOKUP",
]
