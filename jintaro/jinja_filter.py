""" Custom Jinja2 filters """
import re
from distutils.util import strtobool

from jinja2 import StrictUndefined, UndefinedError


def regex_escape(string):
    """Escape special characters in a string so it can be used in regular expressions"""
    return re.escape(string)


def regex_findall(value, pattern, ignorecase=False, multiline=False):
    """Do a regex findall on 'value'"""
    flags = 0
    if ignorecase:
        flags |= re.I
    if multiline:
        flags |= re.M
    compiled_pattern = re.compile(pattern, flags=flags)
    return compiled_pattern.findall(str(value))


def regex_replace(value, pattern, replacement, ignorecase=False, multiline=False):
    """Do a regex search and replace on 'value'"""
    flags = 0
    if ignorecase:
        flags |= re.I
    if multiline:
        flags |= re.M
    compiled_pattern = re.compile(pattern, flags=flags)
    return compiled_pattern.sub(replacement, str(value))


def regex_search(value, pattern, *args, **kwargs):
    """Do a regex search on 'value'"""
    groups = []
    for arg in args:
        match = re.match(r'\\(\d+)', arg)
        if match:
            groups.append(int(match.group(1)))
            continue

        match = re.match(r'^\\g<(\S+)>', arg)
        if match:
            groups.append(match.group(1))
            continue

        raise Exception("Unknown argument: '{}'".format(str(arg)))

    flags = 0
    if kwargs.get('ignorecase'):
        flags |= re.I
    if kwargs.get('multiline'):
        flags |= re.M
    compiled_pattern = re.compile(pattern, flags=flags)
    match = re.search(compiled_pattern, str(value))

    if match:
        if not groups:
            return match.group()
        else:
            items = []
            for item in groups:
                items.append(match.group(item))
            return items


def regex_contains(value, pattern, ignorecase=False, multiline=False):
    """Search the 'value' for 'pattern' and return True if at least one match was found"""
    match = regex_search(value, pattern, ignorecase=ignorecase, multiline=multiline)
    if match:
        return True
    else:
        return False


def to_bool(string, default_value=None):
    """Convert a string representation of a boolean value to an actual bool

    Args:
        string (str): A string to be converted to bool
        default_value: Default value when 'string' is not an boolean value

    Returns:
        bool: Converted string

    """
    try:
        return bool(strtobool(string.strip()))
    except ValueError:
        if default_value is not None:
            return default_value
        else:
            raise ValueError("'{0}' is not a boolean value".format(string.strip()))


# register the filters
FILTERS = {
    'regex_escape': regex_escape,
    'regex_findall': regex_findall,
    'regex_replace': regex_replace,
    'regex_search': regex_search,
    'regex_contains': regex_contains,
    'bool': to_bool,
}
