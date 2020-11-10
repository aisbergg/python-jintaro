import re
import subprocess
from distutils.util import strtobool
from pathlib import Path
from typing import Any, Generator, List, Tuple, Union

import pyexcel

from . import exceptions
from .config import ApiConfigSource, Config
from .jinja_renderer import render_template
from .log import Log
from .utils import check_file, merge_dicts, read_file


class Jintaro:

    def __init__(self):
        self._api_config = ApiConfigSource()

    # -------------------------------------------------------------------------#
    #      _    ____ ___                                                       #
    #     / \  |  _ \_ _|                                                      #
    #    / _ \ | |_) | |                                                       #
    #   / ___ \|  __/| |                                                       #
    #  /_/   \_\_|  |___|                                                      #
    #                                                                          #
    # -------------------------------------------------------------------------#

    def config(self, path: Union[str, Path] = None) -> Union["Jintaro", Path]:
        """Set path of Jintaro configuration file for.

        Returns:
            Path: The config file path, if given path is None.
            Jintaro: The Jintaro instance, if given path is not None.
        """
        assert (isinstance(path, (str, Path, type(None))))

        if path is None:
            return self._api_config.get("config_path")
        elif isinstance(path, str):
            self._api_config.set("config_path", Path(path))
        else:
            self._api_config.set("config_path", path)
        return self

    def input(self, path: Union[str, Path, List[Union[str, Path]]] = None, clear=False) -> Union["Jintaro", List[Path]]:
        assert (isinstance(path, (str, Path, list, type(None))))

        if clear:
            self._api_config.set("input", None)
            return self
        paths = self._api_config.get("input", [])
        if path is None:
            return paths
        elif isinstance(path, list):
            for i in range(len(path)):
                path[i] = Path(path[i]) if isinstance(path[i], str) else path[i]
            paths.extend(path)
        elif isinstance(path, str):
            paths.append(Path(path))
        else:
            paths.append(path)
        self._api_config.set("input", paths)
        return self

    def template(self, path: Union[str, Path, None] = None) -> Union["Jintaro", Path, None]:
        assert (isinstance(path, (str, Path, type(None))))

        if path is None:
            return self._api_config.get("template")
        elif isinstance(path, str):
            self._api_config.set("template", Path(path))
        else:
            self._api_config.set("template", path)
        return self

    def output(self, path: Union[str, Path, None] = None) -> Union["Jintaro", Path, None]:
        assert (isinstance(path, (str, Path, type(None))))

        if path is None:
            return self._api_config.get("output")
        elif isinstance(path, str):
            self._api_config.set("output", Path(path))
        else:
            self._api_config.set("output", path)
        return self

    def force(self, force_: Union[bool, None] = None) -> Union["Jintaro", bool]:
        assert (isinstance(force_, (bool, type(None))))

        if force_ is None:
            return self._api_config.get("force")
        self._api_config.set("force", force_)
        return self

    def delete(self, delete: Union[bool, None] = None) -> Union["Jintaro", bool]:
        assert (isinstance(delete, (bool, type(None))))

        if delete is None:
            return self._api_config.get("delete")
        self._api_config.set("delete", delete)
        return self

    def pre_hook(self, cmd: Union[str, None] = None) -> Union["Jintaro", str]:
        assert (isinstance(cmd, (str, type(None))))

        if cmd is None:
            return self._api_config.get("pre_hook")
        self._api_config.set("pre_hook", cmd)

    def post_hook(self, cmd: Union[str, None] = None) -> Union["Jintaro", str]:
        assert (isinstance(cmd, (str, type(None))))

        if cmd is None:
            return self._api_config.get("post_hook")
        self._api_config.set("post_hook", cmd)

    def header_row_column(self,
                          row: Union[int, None] = None,
                          column: Union[int, None] = None) -> Union["Jintaro", Tuple]:
        assert (row is None or (isinstance(row, int) and row >= 0))
        assert (column is None or (isinstance(column, int) and column >= 0))

        if row is None and column is None:
            return self._api_config.get("header_row_column")
        row = row or 0
        column = column or 0
        self._api_config.set("header_row_column", (row, column))
        return self

    def csv_delimiter(self, delimiter: Union[str, None] = None) -> Union["Jintaro", str]:
        assert (isinstance(delimiter, (str, type(None))))

        if delimiter is None:
            return self._api_config.get("csv_delimiter")
        self._api_config.set("csv_delimiter", delimiter)
        return self

    def extra_vars(self, vars_: Union[dict, None] = None, clear=False) -> Union["Jintaro", dict, None]:
        assert (isinstance(vars_, (dict, type(None))))
        assert (isinstance(clear, bool))

        if clear:
            self._api_config.set("vars", None)
            return self
        if vars_ is None:
            return self._api_config.get("vars")
        self._api_config.set("vars", vars_)
        return self

    def continue_on_error(self, continue_: Union[bool, None] = None) -> Union["Jintaro", bool]:
        assert (isinstance(continue_, (bool, type(None))))

        if continue_ is None:
            return self._api_config.get("continue_on_error")
        self._api_config.set("continue_on_error", continue_)
        return self

    def run(self) -> None:
        # generate final config
        config = Config(self._api_config, use_envs=True)

        # load input files
        contexts = self._load_input(config)

        # create and run jobs
        for context in contexts:
            try:
                job = JintaroJob(context, config)
                job.run()
            except Exception as ex:  #pylint: disable=broad-except
                if not self._api_config.get("continue_on_error"):
                    raise ex
                Log.error(str(ex))

    # -------------------------------------------------------------------------#
    #      __     _    ____ ___                                                #
    #     / /    / \  |  _ \_ _|                                               #
    #    / /    / _ \ | |_) | |                                                #
    #   / /    / ___ \|  __/| |                                                #
    #  /_/    /_/   \_\_|  |___|                                               #
    #                                                                          #
    # -------------------------------------------------------------------------#

    def _load_input(self, config) -> Generator[dict, None, None]:
        input_paths = config.get("input")

        # check input file existence
        for path in input_paths:
            check_file(path)

        # go through each input file and parse the data
        for path in input_paths:
            # load sheet
            sheet = pyexcel.get_sheet(
                file_name=str(path),
                delimiter=config.get("csv_delimiter"),
                start_column=config.get("header_row_column")[0],
                start_row=config.get("header_row_column")[1],
                name_columns_by_row=0,
                skip_empty_rows=True,
            )

            if not sheet.colnames:
                raise exceptions.InputListError(f"Input file '{path}' is missing a proper column header.")

            # parse header
            def process_header(header):
                header = header.lower()
                # create valid identifier by removing invalid combinations
                header = re.sub('[^0-9a-zA-Z_]', '_', header)
                header = re.sub('^[^a-zA-Z_]+', '', header)
                return header

            headers = list(map(process_header, sheet.colnames))

            # turn rows into contexts
            for row in sheet.rows():
                data = {headers[i]: val for i, val in enumerate(row)}
                yield data


