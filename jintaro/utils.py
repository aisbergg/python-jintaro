from pathlib import Path


def merge_dicts(x, y):
    """Recursively merges two dicts.

    When keys exist in both the value of 'y' is used.

    Args:
        x (dict): First dict
        y (dict): Second dict

    Returns:
        dict: The merged dict
    """
    if x is None and y is None:
        return {}
    if x is None:
        return y
    if y is None:
        return x

    merged = dict(x, **y)
    xkeys = x.keys()

    for key in xkeys:
        if type(x[key]) is dict and key in y:
            merged[key] = merge_dicts(x[key], y[key])
    return merged


def read_file(path):
    if isinstance(path, str):
        path = Path(path)
    check_file(path)
    with path.open("r") as f:
        file_content = f.read()
    return file_content


def check_file(path):
    """Check a file for existence and stuffer

    Args:
        path (pathlib.Path): File to check.

    Raises:
        FileNotFoundError: If file does not exist.
        OSError: If path is either not a file or is a binary file.
    """
    if isinstance(path, str):
        path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Given file '{path}' doesn't exist")
    if not path.is_file():
        raise OSError(f"Given path '{path}' is not a file")
    if is_binary(path):
        raise OSError("Given path '{path}' is a binary file")


def is_binary(path):
    """Return true if the given filename is binary.

    Args:
        path (pathlib.Path): File to check

    Returns:
        bool: True if file appears to be binary, False otherwise
    """
    with path.open("rb") as f:
        chunk = f.read(8000)
        if b"\0" in chunk:
            return True

    return False
