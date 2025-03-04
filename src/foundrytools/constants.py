"""Global constants."""

from enum import IntEnum
from importlib import resources as pkg_resources

import foundrytools

with pkg_resources.as_file(pkg_resources.files(foundrytools)) as package_dir:
    DATA_DIR = package_dir / "data"

NAMES_TO_UNICODES_FILE = DATA_DIR / "names_to_unicodes.json"
UNICODES_TO_NAMES_FILE = DATA_DIR / "unicodes_to_names.json"

PS_SFNT_VERSION = "OTTO"
TT_SFNT_VERSION = "\0\1\0\0"

WOFF_FLAVOR = "woff"
WOFF2_FLAVOR = "woff2"
OTF_EXTENSION = ".otf"
TTF_EXTENSION = ".ttf"
WOFF_EXTENSION = ".woff"
WOFF2_EXTENSION = ".woff2"

MIN_UPM = 16
MAX_UPM = 16384
MIN_US_WEIGHT_CLASS = 1
MAX_US_WEIGHT_CLASS = 1000
MIN_US_WIDTH_CLASS = 1
MAX_US_WIDTH_CLASS = 9

# Table tags
T_CFF = "CFF "
T_CMAP = "cmap"
T_CVAR = "cvar"
T_FPGM = "fpgm"
T_FVAR = "fvar"
T_GDEF = "GDEF"
T_GLYF = "glyf"
T_GSUB = "GSUB"
T_HEAD = "head"
T_HHEA = "hhea"
T_HMTX = "hmtx"
T_KERN = "kern"
T_LOCA = "loca"
T_MAXP = "maxp"
T_NAME = "name"
T_OS_2 = "OS/2"
T_POST = "post"
T_STAT = "STAT"
T_VORG = "VORG"


class NameIds(IntEnum):
    """Enumeration of common name IDs in the name table."""

    FAMILY_NAME = 1
    SUBFAMILY_NAME = 2
    UNIQUE_FONT_IDENTIFIER = 3
    FULL_FONT_NAME = 4
    VERSION_STRING = 5
    POSTSCRIPT_NAME = 6
    TRADEMARK = 7
    MANUFACTURER_NAME = 8
    DESIGNER_NAME = 9
    DESCRIPTION = 10
    VENDOR_URL = 11
    DESIGNER_URL = 12
    LICENSE_DESCRIPTION = 13
    LICENSE_INFO_URL = 14
    RESERVED = 15
    TYPO_FAMILY_NAME = 16
    TYPO_SUBFAMILY_NAME = 17
    COMPATIBLE_FULL_NAME_MAC = 18
    SAMPLE_TEXT = 19
    PS_CID_FINDFONT_NAME = 20
    WWS_FAMILY_NAME = 21
    WWS_SUBFAMILY_NAME = 22
    LIGHT_BACKGROUND_PALETTE = 23
    DARK_BACKGROUND_PALETTE = 24
    VARIATIONS_POSTSCRIPT_NAME_PREFIX = 25


NAME_IDS_TO_DESCRIPTION = {
    0: "Copyright Notice",
    1: "Family name",
    2: "Subfamily name",
    3: "Unique identifier",
    4: "Full font name",
    5: "Version string",
    6: "PostScript name",
    7: "Trademark",
    8: "Manufacturer Name",
    9: "Designer",
    10: "Description",
    11: "URL Vendor",
    12: "URL Designer",
    13: "License Description",
    14: "License Info URL",
    15: "Reserved",
    16: "Typographic Family",
    17: "Typographic Subfamily",
    18: "Compatible Full (Mac)",
    19: "Sample text",
    20: "PS CID font name",
    21: "WWS Family Name",
    22: "WWS Subfamily Name",
    23: "Light Background Palette",
    24: "Dark Background Palette",
    25: "Variations PSName Pref",
}


TOP_DICT_NAMES = {
    "full-name": "FullName",
    "family-name": "FamilyName",
    "weight": "Weight",
    "version": "version",
    "notice": "Notice",
    "copyright": "Copyright",
}


PLATFORMS = {
    0: "Unicode",
    1: "Macintosh",
    2: "ISO (deprecated)",
    3: "Windows",
    4: "Custom",
}


MAC_ENCODING_IDS = {
    0: "Roman",
    1: "Japanese",
    2: "Chinese (Traditional)",
    3: "Korean",
    4: "Arabic",
    5: "Hebrew",
    6: "Greek",
    7: "Russian",
    8: "RSymbol",
    9: "Devanagari",
    10: "Gurmukhi",
    11: "Gujarati",
    12: "Oriya",
    13: "Bengali",
    14: "Tamil",
    15: "Telugu",
    16: "Kannada",
    17: "Malayalam",
    18: "Sinhalese",
    19: "Burmese",
    20: "Khmer",
    21: "Thai",
    22: "Laotian",
    23: "Georgian",
    24: "Armenian",
    25: "Chinese (Simplified)",
    26: "Tibetan",
    27: "Mongolian",
    28: "Geez",
    29: "Slavic",
    30: "Vietnamese",
    31: "Sindhi",
    32: "Uninterpreted",
}


WINDOWS_ENCODING_IDS = {
    0: "Symbol",
    1: "Unicode",
    2: "ShiftJIS",
    3: "PRC",
    4: "Big5",
    5: "Wansung",
    6: "Johab",
    7: "Reserved",
    8: "Reserved",
    9: "Reserved",
    10: "UCS4",
}
