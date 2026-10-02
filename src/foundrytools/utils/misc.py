from collections.abc import Iterator
from contextlib import contextmanager

from fontTools.ttLib import TTFont


@contextmanager
def restore_flavor(font: TTFont) -> Iterator[None]:
    """
    This context manager is used to temporarily set the font flavor to None and restore it after
    operations that require the flavor to be None (e.g.: subroutinization or desubroutinization).

    :param font: The TTFont object.
    :type font: TTFont
    :return: A generator that yields.
    :rtype: Iterator[None]
    """
    original_flavor = font.flavor
    font.flavor = None
    try:
        yield
    finally:
        font.flavor = original_flavor
