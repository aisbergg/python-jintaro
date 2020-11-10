import configparser
import os
from distutils.util import strtobool
from pathlib import Path
from typing import Any, Generator, List, Set, Tuple, Union
import yaml

from cerberus import Validator, TypeDefinition
from cerberus.errors import BasicErrorHandler

from .exceptions import ConfigError, UnknownOptionError
from .log import Log
from .utils import read_file

# class MergedConfig(Config):
#     """
#     docstring
#     """

#     def get_value(parameter_list):
#         env_schema_path = "x.y.z"
#         cli_schema_path = "x.y.z"
#         file_schema_path = "x.y.z"

#         env_src = EnvironmentConfigSource()
#         cli_src = None
#         file_src = None

#     def merge_config(parameter_list):
#         env_src = EnvironmentConfigSource()
#         cli_src = None
#         file_src = None

#         data = {
#             "input": file["jintaro"].get("input", env_src.get()),
#             "template": file["jintaro"].get("template", env_src.get()),
#             "output": file["jintaro"].get("output", env_src.get()),
#             "force": file["jintaro"].get("force", env_src.get()),
#             "pre_hook": file["jintaro"].get("pre_hook", env_src.get()),
#             "post_hook": file["jintaro"].get("post_hook", env_src.get()),
#             "csv_delimiter": file["jintaro"].get("csv_delimiter", env_src.get()),
#             "skip": file["jintaro"].get("skip", env_src.get()),
#             "skip_rows": file["jintaro"].get("skip_rows", env_src.get()),
#         }

#         config_schema = {
#             "jintaro": {
#                 "required": True,
#                 "type": "dict",
#                 "nullable": True,
#                 "schema": {
#                     "input": {
#                         "required": False,
#                         "type": "list",
#                         "empty": False,
#                         "coerce": (str, ConfigSource.str_to_list),
#                         "nullable": True,
#                         "default": None,
#                     },
#                     "template": {
#                         "required": False,
#                         "type": "string",
#                         "empty": False,
#                         "nullable": True,
#                         "default": None,
#                     },
#                     "output": {
#                         "required": False,
#                         "type": "string",
#                         "empty": False,
#                         "nullable": True,
#                         "default": None,
#                     },
#                     "force": {
#                         "required": False,
#                         "type": "boolean",
#                         "coerce": (str, ConfigSource.str_to_bool),
#                         "default": False,
#                     },
#                     "pre_hook": {
#                         "required": False,
#                         "type": "string",
#                         "empty": False,
#                         "nullable": True,
#                         "default": None,
#                     },
#                     "post_hook": {
#                         "required": False,
#                         "type": "string",
#                         "empty": False,
#                         "nullable": True,
#                         "default": None,
#                     },
#                     "csv_delimiter": {
#                         "required": False,
#                         "type": "string",
#                         "empty": False,
#                         "default": ",",
#                     },
#                     "skip": {
#                         "required": False,
#                         "type": "string",
#                         "regex": r".*({{|{%|{#).*",
#                         "nullable": True,
#                         "default": None,
#                     },
#                     "skip_rows": {
#                         "required": False,
#                         "type": "integer",
#                         "coerce": int,
#                         "min": 1,
#                         "nullable": True,
#                         "default": None,
#                     },
#                 },
#             },
#             "vars": {
#                 "required": False,
#                 "type": "dict",
#                 "allow_unknown": True,
#                 "nullable": True,
#             },
#         }

# example_schema = {
#     "input": {
#         "required": False,
#         "type": "list",
#         "empty": False,
#         "coerce": (str, ConfigSource.str_to_list),
#         "nullable": True,
#         "default": None,
#         "sources": {
#             "source object"
#             "key": "schema"
#                    "schema"
#                    "env_src[JINTARO_INPUT]"
#         }
#     },
# }

# default_schemas = {
#     "input": {
#         "required": False,
#         "type": "list",
#         "empty": False,
#         "nullable": True,
#         "default": None,
#     },
# }

# data_schema2 = {
#     "input": {
#         "required": True,
#         "type": "list",
#         "empty": False,
#         "sources": [(env, "JINTARO_INPUT", "schema_override"),],
#         "default_setter": defaults(
#             env.JINTARO_INPUT,
#             cli.input,
#             file.jintaro.input,
#         ),
#     },
# }

