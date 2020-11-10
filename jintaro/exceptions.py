class JintaroException(Exception):
    """Base class for Jintaro exceptions"""


class ConfigError(JintaroException):
    """Base class for config exceptions"""


class UnknownOptionError(ConfigError):
    """"""


class ConfigValueError(ConfigError):
    """"""


class InputListError(JintaroException):
    """"""


class OutputError(JintaroException):
    """"""


class HookRunError(JintaroException):
    """"""
