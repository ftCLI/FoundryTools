import os
import tempfile
from pathlib import Path


def get_temp_file_path(directory: str | Path | None = None) -> Path:
    """
    Returns a temporary file path.

    :param directory: The directory to create the temporary file in.
    :type directory: str | Path | None
    :return: The temporary file path.
    :rtype: Path
    """
    if directory and not Path(directory).is_dir():
        raise NotADirectoryError(f"{directory} is not a directory.")
    file_descriptor, path = tempfile.mkstemp(dir=directory)
    os.close(file_descriptor)
    return Path(path)
