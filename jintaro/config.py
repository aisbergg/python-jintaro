import os
from distutils.util import strtobool
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Union

import yaml
from cerberus import TypeDefinition, Validator
from cerberus.errors import REQUIRED_FIELD, BasicErrorHandler, ValidationError

from .exceptions import ConfigError, UnknownOptionError
from .log import Log
from .utils import read_file

# represents a missing option
missing = type("MissingType", (), {"__repr__": lambda x: "missing"})()


class ConfigValidator(Validator):

    class FlatErrorHandler(BasicErrorHandler):

        def __call__(self, errors: List[ValidationError]) -> List[Dict[str, Union[str, int, List[str]]]]:
            return self._format_errors(errors)

        def _format_errors(self, errors: List[ValidationError]) -> List[Dict[str, Union[str, int, List[str]]]]:
            formatted_errors = []
            for error in errors:
                if error.is_logic_error:
                    for definition_errors in error.definitions_errors.values():
                        formatted_errors.extend(self._format_errors(definition_errors))
                elif error.is_group_error:
                    formatted_errors.extend(self._format_errors(error.child_errors))
                elif error.code in self.messages:
                    formatted_errors.append(self._format_error(error))

            return formatted_errors

        def _format_error(self, error: ValidationError) -> Dict[str, Union[str, int, List[str]]]:
            formatted_error = {
                "path": list(error.document_path),
                "code": error.code,
                "msg": self._format_message(error.field, error),
            }
            return formatted_error

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self.purge_unknown = True
        self.error_handler = self.FlatErrorHandler()
        self.types_mapping['path'] = TypeDefinition('path', (Path,), ())

    @staticmethod
    def _normalize_purge_unknown(mapping: Mapping, schema: Mapping):
        """ {'type': 'boolean'} """
        for field in [x for x in mapping if x not in schema]:
            Log.warn(f"Unknown option '{field}' in configuration file")
            mapping.pop(field)
        return mapping

    def _normalize_default(self, mapping: Mapping, schema: Mapping, field: str) -> None:
        """ {'nullable': True} """
        value = schema[field]['default']
        if value is missing:
            self._error(field, REQUIRED_FIELD)
        else:
            mapping[field] = schema[field]['default']


class ConfigSource(object):

    def __init__(self):
        super().__init__()
        self._config = {}
        self._schema = {}
        self._init_schema()

    def get(self, path: str, default: Any = missing) -> Any:
        assert isinstance(path, str) and len(path) > 0

        value = self._config
        for key in path.split('.'):
            if isinstance(value, dict):
                if key in value:
                    value = value[key]
                elif default is not missing:
                    return default
                else:
                    raise UnknownOptionError(f"No such option '{path}' in the configuration")
            else:
                if hasattr(value, key):
                    value = getattr(value, key)
                elif default is not missing:
                    return default
                else:
                    raise UnknownOptionError(f"No such option '{path}' in the configuration")
        return value

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

    def _validate(self) -> None:
        if self._schema:
            validator = ConfigValidator(self._schema)
            if not validator.validate(self._config):
                errors = validator.errors
                for error in errors:
                    path = ".".join(error["path"])
                    if error['code'] == 0x02:
                        Log.error(f"Configuration is missing the option '{path}'. " \
                            "Make sure to supply the option either via configuration, "\
                            "environment variable or command line argument")
                    else:
                        Log.error(f"Configuration contains an invalid option '{path}': {error['msg']}")
                raise ConfigError(
                    "There is one or more errors in the configuration. Check the following options: {}".format(
                        ", ".join([i[0] for i in errors])))

            self._config = validator.document

    def _init_schema(self) -> None:
        raise NotImplementedError()

    @staticmethod
    def str_to_bool(val: str) -> bool:
        return bool(strtobool(val.strip()))

    @staticmethod
    def str_to_list(val: str) -> List[int]:
        return list(map(lambda vi: vi.strip(), val.split(":")))

    @staticmethod
    def val_to_row_column(val: Union[int, float, List[int]]) -> List[int]:
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


