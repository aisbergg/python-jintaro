from ast import literal_eval
from collections.abc import MutableMapping
from distutils.util import strtobool

from jinja2.defaults import (BLOCK_START_STRING, COMMENT_START_STRING, VARIABLE_START_STRING)
from jinja2.environment import Environment, Template
from jinja2.runtime import Context, StrictUndefined
from jinja2.utils import concat, missing

from . import jinja_filter
from .utils import merge_dicts

JINJA_ENVIRONMENT = Environment(
    lstrip_blocks=True,
    trim_blocks=True,
    undefined=StrictUndefined,
)
JINJA_ENVIRONMENT.filters = merge_dicts(JINJA_ENVIRONMENT.filters, jinja_filter.FILTERS)


def render_template(template, context):
    if template:
        return JINJA_ENVIRONMENT.from_string(template, template_class=LazyTemplate).render(context)
    return template


class LazyMapping(MutableMapping):

    class UnresolvedString(str):
        pass

    def __init__(self, data: dict, context=None, root=None):
        self.__data = {}
        self.__root = root or self
        self.__context = context
        self.update(data)

    @property
    def context(self):
        return self.__context

    @context.setter
    def context(self, val):
        self.__context = val

    def __getitem__(self, key):
        value = self.__data[key]
        if isinstance(value, self.UnresolvedString):
            rendered_string = JINJA_ENVIRONMENT.from_string(
                value, template_class=LazyTemplate).render_with_existing_context(self.__context)
            if rendered_string != value:
                value = self._evaluate_string(rendered_string)
            else:
                value = str(value)
            self.__data[key] = value
        return value

    def __setitem__(self, key, value):
        if isinstance(value, str):
            if self.is_possibly_template(value):
                self.__data[key] = self.UnresolvedString(value)
            else:
                self.__data[key] = value
        elif isinstance(value, dict):
            self.__data[key] = LazyMapping(value, root=self.__root, context=self.__context)
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
        except (ValueError, SyntaxError) as e:
            try:
                # evaluate bool from different variations
                return bool(strtobool(string.strip()))
            except ValueError as e:
                # string cannot be evaluated -> return string
                return string

    @staticmethod
    def is_possibly_template(data):
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


class LazyContext(Context):

    def resolve_or_missing(self, key):
        if key in self.vars:
            return self.vars[key]
        if key in self.parent:
            return self.parent[key]
        elif key in self.parent["_lazy_vars"]:
            return self.parent["_lazy_vars"][key]
        return missing


class LazyTemplate(Template):

    def render_with_existing_context(self, context):
        try:
            return concat(self.root_render_func(context))
        except Exception:
            self.environment.handle_exception()

    def new_context(self, vars=None, shared=False, locals=None):
        lazy_vars = LazyMapping(vars.copy() or {})

        # based on jinja2 'new_context' function
        if shared:
            parent = lazy_vars
        else:
            parent = dict(self.globals or (), _lazy_vars=lazy_vars)
        if locals:
            # if the parent is shared a copy should be created because
            # we don't want to modify the dict passed
            if shared:
                parent = dict(parent)
            for key, value in locals.items():
                if key[:2] == 'l_' and value is not missing:
                    parent[key[2:]] = value
        context = LazyContext(self.environment, parent, self.name, self.blocks)

        lazy_vars.context = context
        return context
