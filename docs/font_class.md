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

**Font Loading**

The \_init_font method performs automatic loading of fonts based on the font_source parameter.

Supported methods for loading fonts:

- \_init_from_file: Loads from a file.
- \_init_from_bytesio: Loads from an in-memory BytesIO object.
- \_init_from_ttfont: Loads from an already initialized TTFont.

**Table Initialization**

The \_init_tables method initializes placeholders for various font tables (glyphs, metadata, etc.).
As for now, the following tables are supported (others will be added as needed):

- CFF -> t_cff\_
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

The `_get_table()` method dynamically retrieves specific font tables by their tags (e.g., ‘CFF ’,
‘glyf’, ‘head’, ‘OS/2’) when needed.

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
- **Glyph Operations**:
  - `get_glyph_bounds`: Retrieves glyph boundary coordinates for a given glyph name.
  - `remove_unused_glyphs`: Removes glyphs that are unreachable by Unicode values or lookup rules.
- **Contours**:
  - `correct_contours`: Adjusts glyph contours for overlaps, contour direction errors, and small
    paths.
  - `scale_upm`: Scales the font’s units per em (UPM).
- **Sorting and Managing Glyph Order**:
  - `rename_glyph`: Rename specific glyphs in the font.
  - `sort_glyphs`: Sorts glyphs based on Unicode values, alphabetical order, or custom design order.
  - `rename_glyphs`: Renames multiple glyphs in the font to match new glyph orderings.

### Error Handling

The Font class raises specific exceptions when invalid states or inputs are encountered, such as:

> - **\`FontError\`**: Raised when invalid font sources or errors related to glyph data occur.
> - **\`FontConversionError\`**: Raised when invalid font conversions are attempted (e.g.,
>   converting a variable font into TrueType).
