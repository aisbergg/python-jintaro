from jinja2.environment import Template
from jinja2.runtime import Context
from jinja2.utils import concat, missing

from jintaro.jinja.environment import JINJA_ENVIRONMENT
from jintaro.jinja.filters import JINJA_FILTERS
from jintaro.utils import merge_dicts


def render_template(template, context):
    if template:
        return JINJA_ENVIRONMENT.from_string(template, template_class=RecursiveTemplate).render(context)
    return template


class RecursiveTemplate(Template):

    class LazyContext(Context):

        def __init__(self, environment, parent, lazy_vars, name, blocks):
            super().__init__(environment, parent, name, blocks)
            self.lazy_vars = lazy_vars

        def resolve_or_missing(self, key):
            if key in self.vars:
                return self.vars[key]
            if key in self.parent:
                return self.parent[key]
            elif key in self.lazy_vars:
                return self.lazy_vars[key]
            return missing

    def render_recursive(self, vars: "RecursiveMapping"):
        if not vars.context:
            vars.context = self.LazyContext(self.environment, self.globals, vars, self.name, self.blocks)
        try:
            return concat(self.root_render_func(vars.context))
        except Exception:  #pylint: disable=broad-except
            self.environment.handle_exception()

    def new_context(self, vars=None, shared=False, locals=None):
        from jintaro.jinja.recursive_mapping import RecursiveMapping
        lazy_vars = RecursiveMapping(vars.copy() if vars else {})

        # based on jinja2 'new_context' function
        if shared:
            parent = {}
        else:
            parent = dict(self.globals or ())
        if locals:
            # if the parent is shared a copy should be created because
            # we don't want to modify the dict passed
            if shared:
                parent = dict(parent)
            for key, value in locals.items():
                if key[:2] == 'l_' and value is not missing:
                    parent[key[2:]] = value
        context = self.LazyContext(self.environment, parent, lazy_vars, self.name, self.blocks)

        lazy_vars.context = context
        return context
