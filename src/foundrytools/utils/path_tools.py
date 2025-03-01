"""Miscellaneous path tools."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path


def get_temp_file_path(directory: str | Path | None = None) -> Path:
    """
    Return a temporary file path.

    :param directory: The directory to create the temporary file in.
    :type directory: Optional[Union[str, Path]]
    :return: The temporary file path.
    :rtype: Path
    """
    if directory and not Path(directory).is_dir():
        msg = f"{directory} is not a directory."
        raise NotADirectoryError(msg)
    file_descriptor, path = tempfile.mkstemp(dir=directory)
    os.close(file_descriptor)
    return Path(path)
