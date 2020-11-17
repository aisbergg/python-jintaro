from ast import literal_eval
from collections.abc import MutableMapping
from distutils.util import strtobool

from jinja2.defaults import (BLOCK_START_STRING, COMMENT_START_STRING, VARIABLE_START_STRING)
from jinja2.runtime import StrictUndefined

from jintaro.jinja.environment import JINJA_ENVIRONMENT
from jintaro.jinja.filters import JINJA_FILTERS
from jintaro.jinja.recursive_template import RecursiveTemplate
from jintaro.utils import merge_dicts


class RecursiveMapping(MutableMapping):

    class UnresolvedString(str):
        pass

    def __init__(self, vars: dict, context=None):
        self.__data = {}
        self.__context = context
        self.update(vars)

    @property
    def context(self):
        return self.__context

    @context.setter
    def context(self, val):
        self.__context = val

    def __getitem__(self, key):
        if not key in self.__data:
            return StrictUndefined(name=key)

        value = self.__data[key]
        if isinstance(value, self.UnresolvedString):
            rendered_string = JINJA_ENVIRONMENT.from_string(
                value, template_class=RecursiveTemplate).render_recursive(self)
            if rendered_string != value:
                value = self._evaluate_string(rendered_string)
            else:
                value = str(value)
            self.__data[key] = value
        return value

    def __setitem__(self, key, value):
        if isinstance(value, str):
            if self._is_possibly_template(value):
                self.__data[key] = self.UnresolvedString(value)
            else:
                self.__data[key] = value
        elif isinstance(value, dict):
            self.__data[key] = RecursiveMapping(value, context=self.__context)
        else:
            self.__data[key] = value

    def __delitem__(self, key):
        del self.__data[key]

    def __iter__(self):
        return iter(self.__data)

    def __len__(self):
        return len(self.__data)

    def __str__(self):
        return str(self.__data)

    @staticmethod
    def _evaluate_string(string):
        """Evaluates a string containing a Python value.

        Args:
            string(str): A Python value represented as a string

        Returns:
            str, int, float, bool, list or dict: The value of the evaluated string
        """
        try:
            # evaluate to int, float, list, dict
            return literal_eval(string.strip())
        except (ValueError, SyntaxError):
            try:
                # evaluate bool from different variations
                return bool(strtobool(string.strip()))
            except ValueError:
                # string cannot be evaluated -> return string
                return string

    @staticmethod
    def _is_possibly_template(data):
        """Determine if a string might be a Jinja2 template by searching for Jinja2 start delimiter.

        Args:
            data (any): A string to be assessed

        Returns:
            bool: True if a string looks like a Jinja2 template, False otherwise.
        """
        if isinstance(data, str):
            for marker in (BLOCK_START_STRING, VARIABLE_START_STRING, COMMENT_START_STRING):
                if marker in data:
                    return True
        return False
