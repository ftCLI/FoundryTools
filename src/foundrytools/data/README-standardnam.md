# FontLab 7 standard.nam

## License

Copyright (c) 2001-2020, Fontlab Ltd. Copyright (c) 2016, LettError and Erik van Blokland,
TypeMyType and Frederik Berlaen

All rights reserved.

Redistribution and use in source and binary forms, with or without modification, are permitted
provided that the following conditions are met:

1. Redistributions of source code must retain the above copyright notice, this list of conditions
   and the following disclaimer.

1. Redistributions in binary form must reproduce the above copyright notice, this list of conditions
   and the following disclaimer in the documentation and/or other materials provided with the
   distribution.

1. Neither the name of the copyright holder nor the names of its contributors may be used to endorse
   or promote products derived from this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR
IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND
FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR
CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER
IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF
THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

Copyright 2002-2019 Adobe (http://www.adobe.com/).

Redistribution and use in source and binary forms, with or without modification, are permitted
provided that the following conditions are met:

Redistributions of source code must retain the above copyright notice, this list of conditions and
the following disclaimer.

Redistributions in binary form must reproduce the above copyright notice, this list of conditions
and the following disclaimer in the documentation and/or other materials provided with the
distribution.

Neither the name of Adobe nor the names of its contributors may be used to endorse or promote
products derived from this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR
IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND
FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR
CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER
IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF
THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

Copyright (c) 2016 Georg Seifert

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and
associated documentation files (the "Software"), to deal in the Software without restriction,
including without limitation the rights to use, copy, modify, merge, publish, distribute,
sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial
portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT
NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES
OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

## Readme

Version 4.3.0 / 2020-07-26

This nametable requires FontLab 7 or higher. It uses new syntax:

- names without prefix are used as production, friendly and alternative names
- names with `>` prefix are used as friendly and alternative names
- names with `<` prefix are used as alternative names
- names with `!` prefix are used as synonyms

This table includes data from

- https://github.com/adobe-type-tools/agl-aglfn/
- https://github.com/LettError/glyphNameFormatter
- https://github.com/schriftgestalt/GlyphsInfo

and hand-curated data compiled by FontLab. Algorithmic names (`uniXXXX`, `uXXXX` and `uXXXXX`) are
not included.

Production names are compatible with the Adobe Glyph List for New Fonts (AGLFN) v1.7, with some
exceptions:

| Unicode | Friendly | Production | |:--------|:--------------|:--------------| | 0x00B2 |
twosuperior | twosuperior | | 0x00B3 | threesuperior | threesuperior | | 0x00B5 | micro | uni00B5 |
| 0x00B9 | onesuperior | onesuperior | | 0x0394 | Delta | uni0394 | | 0x03A9 | Omega | uni03A9 | |
0x03BC | mu | uni03BC | | 0x2126 | Ohm | uni2126 | | 0x2206 | increment | uni2206 | | 0xFB00 | f_f |
f_f | | 0xFB01 | fi | fi | | 0xFB02 | fl | fl | | 0xFB03 | f_f_i | f_f_i | | 0xFB03 | f_f_i | f_f_i
| | 0xFB04 | f_f_l | f_f_l | | 0xFB04 | f_f_l | f_f_l | | 0xFB05 | longs_t | longs_t | | 0xFB06 |
s_t | s_t |

For 0x250C-0x256A, it does not use the `SF` names as production names.

## Changes

### 4.4.2 / 2020-09-28

- Bugfix

### 4.4.0 / 2020-09-25

- Updated Friendly and Alternate names
- Added synonyms

### 4.3.1 / 2020-07-26

- Resolved some contradictions between Friendly and Alternate names
- 13 names which previously were Alternative names are now also Friendly names: `Ismall` U+026A,
  `phimod` U+1D60, `ustroke` U+1D7E, `phiModifier-latin` U+1DB2, `bellsymbol` U+237E,
  `firstQuarterMoon` U+263D, `lastQuarterMoon` U+263E, `cross` U+271D, `crossMark` U+274C, `Gscript`
  U+A7AC, `Ismall-latin` U+A7AE, `firstQuarterMoonSymbol` U+1F313, `lastQuarterMoonSymbol` U+1F317
- `prime` is now synonym for U+2032, not U+02B9
- Glagollitic Friendly names now use Alternative-style names
- more Arabic names prefer Alternative style
- added 651 names:
  - some Cyrillic synonyms
  - synonyms for Bengali, Devanagari, Gujarati, Gurmukhi, Kannada and Tamil
  - Javanese names with `-java` suffix
  - Bhaiksuki names with `-bkhs` suffix
  - Marchen names with `-marc` suffix
- 53,102 entries

### 4.2.0 / 2020-02-23

- unified inconsistent Arabic naming to prefer Alternative-style names
- added Friendly names for Unicode 12.1.0
- additional names from https://github.com/schriftgestalt/GlyphsInfo
- added 'uniXXXX.suf'-style synonyms for Arabic presentational forms
- 52,326 entries

### 4.1.0 / 2019-12-12

- updated names from https://github.com/LettError/glyphNameFormatter primarily for math
- 47,119 entries

### 4.0.0 / 2019-10-14

- new syntax
- hand-editing
- changes in handling Omega/Ohm, Delta/increment, mu/micro
- includes names from https://github.com/LettError/glyphNameFormatter
- includes names from https://github.com/schriftgestalt/GlyphsInfo
- 46,127 entries

### 3.3.2

- Removed 0x04A8 !Ohook (was duplicate with 0x1ECE !Ohook)
- Removed 0x04A9 !ohook (was duplicate with 0x1ECF !ohook)

### 3.3.1

- Added 0x213B !facsimile

### 3.3.0

- Removed \*small glyphs

### 3.2.0

- Fixes in Katakana phonetic extensions, enclosed CJK letters and months

### 3.1.0

- new synonyms

### 3.0.0

- documentation updates

### 2.8.0

- in-sync with AGLFN 1.7
- for improved Mac OS X 10.4 compatibility:

```txt
0x0122 !Gcommaaccent
0x0123 !gcommaaccent
0x0136 !Kcommaaccent
0x0137 !kcommaaccent
0x013B !Lcommaaccent
0x013C !lcommaaccent
0x0145 !Ncommaaccent
0x0146 !ncommaaccent
0x0156 !Rcommaaccent
0x0157 !rcommaaccent
0x0162 !Tcommaaccent
0x0163 !tcommaaccent
0x0218 !Scommaaccent
0x0219 !scommaaccent
```

### 2.7.7

- 0x05D5 !vav (added in all files)

### 2.7.5

- 0x012A Imacron (added in all files)
- 0x012D ibreve (added in all files)