class JintaroJob(object):

    def __init__(self, context: dict, config: Config):
        self._context = context
        self._config = config
        self._output = Path(render_template(config.get("output"), context))
        self._template = Path(render_template(config.get("template"), context))
        self._pre_hook = render_template(config.get("pre_hook"), context)
        self._post_hook = render_template(config.get("post_hook"), context)
        self._extend_context()

    def _extend_context(self) -> None:
        extra_vars = self._config.get("vars") or {}
        job_vars = {
            "destination": self._output,
            "_destination": self._output,
            "dest": self._output,
            "_dest": self._output,
            "output": self._output,
            "_output": self._output,
            "template": self._template,
            "_template": self._template,
        }
        merged = merge_dicts(extra_vars, job_vars)
        self._context = merge_dicts(merged, self._context)

    def _run_hook(self, command: str, hook_type: str) -> None:
        if command:
            process = subprocess.Popen(
                command,
                shell=True,
                universal_newlines=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            process_output = lambda output: "\n".join(output.splitlines())
            stdout = process_output(process.stdout.read())
            stderr = process_output(process.stderr.read())
            Log.debug(stdout)
            if process.returncode != 0:
                raise exceptions.HookRunError(f"Failed to run {hook_type} hook for '{self._output}': {stderr}")

    def run(self) -> None:
        # delete rendered file
        skip_rule = self._config.get("skip")
        if skip_rule:
            try:
                skip = render_template(skip_rule, self._context)
                if isinstance(skip, str):
                    skip = bool(strtobool(skip))
            except Exception as ex:
                raise exceptions.OutputError(f"Failed to evaluate skip rule: {ex}")
            if skip:
                Log.info("Skipping ")
                return

        # run pre hook
        self._run_hook(self._pre_hook, 'pre')

        # render template
        template_content = read_file(self._template)
        rendered_template = render_template(template_content, self._context)

        # write content to file
        if self._output.exists():
            if not self._output.is_file():
                raise exceptions.OutputError(f"Path '{self._output}' exists and is not a file. ")
            if not self._config.get("force"):
                raise exceptions.OutputError(f"Path '{self._output}' already exists. Use 'force' to overwrite it.")
        self._output.parent.mkdir(parents=True, exist_ok=True)
        self._output.write_text(rendered_template)

        # run pre hook
        self._run_hook(self._post_hook, 'post')

        # delete rendered file
        if self._config.get("delete"):
            self._output.unlink()
