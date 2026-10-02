"""
The ``foundrytools.core.tables`` module contains classes for handling ``fontTools.ttLib.tables``
objects.

Each table wrapper provides a set of methods for accessing and modifying the table data.

.. code-block:: python

    from foundrytools import Font

    font = Font("path/to/font.otf")
    font.t_cff_.round_coordinates()
    font.os_2.recalc_unicode_ranges()

Wrapped tables are accessible via the ``table`` property of the table wrapper.

.. code-block:: python

    from foundrytools import Font

    font = Font("path/to/font.otf")

    # Access the wrapped ``fontTools.ttLib.tables._c_m_a_p.table__c_m_a_p`` object
    font.t_cmap.table.buildReversed()
"""

from foundrytools import constants
from foundrytools.core.tables.cff_ import CFFTable
from foundrytools.core.tables.cmap import CmapTable
from foundrytools.core.tables.fvar import FvarTable
from foundrytools.core.tables.gdef import GdefTable
from foundrytools.core.tables.glyf import GlyfTable
from foundrytools.core.tables.gsub import GsubTable
from foundrytools.core.tables.head import HeadTable
from foundrytools.core.tables.hhea import HheaTable
from foundrytools.core.tables.hmtx import HmtxTable
from foundrytools.core.tables.kern import KernTable
from foundrytools.core.tables.name import NameTable
from foundrytools.core.tables.os_2 import OS2Table
from foundrytools.core.tables.post import PostTable

TABLES_LOOKUP = {
    constants.T_CFF: ("_cff", CFFTable),
    constants.T_CMAP: ("_cmap", CmapTable),
    constants.T_FVAR: ("_fvar", FvarTable),
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
    "FvarTable",
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
