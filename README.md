# FoundryTools

FoundryTools is a Python library for working with font files and their data. It provides a
high-level interface for inspecting, manipulating, and converting fonts, leveraging the
capabilities of the **fontTools** library and other font-related tools, such as **AFDKO**,
**cffsubr**, **defcon**, **dehinter**, **skia-pathops**, **ttfautohint-py**, **ufo2ft**, and
**ufo-extractor**.

The library is designed to simplify font processing tasks, such as reading and writing font
files, accessing font tables and metadata, modifying glyph data, and converting fonts between
different formats. It offers a set of classes and utilities for working with fonts at various
levels of abstraction, from low-level font table manipulation to high-level font inspection and
conversion.

- [Font Class: High-Level Wrapper for TTFont](#font-class-high-level-wrapper-for-ttfont)
  - [Overview](#overview)
  - [Features](#features)
  - [Initialization](#initialization)
  - [Core Methods and Attributes](#core-methods-and-attributes)
  - [Properties](#properties)
  - [Advanced Features](#advanced-features)
  - [Error Handling](#error-handling)
- [FontFinder Class Documentation](#fontfinder-class-documentation)
  - [Overview](#overview-1)
  - [Constructor](#constructor-1)
  - [Main Methods](#main-methods-1)
  - [Private Methods](#private-methods)
  - [Usage](#usage)
  - [Error Handling](#error-handling-1)
  - [Dependencies](#dependencies)


## Installation

FoundryTools requires Python 3.9 or later.

### pip

FoundryTools releases are available on the Python Package Index (PyPI), so it can be installed
with [pip](https://pip.pypa.io/):

```bash
python -m pip install foundrytools
```

### Editable mode

If you would like to contribute to the development, you can clone the repository from GitHub,
install the package in 'editable' mode, and modify the source code in place. We strongly
recommend using a virtual environment.

```bash
  
# clone the repository:
git clone https://github.com/ftCLI/FoundryTools.git
cd foundrytools

# create new virtual environment named e.g. ftcli-venv, or whatever you prefer:
python -m venv ftcli-venv

# to activate the virtual environment in macOS and Linux, do:
. ftcli-venv/bin/activate

# to activate the virtual environment in Windows, do:
ftcli-venv\Scripts\activate.bat

# install in 'editable' mode
python -m pip install -e .
```

## Font Class: High-Level Wrapper for TTFont

### Overview

The ``Font`` class is a high-level wrapper around the ``TTFont`` class from the
**fontTools** library, providing a user-friendly interface for working with font files and their
data. It simplifies font manipulation and offers various utilities for accessing and modifying
font-specific properties.

### Features

- Load fonts from multiple sources including file paths, BytesIO objects, and TTFont instances.
- Manipulate font tables, attributes, and metadata.
- Provides Pythonic getter and setter properties for accessing internal font data.
- Works as a context manager to automatically manage resources.

### Initialization

The class is initialized with the following parameters:

- **\`font_source\`**:
  A path to a font file (as `str` or `Path`), a `BytesIO` object, or an existing TTFont
  instance.
- **\`lazy\`**  *(Optional[bool], Default: None)*: Controls whether font data is loaded lazily
  (on-demand) or eagerly (immediately). The default value None falls somewhere between.
- **\`recalc_bboxes\`**  *(bool, Default: True)*:
  Recalculates glyf, CFF, head bounding box values, and hhea/vhea min/max values when
  saving the font.
- **\`recalc_timestamp\`**  *(bool, Default: False)*:
  Updates the font’s modified timestamp in the head table when saving.

Example Usage:

```python
from io import BytesIO

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

**Font Loading**

The \_init_font method performs automatic loading of fonts based on the font_source parameter.

Supported methods for loading fonts:
- \_init_from_file: Loads from a file.
- \_init_from_bytesio: Loads from an in-memory BytesIO object.
- \_init_from_ttfont: Loads from an already initialized TTFont.

**Table Initialization**

The \_init_tables method initializes placeholders for various font tables (glyphs, metadata, etc.).
As for now, the following tables are supported (others will be added as needed):

- CFF -> t_cff_
- cmap -> t_cmap
- fvar -> t_fvar
- GDEF -> t_gdef
- GSUB -> t_gsub
- glyf -> t_glyf
- head -> t_head
- hhea -> t_hhea
- hmtx -> t_hmtx
- kern -> t_kern
- name -> t_name
- OS/2 -> t_os_2
- post -> t_post

These are lazy-loaded to ensure efficient memory usage.

**Table Access**

The \_get_table method dynamically retrieves specific font tables by their tags (e.g., ‘glyf’,
‘head’) when needed.

If the table does not exist or can’t be loaded, it raises a KeyError.

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
- **\`is_ps\`**  *(bool)*:
  Indicates if the font contains PostScript outlines based on TTFont.sfntVersion.
- **\`is_tt\`**  *(bool)*:
  Indicates if the font contains TrueType outlines based on TTFont.sfntVersion.
- **\`is_woff\`**  *(bool)*:
  Indicates if the font is in the WOFF format by checking the flavor attribute.
- **\`is_woff2\`**  *(bool)*:
  Indicates if the font is in the WOFF2 format by checking the flavor attribute.
- **\`is_static\`**  *(bool)*:
  Indicates if the font is a static font by checking for the absence of an fvar table.
- **\`is_variable\`**  *(bool)*:
  Indicates if the font is a variable font by checking for the presence of an fvar table.

### Advanced Features

- **Context Management**: The Font class supports the with statement. On entering the context,
  it returns the Font instance, and upon exiting, it releases allocated resources (e.g., closing
  files, clearing temporary data).
- **Rebuilding and Reloading**:
  - reload: Reload the font by saving it to a temporary stream and reloading from it.
  - rebuild: Save the font as XML to a temporary stream and then re-import it.
- **Conversion Utilities**:
  - to_woff: Converts the font into WOFF format.
  - to_woff2: Converts the font into WOFF2 format.
  - to_ttf: Converts a PostScript font into TrueType.
  - to_otf: Converts a TrueType font into PostScript.
  - to_sfnt: Converts WOFF/WOFF2 fonts to SFNT format.
- **Glyph Operations**:
  - get_glyph_bounds: Retrieves glyph boundary coordinates for a given glyph name.
  - remove_unused_glyphs: Removes glyphs that are unreachable by Unicode values or lookup rules.
- **Contours**:
  - correct_contours: Adjusts glyph contours for overlaps, contour direction errors, and small
    paths.
  - scale_upm: Scales the font’s units per em (UPM).
- **Sorting and Managing Glyph Order**:
  - rename_glyph: Rename specific glyphs in the font.
  - sort_glyphs: Sorts glyphs based on Unicode values, alphabetical order, or custom design order.
  - rename_glyphs: Renames multiple glyphs in the font to match new glyph orderings.

### Error Handling

The Font class raises specific exceptions when invalid states or inputs are encountered, such as:

> - **\`FontError\`**: Raised when invalid font sources or errors related to glyph data occur.
> - **\`FontConversionError\`**: Raised when invalid font conversions are attempted (e.g., converting
>   a variable font into TrueType).

## FontFinder Class: Font Search and Filtering

The `FontFinder` class is a robust Python tool designed to search for font files in a directory,
with options for filtering, customization, and recursion. It simplifies the process of finding fonts
based on specific criteria and supports the handling of single files and directories.

### Overview

The `FontFinder` class can search for fonts in a given path, handling both directories and individual font files. The user can specify filters to exclude certain font types, flavors, or variations.

### Features:
- **Recursive Search**: Searches directories and subdirectories for font files.
- **Filtering**: Supports filtering by font type (TrueType/PostScript), web font flavor (`woff`, `woff2`), and font variations (static/variable).
- **Customizable Options**: Options for lazy processing, recalculation of timestamps, and bounding boxes.
- **Error Handling**: Handles invalid input paths and conflicting filter conditions.

---

## Constructor

### `__init__(input_path: Path, options: Optional[FinderOptions] = None, filter_: Optional[FinderFilter] = None)`

Initializes the `FontFinder` instance.

- **Parameters**:
  - `input_path` (`Path`): The file or directory path to search for fonts.
  - `options` (`FinderOptions`): Optional class containing customizable search options. If not provided, defaults to sensible defaults.
  - `filter_` (`FinderFilter`): Optional class used to filter results based on font properties.

- **Key Actions**:
  - Resolves the `input_path` to an absolute path. If invalid, a `FinderError` is raised.
  - Generates filter conditions from the provided `filter_`.
  - Validates that no conflicting filters are in use.

---

## Main Methods

### `find_fonts()`

Returns a **list of Fonts** that meet the specified conditions.

- **Description**:
  This method evaluates font files in the given path and applies the specified filter conditions.

- **Example**:
    ```python
    fonts = font_finder.find_fonts()
    for font in fonts:
        print(font.name)
    ```

---

### `generate_fonts()`

A **generator function** that yields `Font` objects one by one.

- **Purpose**:
  Useful when memory efficiency is critical and a large number of files are processed.

- **Yield**:
  - An object of type `Font` for each font matching the criteria.

- **Exceptions**:
  - Skips files that raise `TTLibError` or `PermissionError`.

---

## Private Methods

### `_generate_files()`

Generates file paths from the given `input_path`.

- **Description**:
  - If `input_path` is a file, it yields that file.
  - If `input_path` is a directory:
    - Searches recursively (`Path.rglob("*")`) if the `recursive` option is `True`.
    - Searches non-recursively (`Path.glob("*")`) otherwise.

- **Yield**:
  - Paths to font files.

---

### `_validate_filter_conditions()`

Ensures that no conflicting filter conditions are present.

- **Raises**:
  - `FinderError` if:
    - Both TrueType (`filter_out_tt`) **and** PostScript (`filter_out_ps`) are excluded.
    - All web fonts (`woff`, `woff2`) **and** standard fonts (`sfnt`) are excluded.
    - Both static **and** variable fonts are excluded.

---

### `_generate_filter_conditions(filter_: FinderFilter)`

Converts the provided `FinderFilter` into executable filter conditions.

- **Parameters**:
  - `filter_`: Instance of `FinderFilter`.

- **Returns**:
  - A list of tuples, where each tuple consists of:
    1. A boolean indicating whether the filter is enabled.
    2. A callable function that checks a font property.

---

## Usage

### Basic Example:

```python
from font_finder import FontFinder, FinderOptions, FinderFilter

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

### Example with Recursion and Filtering:

```python
options = FinderOptions(recursive=True, lazy=True)
filter_ = FinderFilter(filter_out_tt=True, filter_out_woff=True)

finder = FontFinder(input_path="path/to/fonts", options=options, filter_=filter_)

for font in finder.generate_fonts():
    print(font.name)
```

---

## Error Handling

### `FinderError`

Raised for:
1. Invalid paths (e.g., non-existent files or directories).
2. Conflicting filter conditions (e.g., excluding both static and variable fonts).

### Other Exceptions:
- `TTLibError`: Related to font processing, typically skipped during generation.

---

## Dependencies

This class depends on the following:
- **Python `pathlib`**: For handling file paths.
- **FontTools**: To process font files (e.g., `Font` class).
- **Optional Libraries**: FontTools `TTLibError` for error handling.

Make sure to install these dependencies before using `FontFinder`.

---

## FontFinder Class Documentation

The `FontFinder` class is a robust Python tool designed to search for font files in a directory, with options for filtering, customization, and recursion. It simplifies the process of finding fonts based on specific criteria and supports the handling of single files and directories.

### Overview

The `FontFinder` class can search for fonts in a given path, handling both directories and individual font files. The user can specify filters to exclude certain font types, flavors, or variations.

### Features:
- **Recursive Search**: Searches directories and subdirectories for font files.
- **Filtering**: Supports filtering by font type (TrueType/PostScript), web font flavor (`woff`, `woff2`), and font variations (static/variable).
- **Customizable Options**: Options for lazy processing, recalculation of timestamps, and bounding boxes.
- **Error Handling**: Handles invalid input paths and conflicting filter conditions.

---

### Constructor

#### `__init__(input_path: Path, options: Optional[FinderOptions] = None, filter_: Optional[FinderFilter] = None)`

Initializes the `FontFinder` instance.

- **Parameters**:
  - `input_path` (`Path`): The file or directory path to search for fonts.
  - `options` (`FinderOptions`): Optional class containing customizable search options. If not provided, defaults to sensible defaults.
  - `filter_` (`FinderFilter`): Optional class used to filter results based on font properties.

- **Key Actions**:
  - Resolves the `input_path` to an absolute path. If invalid, a `FinderError` is raised.
  - Generates filter conditions from the provided `filter_`.
  - Validates that no conflicting filters are in use.

---

### Main Methods

#### `find_fonts()`

Returns a **list of Fonts** that meet the specified conditions.

- **Description**:
  This method evaluates font files in the given path and applies the specified filter conditions.

- **Example**:
    ```python
    fonts = font_finder.find_fonts()
    for font in fonts:
        print(font.name)
    ```

---

#### `generate_fonts()`

A **generator function** that yields `Font` objects one by one.

- **Purpose**:
  Useful when memory efficiency is critical and a large number of files are processed.

- **Yield**:
  - An object of type `Font` for each font matching the criteria.

- **Exceptions**:
  - Skips files that raise `TTLibError` or `PermissionError`.

---

### Private Methods

#### `_generate_files()`

Generates file paths from the given `input_path`.

- **Description**:
  - If `input_path` is a file, it yields that file.
  - If `input_path` is a directory:
    - Searches recursively (`Path.rglob("*")`) if the `recursive` option is `True`.
    - Searches non-recursively (`Path.glob("*")`) otherwise.

- **Yield**:
  - Paths to font files.

---

#### `_validate_filter_conditions()`

Ensures that no conflicting filter conditions are present.

- **Raises**:
  - `FinderError` if:
    - Both TrueType (`filter_out_tt`) **and** PostScript (`filter_out_ps`) are excluded.
    - All web fonts (`woff`, `woff2`) **and** standard fonts (`sfnt`) are excluded.
    - Both static **and** variable fonts are excluded.

---

#### `_generate_filter_conditions(filter_: FinderFilter)`

Converts the provided `FinderFilter` into executable filter conditions.

- **Parameters**:
  - `filter_`: Instance of `FinderFilter`.

- **Returns**:
  - A list of tuples, where each tuple consists of:
    1. A boolean indicating whether the filter is enabled.
    2. A callable function that checks a font property.

---

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

---

### Error Handling

#### `FinderError`

Raised for:
1. Invalid paths (e.g., non-existent files or directories).
2. Conflicting filter conditions (e.g., excluding both static and variable fonts).

#### Other Exceptions:
- `TTLibError`: Related to font processing, typically skipped during generation.

---

### Dependencies

This class depends on the following:
- **Python `pathlib`**: For handling file paths.
- **FontTools**: To process font files (e.g., `Font` class).
- **Optional Libraries**: FontTools `TTLibError` for error handling.

Make sure to install these dependencies before using `FontFinder`.

---

## Conclusion

The `FontFinder` class is a versatile tool for managing and filtering font files efficiently. It is
particularly useful in scenarios involving large font repositories or automated font processing
pipelines. With its built-in filtering and customization options, it provides a robust way to manage
fonts programmatically.
