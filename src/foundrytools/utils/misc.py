"""Miscellaneous library code."""

from collections.abc import Iterator
from contextlib import contextmanager

from fontTools.ttLib import TTFont


@contextmanager
def restore_flavor(font: TTFont) -> Iterator[None]:
    """
    Temporarily set the font flavor to None.

    Restores it after operations that require the flavor to be None
    (e.g.: subroutinization or desubroutinization).

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
