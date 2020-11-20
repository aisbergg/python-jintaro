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
        #TODO: Add description and examples
        description="Template List excel, csv ods",
        add_help=False,
    )

    parser.add_argument(
        "--help",
        action="help",
        help="Show this help message and exit",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"Jintaro v{jintaro_version}",
        help="Print the program version and quit",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        dest="verbose",
        action="count",
        default=0,
        help="Enable more verbose mode",
    )
    parser.add_argument(
        "-c",
        "--config",
        dest="config",
        type=str,
        default=None,
        help="",
    )
    parser.add_argument(
        "-i",
        "--input",
        dest="input",
        type=str,
        default=None,
        nargs='*',
        help="",
    )
    parser.add_argument(
        "-t",
        "--template",
        dest="template",
        type=str,
        default=None,
        help="",
    )
    parser.add_argument(
        "-o",
        "--output",
        dest="output",
        type=str,
        default=None,
        help="",
    )
    parser.add_argument(
        "-f",
        "--force",
        dest="force",
        action="store_true",
        default=None,
        help="",
    )
    parser.add_argument(
        "--delete",
        dest="delete",
        action="store_true",
        default=None,
        help="Delete rendered files afterwards. Might be usefull in combination with --post-hook.",
    )
    parser.add_argument(
        "--pre-hook",
        dest="pre_hook",
        type=str,
        default=None,
        help="",
    )
    parser.add_argument(
        "--post-hook",
        dest="post_hook",
        type=str,
        default=None,
        help="",
    )
    parser.add_argument(
        "--header-row-column",
        dest="header_row_column",
        type=str,
        default=None,
        help="",
    )
    parser.add_argument(
        "-e",
        "--extra-vars",
        dest="extra_vars",
        type=str,
        default=None,
        nargs='*',
        help="",
    )
    parser.add_argument(
        "--continue-on-error",
        dest="continue_on_error",
        action="store_true",
        default=None,
        help="",
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
