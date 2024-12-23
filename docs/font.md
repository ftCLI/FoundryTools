## Font Class: High-Level Wrapper for TTFont

### Overview

The `Font` class is a high-level wrapper around the `TTFont` class from the **fontTools** library,
providing a user-friendly interface for working with font files and their data. It simplifies font
manipulation and offers various utilities for accessing and modifying font-specific properties.

### Features

- Load fonts from multiple sources including file paths, BytesIO objects, and TTFont instances.
- Manipulate font tables, attributes, and metadata.
- Provides Pythonic getter and setter properties for accessing internal font data.
- Works as a context manager to automatically manage resources.

### Initialization

The class is initialized with the following parameters:

- **\`font_source\`**: A path to a font file (as `str` or `Path`), a `BytesIO` object, or an
  existing `TTFont` instance.
- **\`lazy\`** *(Optional[bool], Default: None)*: Controls whether font data is loaded lazily
  (on-demand) or eagerly (immediately). The default value None falls somewhere between.
- **\`recalc_bboxes\`** *(bool, Default: True)*: Recalculates glyf, CFF, head bounding box values,
  and hhea/vhea min/max values when saving the font.
- **\`recalc_timestamp\`** *(bool, Default: False)*: Updates the font’s modified timestamp in the
  head table when saving.

Example Usage:

```python
from io import BytesIO

from foundrytools import Font

# Loading a font from a file
font = Font("path/to/font.ttf")
print(font.file)  # Path to the file
print(font.ttfont)  # Access the underlying TTFont object

# Loading a font from BytesIO
with open("path/to/font.ttf", "rb") as f:
    font_data = BytesIO(f.read())
font = Font(font_data)
print(font.bytesio)  # BytesIO object access

# Using the class as a context manager
with Font("path/to/font.ttf") as font:
    print(font.ttfont)
```

### Core Methods and Attributes

#### Font Loading

The `_init_font` method performs automatic loading of fonts based on the `font_source` parameter.

Supported methods for loading fonts:

- `_init_from_file`: Loads from a file.
- `_init_from_bytesio`: Loads from an in-memory BytesIO object.
- `_init_from_ttfont`: Loads from an already initialized TTFont.

#### Font Tables Initialization

The `_init_tables` method initializes placeholders for various font tables, ensuring that they are
ready to be loaded when accessed. The method sets up the initial state for each table in the font.

```python
def _init_tables(self) -> None:
    """
    Initialize all font table attributes to None. This method sets up the initial state
    for each table in the font, ensuring that they are ready to be loaded when accessed.
    """
    self._cff: Optional[CFFTable] = None
    self._cmap: Optional[CmapTable] = None
    self._fvar: Optional[FvarTable] = None
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
```

#### Font Tables Access

The `_get_table` method is a private helper function within the `Font` class, designed to manage and
retrieve font table objects. It utilizes **lazy loading**, meaning that it only initializes and
loads a font table when it is explicitly requested, leading to better performance and reduced memory
usage. Below is a step-by-step explanation.

```python
TABLES_LOOKUP = {
    "CFF ": ("_cff", CFFTable),
    "cmap": ("_cmap", CmapTable),
    "fvar": ("_fvar", FvarTable),
    "GDEF": ("_gdef", GdefTable),
    "glyf": ("_glyf", GlyfTable),
    "GSUB": ("_gsub", GsubTable),
    "head": ("_head", HeadTable),
    "hhea": ("_hhea", HheaTable),
    "kern": ("_kern", KernTable),
    "hmtx": ("_hmtx", HmtxTable),
    "name": ("_name", NameTable),
    "OS/2": ("_os_2", OS2Table),
    "post": ("_post", PostTable),
}

def _get_table(self, table_tag: str):  # type: ignore
    table_attr, table_cls = TABLES_LOOKUP[table_tag]
    if getattr(self, table_attr) is None:
        if self.ttfont.get(table_tag) is None:
            raise KeyError(f"The '{table_tag}' table is not present in the font")
        setattr(self, table_attr, table_cls(self.ttfont))
    table = getattr(self, table_attr)
    if table is None:
        raise KeyError(f"An error occurred while loading the '{table_tag}' table")
    return table
```

- **Purpose**:
  - Accepts `table_tag`, a string identifier corresponding to a specific table in the font file
    (e.g., `"CFF"`, `"cmap"`, etc.).
  - Looks up `table_tag` in the `TABLES_LOOKUP` dictionary or mapping, which provides:
    - `table_attr`: The attribute name in the `Font` object where the table is stored.
    - `table_cls`: The class used to instantiate the requested table.
  - Checks if the corresponding table attribute (`table_attr`) already exists (i.e., has been
    previously loaded).
  - If it is `None`, the method proceeds to load the table.
  - Verifies whether the requested table (`table_tag`) is present in the underlying `TTFont` object
    (`self.ttfont`).
  - If the table is missing from the font file, it raises a `KeyError` to notify the caller.
  - If the table exists, it is instantiated using the corresponding table class (`table_cls`) and
    passed the `TTFont` object (`self.ttfont`) as an argument.
  - The table instance is then stored in the `Font` object as an attribute using `setattr`.
  - Retrieves the table object stored in the `Font` object after ensuring its proper initialization.
  - As a safeguard, checks if the table object is still `None`.
  - If it has not been successfully instantiated, an error is raised to indicate a failure during
    the loading process.

The `_get_table` method is commonly used in property methods of the `Font` class to provide easy
access to specific font tables. For example:

```python
@property
def t_cff_(self) -> CFFTable:
    return self._get_table("CFF ")