# # sind gleich, unterschied in coerce
# "env.JINTARO_INPUT"
# "cli.input"
# "file.jintaro.input"

# # als default handler verwenden, dann wird auch die validierung durchgeführt

# # quellen nur validieren
# env_schema = {
#     "JINTARO_INPUT": {
#         "type": "list",
#         "coerce": (str, ConfigSource.str_to_list)
#     },
#     "JINTARO_TEMPLATE": {
#         "type": "list",
#         "coerce": (str, ConfigSource.str_to_list)
#     }
# }

# # only normalization and warn messages
# example_schema2 = {
#     "JINTARO_INPUT": {
#         **default_schemas["input"],
#         "coerce": (str, ConfigSource.str_to_list),
#     },
# }
# example_schema3 = {
#     "JINTARO_INPUT": {
#         **default_schemas["input"], "required": False,
#         "type": "list",
#         "empty": False,
#         "coerce": (str, ConfigSource.str_to_list),
#         "nullable": True,
#         "default": None,
#         "sources": {
#             "source object"
#             "key": "schema"
#                    "schema"
#                    "env_src[JINTARO_INPUT]"
#         }
#     },
# }

# Was ich gerne hätte
# ein Schema
# das Schema gibt die endgültige Config Struktur an
# es gibt für jeden Schlüssel mehrere Quellen (file, env, cli)
# jede Quelle hat eigene coerce regeln und fehlermeldungen
# nicht alle quellen müssen für jür jeden Schlüssel verfürbar sein

# Config consists of multiple config sources
# config validates itself, so that no value is missing

# Config Sources check type validation and normalization
# Config only checks, if all required values exist


class ConfigValidation(object):

    class PurgeUnknownValidator(Validator):

        class PrettyErrorHandler(BasicErrorHandler):

            def __call__(self, errors):
                self.clear()
                self.extend(errors)
                return self._prettify_errors(self.tree)

            def __str__(self):
                return str(self._prettify_errors(self.tree))

            def __iter__(self):
                pretty_errors = self._prettify_errors(self.tree)
                for err in pretty_errors:
                    yield err

            def _prettify_errors(self, tree, parent=None):
                prefix = parent + "." if parent else ""
                messages = []
                for name, errors in tree.items():
                    prefixed_name = prefix + name
                    for err in errors:
                        if isinstance(err, str):
                            messages.append((prefixed_name, err))
                        elif isinstance(err, dict):
                            messages.extend(self._prettify_errors(err, prefixed_name))
                return messages

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.purge_unknown = True
            self.error_handler = self.PrettyErrorHandler()
            self.types_mapping['path'] = TypeDefinition('path', (Path,), ())

        @staticmethod
        def _normalize_purge_unknown(mapping, schema):
            """ {'type': 'boolean'} """
            for field in [x for x in mapping if x not in schema]:
                Log.warn(f"Unknown option '{field}' in configuration file")
                mapping.pop(field)
            return mapping

    def __init__(self):
        super().__init__()
        self._config = {}
        self._schema = {}
        self._init_schema()

    def _validate(self) -> dict:
        if self._schema:
            validator = self.PurgeUnknownValidator(self._schema)
            if not validator.validate(self._config):
                errors = validator.errors
                for var, description in errors:
                    Log.error(f"Configuration contains an invalid option '{var}': {description}")
                raise ConfigError(
                    "There is one or more errors in the configuration. Check the following options: {}".format(
                        ", ".join([i[0] for i in errors])))

            self._config = validator.document

    def _init_schema(self):
        pass

    @staticmethod
    def str_to_bool(val):
        return bool(strtobool(val.strip()))

    @staticmethod
    def str_to_list(val):
        return list(map(lambda vi: vi.strip(), val.split(":")))

    @staticmethod
    def val_to_row_column(val):
        if isinstance(val, str):
            val = val.split(",")
            row = column = 0
            if len(val) > 0:
                row = int(val[0]) if len(val[0]) > 0 else 0
            if len(val) > 1:
                column = int(val[0]) if len(val[0]) > 0 else 0
            return [row, column]
        if isinstance(val, (int, float)):
            return [int(val), 0]
        if isinstance(val, list):
            row = int(val[0]) if len(val) > 0 else 0
            column = int(val[1]) if len(val) > 1 else 0
            return [row, column]


