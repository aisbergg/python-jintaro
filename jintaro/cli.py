#!/usr/bin/env python

import argparse
import logging
import sys
import traceback

from . import __version__ as jintaro_version
from .exceptions import ConfigValueError
from .jintaro import Jintaro
from .log import configure_root_logger, log


def main():
    # parse arguments
    parser = argparse.ArgumentParser(
        prog="jintaro",
        description="Versatile batch templating, using Jinja2 templates and " \
                    "a spreadsheet format of your choice (xlsx, ods, csv)",
        add_help=False,
    )
    general_options = parser.add_argument_group(title="general options")
    general_options.add_argument(
        "-h",
        "--help",
        action="help",
        help="Show this help message and quit",
    )
    general_options.add_argument(
        "--version",
        action="version",
        version=f"Jintaro v{jintaro_version}",
        help="Print the program version and quit",
    )
    general_options.add_argument(
        "-v",
        "--verbose",
        dest="verbose",
        action="count",
        default=0,
        help="Make output verbose. Use it multiple times to increase verbosity",
    )
    general_options.add_argument(
        "-c",
        "--config",
        dest="config",
        type=str,
        default=None,
        help="The Jintaro configuration file",
    )
    general_options.add_argument(
        "--continue-on-error",
        dest="continue_on_error",
        action="store_true",
        default=None,
        help="Continue execution, even if errors occur",
    )

    config_options = parser.add_argument_group(title="config options")
    config_options.add_argument(
        "-i",
        "--input",
        dest="input",
        type=str,
        default=None,
        nargs='*',
        help="The input spreadsheet file(s) (file formats: xlsx, ods, csv)",
    )
    config_options.add_argument(
        "-t",
        "--template",
        dest="template",
        type=str,
        default=None,
        help="The template file. Path can contain Jinja2 syntax.",
    )
    config_options.add_argument(
        "-o",
        "--output",
        dest="output",
        type=str,
        default=None,
        help="Directory for resulting files",
    )
    config_options.add_argument(
        "-f",
        "--force",
        dest="force",
        action="store_true",
        default=None,
        help="Force overwrite of existing files",
    )
    config_options.add_argument(
        "--delete",
        dest="delete",
        action="store_true",
        default=None,
        help="Delete rendered files after post-hook finished",
    )
    config_options.add_argument(
        "--pre-hook",
        dest="pre_hook",
        type=str,
        default=None,
        help="Command to execute before templating",
    )
    config_options.add_argument(
        "--post-hook",
        dest="post_hook",
        type=str,
        default=None,
        help="Command to execute after templating",
    )
    config_options.add_argument(
        "--skip",
        dest="skip",
        type=str,
        default=None,
        help="Rule for skipping input list entries",
    )
    config_options.add_argument(
        "--header-row-column",
        dest="header_row_column",
        type=str,
        default=None,
        help="First row/column of the input file(s), that contains the header (format: 0,0)",
    )
    config_options.add_argument(
        "-e",
        "--extra-vars",
        dest="extra_vars",
        type=str,
        default=None,
        nargs='*',
        help="Extra variables used for templating (format: key=value)",
    )
    args = parser.parse_args(sys.argv[1:])

    # initialize logger
    levels = ["WARNING", "V", "VV", "VVV", "DEBUG"]
    configure_root_logger(levels[min(len(levels), args.verbose)])

    try:
        jintaro = Jintaro()

        # apply user config
        if args.config:
            jintaro.config(args.config)
        if args.input:
            jintaro.input(args.input)
        if args.template:
            jintaro.template(args.template)
        if args.output:
            jintaro.output(args.output)
        if args.force is not None:
            jintaro.force(args.force)
        if args.delete is not None:
            jintaro.delete(args.delete)
        if args.pre_hook:
            jintaro.pre_hook(args.pre_hook)
        if args.post_hook:
            jintaro.post_hook(args.post_hook)
        if args.skip:
            jintaro.skip(args.skip)
        if args.header_row_column:
            jintaro.header_row_column(args.header_row_column)
        if args.extra_vars:
            vars_ = {}
            for key_value in args.extra_values:
                key_value = key_value.split("=", 1)
                if len(key_value) != 2:
                    raise ConfigValueError("Extra vars must be specified as key-value pairs: 'key=value'")
                vars_[key_value[0]] = key_value[1]
            jintaro.extra_vars(vars_)
        if args.continue_on_error:
            jintaro.continue_on_error(args.continue_on_error)

        # render the templates
        jintaro.run()

    except KeyboardInterrupt:
        log.v("Interrupted by user, Exiting...")
        sys.exit(1)
    except Exception as e:  #pylint: disable=broad-except
        # catch errors and print to stderr
        if logging.root.level <= logging.DEBUG:
            log.error(traceback.format_exc())
        else:
            log.error(str(e))
        sys.exit(1)

    log.v("Jintaro finished, exiting now...")
    sys.exit(0)


if __name__ == "__main__":
    main()
