from pathlib import Path
from typing import Union, Any


def merge_dicts(x: dict, y: dict) -> dict:
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


def read_file(path: Union[Path, str]) -> str:
    if isinstance(path, str):
        path = Path(path)
    check_file(path)
    with path.open("r") as f:
        file_content = f.read()
    return file_content


def check_file(path: Union[Path, str], binary=False) -> None:
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
    if binary and not is_binary(path):
        raise OSError(f"Given file '{path}' is supposed to be a binary file, but it seems to be a text file")
    if not binary and is_binary(path):
        raise OSError(f"Given file '{path}' is supposed to be a text file, but it seems to be binary")


def is_binary(path: Union[Path, str]) -> bool:
    """Return true if the given filename is binary.

    Args:
        path (pathlib.Path): File to check

    Returns:
        bool: True if file appears to be binary, False otherwise
    """
    if isinstance(path, str):
        path = Path(path)
    with path.open("rb") as f:
        chunk = f.read(8000)
        if b"\0" in chunk:
            return True

    return False


class Property(object):

    @staticmethod
    def get(obj: dict, path: str, default: Any = None, exception: Union[Exception, None] = None):
        value = obj
        for key in path.split('.'):
            if isinstance(value, dict):
                if key in value:
                    value = value[key]
                elif default is not None:
                    value = default
                else:
                    raise exception(f"Unknown option '{path}'")
            elif isinstance(value, list):
                try:
                    key = int(key)
                    value = value[key]
                except (ValueError, IndexError):
                    if default is not None:
                        value = default
                    else:
                        raise exception(f"Unknown option '{path}'")  #pylint: disable=raise-missing-from
            else:
                if hasattr(value, key):
                    value = getattr(value, key)
                elif default is not None:
                    value = default
                else:
                    raise exception(f"Unknown option '{path}'")
        return value

    @staticmethod
    def set(obj: dict, path: str, value: Any) -> None:
        assert isinstance(path, str) and len(path) > 0

        full_path = path.split('.')
        parent = full_path[:-1]
        key = full_path[-1]

        last_branch = obj
        for p in parent:
            if not (p in last_branch and isinstance(last_branch[p], dict)):
                last_branch[p] = {}
            last_branch = last_branch[p]

        last_branch[key] = value