class Config(ConfigSource):

    def __init__(self, api_config_src: "ApiConfigSource", use_envs: Optional[bool] = False):
        self._api_src = api_config_src
        self._env_src = EnvironmentConfigSource() if use_envs else ConfigSource()
        config_file_path = api_config_src.get("config_path")
        self._file_src = YmlFileConfigSource(config_file_path) if config_file_path else ConfigSource()
        super().__init__()
        self._validate()

    def _init_schema(self) -> None:
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
                        self._api_src.get("input", None),
                        self._env_src.get("JINTARO_INPUT", None),
                        self._file_src.get("input", None),
                        missing,
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
                        self._api_src.get("template", None),
                        self._env_src.get("JINTARO_TEMPLATE", None),
                        self._file_src.get("template", None),
                        missing,
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
                        self._api_src.get("output", None),
                        self._env_src.get("JINTARO_OUTPUT", None),
                        self._file_src.get("output", None),
                        missing,
                    ),
            },
            "force": {
                "required":
                    False,
                "type":
                    "boolean",
                "default":
                    self._defaults(
                        self._api_src.get("force", None),
                        self._env_src.get("JINTARO_FORCE", None),
                        self._file_src.get("force", None),
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
                        self._api_src.get("delete", None),
                        self._env_src.get("JINTARO_DELETE", None),
                        self._file_src.get("delete", None),
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
                        self._api_src.get("pre_hook", None),
                        self._env_src.get("JINTARO_PRE_HOOK", None),
                        self._file_src.get("pre_hook", None),
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
                        self._api_src.get("post_hook", None),
                        self._env_src.get("JINTARO_POST_HOOK", None),
                        self._file_src.get("post_hook", None),
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
                        self._api_src.get("csv_delimiter", None),
                        self._env_src.get("JINTARO_CSV_DELIMITER", None),
                        self._file_src.get("csv_delimiter", None),
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
                        self._api_src.get("skip", None),
                        self._env_src.get("JINTARO_SKIP", None),
                        self._file_src.get("skip", None),
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
                    self._defaults(
                        self._api_src.get("header_row_column", None),
                        self._env_src.get("JINTARO_HEADER_ROW_COLUMN", None),
                        self._file_src.get("header_row_column", None),
                        [0, 0],
                    ),
            },
            "vars": {
                "required": False,
                "type": "dict",
                "allow_unknown": True,
                "nullable": True,
                "default": self._defaults(
                    self._api_src.get("vars", None),
                    self._file_src.get("vars", None),
                ),
            },
        }

    @staticmethod
    def _defaults(*values: Any) -> Any:
        for value in values:
            if value is not None:
                return value
        return None


class ApiConfigSource(ConfigSource):

    def __init__(self, config: Optional[dict] = None):
        super().__init__()
        assert isinstance(config, (dict, type(None)))
        self._config = {} if config is None else config

    def _init_schema(self) -> None:
        pass


class EnvironmentConfigSource(ConfigSource):

    def __init__(self):
        super().__init__()
        self._get_environment_variables()
        self._validate()

    def _init_schema(self) -> None:
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

    def _get_environment_variables(self) -> None:
        self._config = {k: v for k, v in os.environ.items() if k.startswith("JINTARO_")}


class YmlFileConfigSource(ConfigSource):

    def __init__(self, path: Union[str, Path]):
        assert isinstance(path, (str, Path))
        super().__init__()
        self._path = path if isinstance(path, Path) else Path(path)
        self._parse_file()
        self._validate()
        self._make_relative_paths()

    def _init_schema(self) -> None:
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

    def _make_relative_paths(self) -> None:

        def make_relative(string):
            path = Path(string)
            if path.is_absolute():
                return string
            return str(self._path.parent.joinpath(path))

        input_ = self._config.get("input", None)
        if input_:
            self._config["input"] = [make_relative(p) for p in input_]

        output = self._config.get("output", None)
        if output:
            self._config["output"] = make_relative(output)

        template = self._config.get("template", None)
        if template:
            self._config["template"] = make_relative(template)

    def _parse_file(self) -> None:
        try:
            config_raw_content = read_file(self._path)
            self._config = yaml.load(config_raw_content, Loader=yaml.Loader) or {}
        except Exception as ex:
            raise ConfigError(f"Failed to read YAML config file: {ex}") from ex