```

In the above code snippet:

- The `t_cff_` property calls `_get_table` with the table tag `"CFF"`.
- `_get_table` ensures that the `CFF ` table, if not already initialized, is loaded and stored in
  the `Font` object.
- The returned table object is of type `CFFTable`.
- The same pattern is followed for other tables such as `t_cmap`, `t_name`, `t_os_2`, etc.

#### Using Font Tables

Accessing font tables is straightforward using the `Font` class. For example, to access the CFF
table of a font:

```python
from foundrytools import Font

font = Font("path/to/font.otf")
cff_table = font.t_cff_
```

The `CFFTable` object is defined in the `core.tables.cff_` module and provides a wrapper around the
CFF table (i.e., a `fontTools.ttLib.tables.C_F_F_.table_C_F_F_` object), adding convenience methods
for common operations. For example:

```python
from foundrytools.core.font import Font

font = Font("path/to/font.otf")
font.t_cff_.remove_hinting()
font.t_cff_.round_coordinates()
font.save("path/to/font_2.otf")
```

Another example accessing the `name` and `OS/2` tables:

```python
from foundrytools import Font

font = Font("path/to/font.otf")
font.t_name.remove_unused_names()
font.t_name.find_replace("Old Family Name", "New Family Name")
font.t_os_2.weight_class = 400
font.t_os_2.recalc_unicode_ranges(percentage=33.0)
```

Being table classes wrappers, they provide the `table` property to access the underlying `TTFont`
table object:

```python
from foundrytools import Font

font = Font("path/to/font.otf")
font.t_name.table.getBestFamilyName()
```

Tables can also be **accessed directly**, without using the `Font` class:

```python
from fontTools.ttLib import TTFont
from foundrytools.core.tables.post import PostTable

ttfont = TTFont("path/to/font.ttf")

post = PostTable(ttfont)
post.italic_angle = 0.0
post.underline_position = -100

ttfont.save("path/to/font_2.ttf")
```

#### Supported Tables

The `Font` class provides access to various font tables through properties. The following tables are
currently supported, other tables will be added as needed:

- **CFF**: `t_cff_`
- **cmap**: `t_cmap`
- **fvar**: `t_fvar`
- **GDEF**: `t_gdef`
- **GSUB**: `t_gsub`
- **glyf**: `t_glyf`
- **head**: `t_head`
- **hhea**: `t_hhea`
- **hmtx**: `t_hmtx`
- **kern**: `t_kern`
- **name**: `t_name`
- **OS/2**: `t_os_2`
- **post**: `t_post`

### Properties

The following properties provide accessible abstractions of internal font data:

- **\`file\`**:
  - Returns the font’s file path (or `None` if not loaded from file).
  - Provides a setter to update the file path.
- **\`bytesio\`**:
  - Returns the in-memory BytesIO object containing the font data.
  - Provides a setter to update the BytesIO object.
- **\`ttfont\`**:
  - Returns the underlying TTFont representation of the font.
  - Provides a setter for replacing the TTFont object.
- **\`temp_file\`**: A placeholder for temporary file path of the font, in case it is needed for
  some operations.
- **\`is_ps\`** *(bool)*: Indicates if the font contains PostScript outlines based on
  `TTFont.sfntVersion`.
- **\`is_tt\`** *(bool)*: Indicates if the font contains TrueType outlines based on
  `TTFont.sfntVersion`.
- **\`is_woff\`** *(bool)*: Indicates if the font is in the WOFF format by checking the flavor
  attribute.
- **\`is_woff2\`** *(bool)*: Indicates if the font is in the WOFF2 format by checking the flavor
  attribute.
- **\`is_static\`** *(bool)*: Indicates if the font is a static font by checking for the absence of
  a `fvar` table.
- **\`is_variable\`** *(bool)*: Indicates if the font is a variable font by checking for the
  presence of a `fvar` table.

### Advanced Features

- **Context Management**: The Font class supports the with statement. On entering the context, it
  returns the Font instance, and upon exiting, it releases allocated resources (e.g., closing files,
  clearing temporary data).
- **Rebuilding and Reloading**:
  - `reload`: Reload the font by saving it to a temporary stream and reloading from it.
  - `rebuild`: Save the font as XML to a temporary stream and then re-import it.
- **Conversion Utilities**:
  - `to_woff`: Converts the font into WOFF format.
  - `to_woff2`: Converts the font into WOFF2 format.
  - `to_ttf`: Converts a PostScript font into TrueType.
  - `to_otf`: Converts a TrueType font into PostScript.
  - `to_sfnt`: Converts WOFF/WOFF2 fonts to SFNT format.
- **Subsetting Operations**:
  - `remove_glyphs`: Removes specified glyphs from the font.
  - `remove_unused_glyphs`: Removes glyphs that are unreachable by Unicode values or lookup rules.
- **Contours**:
  - `correct_contours`: Adjusts glyph contours for overlaps, contour direction errors, and small
    paths.
  - `scale_upm`: Scales the font’s units per em (UPM).
- **Sorting and Managing Glyph Order**:
  - `rename_glyph`: Rename specific glyphs in the font.
  - `rename_glyphs`: Renames all glyphs in the font based on a custom mapping.
  - `sort_glyphs`: Sorts glyphs based on Unicode values, alphabetical order, or design order.

### Error Handling

The Font class raises specific exceptions when invalid states or inputs are encountered, such as:

> - **\`FontError\`**: Raised when invalid font sources or errors related to glyph data occur.
> - **\`FontConversionError\`**: Raised when invalid font conversions are attempted (e.g.,
>   converting a variable font into TrueType).