class Config(ConfigValidation):

    # validate ini file
    # validate command line arguments
    # validate environment args
    # validate overall config
    # what are their intersections?
    # merge the configs
    # allow single interface to access the config (underlying data structure)

    # separate validation and final assembly?

    # JINTARO_INPUT
    # --input
    # [jintaro] input=/dad

    # JINTARO_TEMPLATE -> convert into nested dict (error message must be flat)
    # --template -> convert into nested dict (error message must be flat)
    # [jintaro] template=/dad:/daiuwghd

    # convert into nested dict the way I want it
    # adapt errror message to be either flat or nested

    def __init__(self, api_config_src: "ApiConfigSource", use_envs=False):
        self._api_src = api_config_src
        self._env_src = EnvironmentConfigSource() if use_envs else ConfigSource()
        config_file_path = api_config_src.get("config_path")
        self._file_src = YmlFileConfigSource(config_file_path) if config_file_path else ConfigSource()
        super().__init__()
        self._validate()

    def _init_schema(self):
        self._schema = {
            "input": {
                "required":
                    True,
                "type":
                    "list",
                "empty":
                    False,
                "default":
                    self._defaults(
                        self._api_src.get("input"),
                        self._env_src.get("JINTARO_INPUT"),
                        self._file_src.get("input"),
                    ),
            },
            "template": {
                "required":
                    True,
                "type":
                    "string",
                "empty":
                    False,
                "default":
                    self._defaults(
                        self._api_src.get("template"),
                        self._env_src.get("JINTARO_TEMPLATE"),
                        self._file_src.get("template"),
                    ),
            },
            "output": {
                "required":
                    True,
                "type":
                    "string",
                "empty":
                    False,
                "default":
                    self._defaults(
                        self._api_src.get("output"),
                        self._env_src.get("JINTARO_OUTPUT"),
                        self._file_src.get("output"),
                    ),
            },
            "force": {
                "required":
                    False,
                "type":
                    "boolean",
                "default":
                    self._defaults(
                        self._api_src.get("force"),
                        self._env_src.get("JINTARO_FORCE"),
                        self._file_src.get("force"),
                        False,
                    ),
            },
            "delete": {
                "required":
                    False,
                "type":
                    "boolean",
                "default":
                    self._defaults(
                        self._api_src.get("delete"),
                        self._env_src.get("JINTARO_DELETE"),
                        self._file_src.get("delete"),
                        False,
                    ),
            },
            "pre_hook": {
                "required":
                    False,
                "type":
                    "string",
                "nullable":
                    True,
                "default":
                    self._defaults(
                        self._api_src.get("pre_hook"),
                        self._env_src.get("JINTARO_PRE_HOOK"),
                        self._file_src.get("pre_hook"),
                    ),
            },
            "post_hook": {
                "required":
                    False,
                "type":
                    "string",
                "nullable":
                    True,
                "default":
                    self._defaults(
                        self._api_src.get("post_hook"),
                        self._env_src.get("JINTARO_POST_HOOK"),
                        self._file_src.get("post_hook"),
                    ),
            },
            "csv_delimiter": {
                "required":
                    False,
                "type":
                    "string",
                "minlength":
                    1,
                "default":
                    self._defaults(
                        self._api_src.get("csv_delimiter"),
                        self._env_src.get("JINTARO_CSV_DELIMITER"),
                        self._file_src.get("csv_delimiter"),
                        ",",
                    ),
            },
            "skip": {
                "required":
                    False,
                "type":
                    "string",
                "regex":
                    r".*({{|{%|{#).*",
                "nullable":
                    True,
                "default":
                    self._defaults(
                        self._api_src.get("skip"),
                        self._env_src.get("JINTARO_SKIP"),
                        self._file_src.get("skip"),
                    ),
            },
            "header_row_column": {
                "required":
                    False,
                "type":
                    "list",
                "nullable":
                    True,
                "default":
                    self._defaults(self._api_src.get("header_row_column"),
                                   self._env_src.get("JINTARO_HEADER_ROW_COLUMN"),
                                   self._file_src.get("header_row_column"), [0, 0]),
            },
            "vars": {
                "required":
                    False,
                "type":
                    "dict",
                "allow_unknown":
                    True,
                "nullable":
                    True,
                "default":
                    self._defaults(self._api_src.get("vars"), self._env_src.get("JINTARO_HEADER_ROW_COLUMN"),
                                   self._file_src.get("vars"), [0, 0]),
            },
        }

    @staticmethod
    def _defaults(*values):
        for value in values:
            if value is not None:
                return value
        return None

    def get(self, path: str):
        value = self._config
        for key in path.split('.'):
            if isinstance(value, dict):
                if key in value:
                    value = value[key]
                else:
                    raise UnknownOptionError(f"Unknown option '{path}'")
            else:
                if hasattr(value, key):
                    value = getattr(value, key)
                else:
                    raise UnknownOptionError(f"Unknown option '{path}'")
        return value


