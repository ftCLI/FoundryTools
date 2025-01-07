# FoundryTools

FoundryTools is a Python library for working with font files and their data. It provides a
high-level interface for inspecting, manipulating, and converting fonts, leveraging the capabilities
of the **fontTools** library and other font-related tools, such as **AFDKO**, **cffsubr**,
**defcon**, **dehinter**, **skia-pathops**, **ttfautohint-py**, **ufo2ft**, and **ufo-extractor**.

The library is designed to simplify font processing tasks, such as reading and writing font files,
accessing font tables and metadata, modifying glyph data, and converting fonts between different
formats. It offers a set of classes and utilities for working with fonts at various levels of
abstraction, from low-level font table manipulation to high-level font inspection and conversion.

FoundryTools is intended for font developers, type designers, font engineers, and anyone working
with font files who needs a programmatic way to interact with font data. It provides a Pythonic API
for common font operations and can be used in scripts, tools, and workflows that involve font
processing.

Below is an overview of the key components and features of FoundryTools, while the detailed
documentation can be found at the following link: https://foundrytools.readthedocs.io/en/latest/

## Table of Contents

- [Installation](#installation)
  - [pip](#pip)
  - [Editable mode](#editable-mode)
- [Font Class: High-Level Wrapper for TTFont](#font-class-high-level-wrapper-for-ttfont)
  - [Overview](#overview)
  - [Features](#features)
  - [Initialization](#initialization)
    - [Font Initialization](#font-initialization)
    - [Style Flags Initialization](#style-flags-initialization)
    - [Tables Initialization](#tables-initialization)
  - [Font Tables](#font-tables)
    - [Font Tables Access](#font-tables-access)
    - [Supported Tables](#supported-tables)
  - [Style Flags](#style-flags)
  - [Properties](#properties)
  - [Advanced Features](#advanced-features)
- [FontFinder Class: Font Search and Filtering](#fontfinder-class-font-search-and-filtering)
  - [Overview](#overview-1)
  - [Features](#features-1)
  - [Constructor](#constructor)
  - [Main Methods](#main-methods)
  - [Private Methods](#private-methods)
  - [Usage](#usage)
    - [Basic Example](#basic-example)
    - [Example with Recursion and Filtering](#example-with-recursion-and-filtering)
- [The `apps` package](#the-apps-package)

## Installation

FoundryTools requires Python 3.9 or later.

### pip

FoundryTools releases are available on the Python Package Index (PyPI), so it can be installed with
[pip](https://pip.pypa.io/):

```bash
python -m pip install foundrytools
```

### Editable mode

If you would like to contribute to the development, you can clone the repository from GitHub,
install the package in 'editable' mode, and modify the source code in place. We strongly recommend
using a virtual environment.

```bash

# clone the repository:
git clone https://github.com/ftCLI/FoundryTools.git
cd foundrytools

# create new virtual environment named e.g. ftcli-venv, or whatever you prefer:
python -m venv foundrytools-venv

# to activate the virtual environment in macOS and Linux, do:
. foundrytools-venv/bin/activate

# to activate the virtual environment in Windows, do:
foundrytools-venv\Scripts\activate.bat

# install in 'editable' mode
python -m pip install -e .
```

## Font Class: High-Level Wrapper for TTFont

### Overview

The `Font` class is a high-level wrapper around the `TTFont` class from the **fontTools** library,
providing a user-friendly interface for working with font files and their data. It simplifies font
manipulation and offers various utilities for accessing and modifying font-specific properties.

### Features

- Load fonts from file paths (`str` or `Path`), `BytesIO` objects, and `TTFont` instances.
- Manipulate font tables, attributes, and metadata.
- Provides Pythonic getter and setter properties for accessing internal font data.
- Works as a context manager to automatically manage resources.

### Initialization

The class is initialized with the following parameters:

- **\`font_source\`**: A path to a font file (as `str` or `Path`), a `BytesIO` object, or an
  existing `TTFont` instance.
- **\`lazy\`** *(Optional[bool], Default: `None`)*: Controls whether font data is loaded lazily
  (on-demand) or eagerly (immediately). The default value `None` falls somewhere between.
- **\`recalc_bboxes\`** *(bool, Default: `True`)*: Recalculates glyf, CFF, head bounding box values,
  and hhea/vhea min/max values when saving the font.
- **\`recalc_timestamp\`** *(bool, Default: False)*: Updates the font’s modified timestamp in the
  head table when saving.

Example Usage:

```python
from io import BytesIO

from foundrytools import Font

# Loading a font from a file
font = Font("path/to/font.ttf")
print(font.file)  # Access the file path

# Loading a font from BytesIO
with open("path/to/font.ttf", "rb") as f:
    font_data = BytesIO(f.read())
font = Font(font_data)
print(font.bytesio)  # BytesIO object access

# Using the class as a context manager
with Font("path/to/font.ttf") as font:
    print(font.ttfont)  # Access the TTFont object
```

#### Font Initialization

The `_init_font` method performs automatic loading of fonts based on the `font_source` parameter.

Supported methods for loading fonts:

- `_init_from_file`: Loads from a file.
- `_init_from_bytesio`: Loads from an in-memory `BytesIO` object.
- `_init_from_ttfont`: Loads from an already initialized `TTFont`.

#### Style Flags Initialization

The `flags` attribute is initialized to an instance of the `StyleFlags` class, which provides
convenience methods for managing font styles. It abstracts away low-level bitwise operations on the
font tables (`OS/2` and `head`). Instead, users can interact with properties like `is_bold`,
`is_italic`, `is_regular`, `is_oblique` to check or modify the font's style easily.

```python
from foundrytools.core.font import Font

font = Font("path/to/font.ttf")
print(font.flags.is_bold)  # Check if the font is bold
font.flags.is_bold = True  # Set the font as bold
font.flags.is_italic = False  # Set the font as non-italic
font.flags.is_oblique = True  # Set the font as oblique
# The is_regular property is read-only, as it is inferred from the other style flags. To set the
# font as regular, use the set_regular method.
font.flags.set_regular()  # Set the font as regular
```

#### Tables Initialization

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

### Font Tables

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
- The returned table object is of type `CFFTable`, which is a wrapper around `Font.ttfont['CFF ']`
  table.
- The same pattern is followed for other tables such as `t_cmap`, `t_name`, `t_os_2`, etc.

Accessing font tables is straightforward using the `Font` class. For example, to access the CFF
table of a font:

```python
from foundrytools import Font

font = Font("path/to/font.otf")
cff_table = font.t_cff_
```

The `CFFTable` object is defined in the `core.tables.cff_` module and provides a wrapper around the
CFF table (i.e., a `fontTools.ttLib.tables.C_F_F_.table_C_F_F_` object), adding convenience methods
for common operations.

For example:

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

Table wrappers provide the `table` property to access the wrapped `ttLib.tables` objects.

The following lines are equivalent:

```python
font.t_name.table.getBestFamilyName()  # Access the wrapped ttLib.tables._n_a_m_e.table__n_a_m_e object

font.ttfont["name"].getBestFamilyName()  # This is equivalent to the above line
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

The following tables are currently supported, other tables will be added as needed:

- **CFF**: `t_cff_` (`CFFTable`)
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

### Style Flags

The `Font` class provides a set of style flags to simplify font style management. These flags are
used to determine the font style based on the font’s attributes, such as weight, italic, and
obliqueness.

The following style flags are available:

- **\`is_bold\`** *(bool)*:
  - Returns `True` if the font is bold based on the `OS/2` table’s and `head` table’s values.
  - Provides a setter to update the bold flag.
- **\`is_italic\`** *(bool)*:
  - Returns `True` if the font is italic based on the `OS/2` table’s and `head` table’s values.
  - Provides a setter to update the italic flag.
- **\`is_regular\`** *(bool)*:
  - Returns `True` if the font is regular based on the `OS/2` table’s and `head` table’s values.
  - This property is read-only and inferred from the other style flags. To set the font as regular,
    use the `set_regular` method.
- **\`is_oblique\`** *(bool)*:
  - Returns `True` if the font is oblique based on the `OS/2` table’s and `head` table’s values.
  - Provides a setter to update the oblique flag.

### Properties

The following properties provide accessible abstractions of internal font data:

- **\`file\`**:
  - Returns the font’s file path (or `None` if not loaded from file).
  - Provides a setter to update the file path.
- **\`bytesio\`**:
  - Returns the in-memory `BytesIO` object containing the font data.
  - Provides a setter to update the `BytesIO` object.
- **\`ttfont\`**:
  - Returns the wrapped `TTFont` object.
  - Provides a setter for replacing the `TTFont` object.
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

## FontFinder Class: Font Search and Filtering

### Overview

The `FontFinder` class is a robust Python tool designed to search for font files in a directory,
with options for filtering, customization, and recursion. It simplifies the process of finding fonts
based on specific criteria and supports the handling of single files and directories. It is
particularly useful in scenarios involving large font repositories or automated font processing
pipelines. With its built-in filtering and customization options, it provides a robust way to manage
fonts programmatically.

### Features:

- **Recursive Search**: Searches directories and subdirectories for font files.
- **Filtering**: Supports filtering by font type (TrueType/PostScript), web font flavor (`woff`,
  `woff2`), and font variations (static/variable).
- **Customizable Options**: Options for lazy processing, recalculation of timestamps, and bounding
  boxes.
- **Error Handling**: Handles invalid input paths and conflicting filter conditions.

### Constructor

#### `__init__(input_path: Path, options: Optional[FinderOptions] = None, filter_: Optional[FinderFilter] = None)`

Initializes the `FontFinder` instance.

- **Parameters**:

  - `input_path` (`Path`): The file or directory path to search for fonts.
  - `options` (`FinderOptions`): Optional class containing customizable search options. If not
    provided, defaults to sensible defaults.
  - `filter_` (`FinderFilter`): Optional class used to filter results based on font properties.

- **Key Actions**:

  - Resolves the `input_path` to an absolute path. If invalid, a `FinderError` is raised.
  - Generates filter conditions from the provided `filter_`.
  - Validates that no conflicting filters are in use.

### Main Methods

#### `find_fonts()`

Returns a **list of Fonts** that meet the specified conditions.

- **Description**: This method evaluates font files in the given path and applies the specified
  filter conditions.

- **Example**:

```python
from foundrytools.lib.font_finder import FontFinder
finder = FontFinder(input_path="path/to/fonts")
fonts = finder.find_fonts()
for font in fonts:
  print(font.file)
```

#### `generate_fonts()`

A **generator function** that yields `Font` objects one by one.

- **Purpose**: Useful when memory efficiency is critical and a large number of files are processed.

- **Yield**:

  - An object of type `Font` for each font matching the criteria.

- **Exceptions**:

  - Skips files that raise `TTLibError` or `PermissionError`.

### Private Methods

#### `_generate_files()`

Generates file paths from the given `input_path`.

- **Description**:

  - If `input_path` is a file, it yields that file.
  - If `input_path` is a directory:
    - Searches recursively (`Path.rglob("*")`) if the `recursive` option is `True`.
    - Searches non-recursively (`Path.glob("*")`) otherwise.

- **Yield**:

  - Paths to files that match the criteria.

#### `_validate_filter_conditions()`

Ensures that no conflicting filter conditions are present.

- **Raises**:
  - `FinderError` if:
    - Both TrueType (`filter_out_tt`) **and** PostScript (`filter_out_ps`) are excluded.
    - All web fonts (`woff`, `woff2`) **and** standard fonts (`sfnt`) are excluded.
    - Both static **and** variable fonts are excluded.

#### `_generate_filter_conditions(filter_: FinderFilter)`

Converts the provided `FinderFilter` into executable filter conditions.

- **Parameters**:

  - `filter_`: Instance of `FinderFilter`.

- **Returns**:

  - A list of tuples, where each tuple consists of:
    1. A boolean indicating whether the filter is enabled.
    1. A callable function that checks a font property.

### Usage

#### Basic Example:

```python
from foundrytools.lib.font_finder import FontFinder

# Path to process
path = "path/to/fonts/"

# Initialize FontFinder with default options
finder = FontFinder(input_path=path)

# Find fonts
fonts = finder.find_fonts()

# Process fonts
for font in fonts:
    print(font)
```

#### Example with Recursion and Filtering:

```python
from foundrytools.lib.font_finder import FontFinder, FinderOptions, FinderFilter
options = FinderOptions(recursive=True, lazy=True)
filter_ = FinderFilter(filter_out_tt=True, filter_out_woff=True)

finder = FontFinder(input_path="path/to/fonts", options=options, filter_=filter_)

for font in finder.generate_fonts():
    print(font.file)
```

## The `apps` package

The `apps` package contains pre-built applications that leverage the `Font` class and other
utilities provided by FoundryTools. These applications are designed to perform specific font
processing tasks, such as fixing errors, autohinting, and more.

Please refer to the individual modules within the `apps` package for detailed information on each
application.

An example of using the `fix_italic_angle` application:

```python
from foudrytools.lib.font_finder import FontFinder
from foundrytools.apps.fix_italic_angle import run as fix_italic_angle

finder = FontFinder(input_path="path/to/fonts")
fonts = finder.find_fonts()

for font in fonts:
    fix_italic_angle(font)
    font.save(font.file.with_name(f"{font.file.stem}_fixed.ttf"))
```
