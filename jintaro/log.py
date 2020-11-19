import sys


class Log:
    """Stupid logger that writes messages to stdout or stderr accordingly."""

    ERROR = 40
    WARN = 30
    INFO = 20
    V = 20
    VV = 21
    VVV = 22
    DEBUG = 10
    level = ERROR
    prefix = ""

    @classmethod
    def configure(cls, level=ERROR, prefix=""):
        cls.level = level
        cls.prefix = prefix

    @classmethod
    def _log(cls, level: str, stream, msg: str, *args):
        """Write a message to a stream.

        Args:
            stream (TextIOWrapper): the stream to write to
            msg (str): the message to write
        """
        if args:
            msg = msg.format(*args)

        stream.write(level + ": " + cls.prefix + msg + "\n")

    @classmethod
    def debug(cls, msg, *args):
        """Log in debug messages.

        Args:
            msg (str): the message to be logged
            indent (int, optional): Add indentation to the message. Defaults to 0.
        """
        if cls.level <= cls.DEBUG:
            cls._log("DEBUG", sys.stdout, cls._indent(msg), *args)

    @classmethod
    def info(cls, msg, *args):
        """Log in info messages.

        Args:
            msg (str): the message to be logged
            indent (int, optional): Add indentation to the message. Defaults to 0.
        """
        if cls.level <= cls.INFO:
            cls._log("INFO", sys.stdout, cls._indent(msg), *args)

    @classmethod
    def v(cls, msg, *args):
        """Log in info messages.

        Args:
            msg (str): the message to be logged
            indent (int, optional): Add indentation to the message. Defaults to 0.
        """
        if cls.level <= cls.V:
            cls._log("INFO", sys.stdout, cls._indent(msg), *args)

    @classmethod
    def warn(cls, msg, *args):
        """Log in warn messages.

        Args:
            msg (str): the message to be logged
            indent (int, optional): Add indentation to the message. Defaults to 0.
        """
        if cls.level <= cls.WARN:
            cls._log("WARN", sys.stderr, cls._indent(msg), *args)

    @classmethod
    def error(cls, msg, *args):
        """Log in error messages.

        Args:
            msg (str): the message to be logged
            indent (int, optional): Add indentation to the message. Defaults to 0.
        """
        if cls.level <= cls.ERROR:
            cls._log("ERROR", sys.stderr, cls._indent(msg), *args)

    @staticmethod
    def _indent(string, indent=4):
        """Adds indentation to a multiline string. The fist line will be kept unchanged.

        Args:
            string (str): String to be indented
            indent (int): Number of spaces to indent the string

        Returns:
            str: The indented string.
        """
        if indent > 0 and string:
            lines = string.splitlines()
            string = lines[0]
            if len(lines) > 1:
                string = string + "\n" + "\n".join([" " * indent + l for l in lines[1:]])
            return string

        return string