class ConfigSource(object):

    def __init__(self):
        super().__init__()
        self._config = {}

    def get(self, path: str, default=None):
        value = self._config
        for key in path.split('.'):
            if isinstance(value, dict):
                if key in value:
                    value = value[key]
                else:
                    return default
            else:
                if hasattr(value, key):
                    value = getattr(value, key)
                else:
                    return default
        return value


class ApiConfigSource(ConfigSource, ConfigValidation):

    def __init__(self, config=None):
        super().__init__()
        assert isinstance(config, (dict, type(None)))
        self._config = {} if config is None else config

    def set(self, path: str, value: Any) -> None:
        assert isinstance(path, str) and len(path) > 0

        full_path = path.split('.')
        parent = full_path[:-1]
        key = full_path[-1]

        last_branch = self._config
        for p in parent:
            if not (p in last_branch and isinstance(last_branch[p], dict)):
                last_branch[p] = {}
            last_branch = last_branch[p]

        last_branch[key] = value


class EnvironmentConfigSource(ConfigSource, ConfigValidation):

    def __init__(self):
        super().__init__()
        self._get_environment_variables()
        self._validate()

    def _init_schema(self):
        self._schema = {
            "JINTARO_INPUT": {
                "type": "list",
                "coerce": (str, self.str_to_list),
            },
            "JINTARO_TEMPLATE": {},
            "JINTARO_OUTPUT": {},
            "JINTARO_FORCE": {
                "type": "boolean",
                "coerce": (str, self.str_to_bool),
            },
            "JINTARO_DELETE": {
                "type": "boolean",
                "coerce": (str, self.str_to_bool),
            },
            "JINTARO_PRE_HOOK": {},
            "JINTARO_POST_HOOK": {},
            "JINTARO_CSV_DELIMITER": {},
            "JINTARO_SKIP": {},
            "JINTARO_HEADER_ROW_COLUMN": {
                "type": "list",
                "coerce": self.val_to_row_column,
            }
        }

    def _get_environment_variables(self):
        self._config = {k: v for k, v in os.environ.items() if k.startswith("JINTARO_")}


class YmlFileConfigSource(ConfigSource, ConfigValidation):

    def __init__(self, path):
        assert isinstance(path, (str, Path))
        super().__init__()
        self._path = path if isinstance(path, Path) else Path(path)
        self._parse_file()
        self._validate()

    def _init_schema(self):
        self._schema = {
            "input": {
                "type": "list",
                "coerce": (str, self.str_to_list),
            },
            "template": {},
            "output": {},
            "force": {
                "type": "boolean",
            },
            "delete": {
                "type": "boolean",
            },
            "pre_hook": {},
            "post_hook": {},
            "csv_delimiter": {},
            "skip": {},
            "header_row_column": {
                "type": "list",
                "coerce": self.val_to_row_column,
            },
            "vars": {
                "required": False,
                "type": "dict",
                "allow_unknown": True,
                "nullable": True,
            },
        }

    def _parse_file(self):
        try:
            config_raw_content = read_file(self._path)
            self._config = yaml.load(config_raw_content, Loader=yaml.Loader) or {}
        except Exception as ex:
            raise ConfigError(f"Failed to read YAML config file: {ex}") from ex
