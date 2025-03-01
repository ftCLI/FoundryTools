import importlib.metadata

from foundrytools.core import tables
from foundrytools.core.font import Font
from foundrytools.lib.font_finder import FontFinder

try:
    __version__ = importlib.metadata.version(__name__)
except importlib.metadata.PackageNotFoundError:
    __version__ = "0.0.0"

VERSION = __version__
__all__ = ["VERSION", "Font", "tables", "FontFinder"]
