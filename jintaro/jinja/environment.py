from jinja2.environment import Environment
from jinja2.runtime import StrictUndefined

from jintaro.jinja.filters import JINJA_FILTERS
from jintaro.utils import merge_dicts

JINJA_ENVIRONMENT = Environment(
    lstrip_blocks=True,
    trim_blocks=True,
    undefined=StrictUndefined,
)
JINJA_ENVIRONMENT.filters = merge_dicts(JINJA_ENVIRONMENT.filters, JINJA_FILTERS)
