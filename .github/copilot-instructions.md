# Repository guidance

## Project overview

FoundryTools is a Python 3.11+ library built on `fontTools` for inspecting, editing, and converting
OpenType fonts.

- `src/foundrytools/core/font.py` defines `Font`, the high-level wrapper around `fontTools.ttLib.TTFont`.
  It accepts font paths, in-memory streams, or existing `TTFont` objects and centralizes font
  properties, editing, saving, and conversions.
- `src/foundrytools/core/tables/` contains wrappers for supported font tables. `TABLES_LOOKUP` maps
  OpenType table tags to wrapper classes; `Font` loads these wrappers lazily. Each wrapper exposes
  the underlying fontTools table through `.table`.
- `src/foundrytools/app/` contains higher-level font operations, generally exposed as `run(...)`
  functions that operate on a `Font`.
- `src/foundrytools/lib/` and `src/foundrytools/utils/` provide shared font-building, path, glyph,
  and bit-manipulation helpers. `FontFinder` is in `lib/font_finder.py`.

## Build, checks, and documentation

Use `uv` and the checked-in `uv.lock` to manage the environment. Install development dependencies
with `uv sync --group dev`.

The CI checks are:

```powershell
uv run ruff check .
uv run ruff format --check .
uv run mypy src
```

To check a single Python file with Ruff:

```powershell
uv run ruff check src/foundrytools/core/font.py
uv run ruff format --check src/foundrytools/core/font.py
```

Security checks require the `security` dependency group:

```powershell
uv sync --only-group security
uv run bandit -r src
uv run pip-audit
```

Build a package with `uv build`. To build the Sphinx documentation, install its optional
dependencies with `uv sync --group docs`, then run:

```powershell
uv run sphinx-build -b html docs docs/_build/html
```

There is currently no tracked test suite or configured test command in the repository.

## Codebase conventions

- Target Python 3.11 and keep lines within 100 characters. Ruff handles linting and formatting;
  its configured rules include pyflakes, import sorting, pyupgrade, bugbear, comprehensions, and
  simplify checks.
- Keep public and internal function definitions fully typed; Mypy enforces `disallow_untyped_defs`
  for `src`.
- Reuse the table-tag constants in `foundrytools.constants` and register new table wrappers in
  `core/tables/__init__.py`'s `TABLES_LOOKUP` so `Font` can expose them using its established lazy
  table-access pattern.
- Table wrappers should follow the existing `DefaultTbl` pattern: retain the owning `TTFont`, expose
  the wrapped object as `.table`, and implement table-specific helpers in the relevant module.
- Font operations in `app/` work through the shared `Font` abstraction rather than duplicating font
  loading and table access. Use operation-specific exceptions where the existing module defines
  them.
- Keep API documentation in the Sphinx sources under `docs/`; public API changes should align with
  the documented `Font` and table-wrapper interfaces in `README.md`.
