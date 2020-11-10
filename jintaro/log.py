import sys


class Log:
    """Stupid logger that writes messages to stdout or stderr accordingly."""

    ERROR = 30
    INFO = 20
    DEBUG = 10
    level = ERROR
    prefix = ""

    @staticmethod
    def _log(level: str, stream, msg: str, *args):
        """Write a message to a stream.

        Args:
            stream (TextIOWrapper): the stream to write to
            msg (str): the message to write
        """
        if args:
            msg = msg.format(*args)

        stream.write(level + ": " + Log.prefix + msg + "\n")

    @staticmethod
    def debug(msg, *args, indent=0):
        """Log in debug messages.

        Args:
            msg (str): the message to be logged
            indent (int, optional): Add indentation to the message. Defaults to 0.
        """
        if Log.level <= 10:
            Log._log("DEBUG", sys.stdout, Log.indent_string(msg, indent), *args)

    @staticmethod
    def info(msg, *args, indent=0):
        """Log in info messages.

        Args:
            msg (str): the message to be logged
            indent (int, optional): Add indentation to the message. Defaults to 0.
        """
        if Log.level <= 20:
            Log._log("INFO", sys.stdout, Log.indent_string(msg, indent), *args)

    @staticmethod
    def warn(msg, *args, indent=0):
        """Log in warn messages.

        Args:
            msg (str): the message to be logged
            indent (int, optional): Add indentation to the message. Defaults to 0.
        """
        if Log.level <= 30:
            Log._log("WARN", sys.stderr, Log.indent_string(msg, indent), *args)

    @staticmethod
    def error(msg, *args, indent=0):
        """Log in error messages.

        Args:
            msg (str): the message to be logged
            indent (int, optional): Add indentation to the message. Defaults to 0.
        """
        if Log.level <= 30:
            Log._log("ERROR", sys.stderr, Log.indent_string(msg, indent), *args)

    @staticmethod
    def indent_string(string, indent):
        """Adds indentation to a string.

        Args:
            string (str): String to be indented
            indent (int): Number of spaces to indent the string

        Returns:
            str: The indented string.
        """
        if indent > 0:
            return "\n".join([" " * indent + l for l in string.splitlines()])

        return string
