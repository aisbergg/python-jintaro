import logging
import logging.config


def add_log_level(name, level):

    def logging_method(level):

        def method(self, message, *args, **kws):
            if self.isEnabledFor(level):
                self._log(level, message, args, **kws)  #pylint: disable=protected-access

        return method

    uppercase_name = name.upper()
    logging.addLevelName(level, uppercase_name)
    setattr(logging.Logger, uppercase_name, level)
    setattr(logging.Logger, name, logging_method(level))
    logging.__all__ += [uppercase_name]


# add more fine grained info levels
add_log_level("v", logging.INFO)
add_log_level("vv", logging.INFO + 1)
add_log_level("vvv", logging.INFO + 2)

log = logging.getLogger(__name__)


def configure_root_logger(level):

    class StdoutFilter(object):

        def filter(self, record):
            return record.levelno < logging.WARNING

    class StderrFilter(object):

        def filter(self, record):
            return record.levelno >= logging.WARNING

    logging_config = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'message_only': {
                'format': '%(message)s'
            },
        },
        'filters': {
            'stdout_filter': {
                '()': StdoutFilter
            },
            'stderr_filter': {
                '()': StderrFilter
            }
        },
        'handlers': {
            'stdout': {
                'class': 'logging.StreamHandler',
                'formatter': 'message_only',
                'filters': ['stdout_filter'],
                'stream': 'ext://sys.stdout'
            },
            'stderr': {
                'class': 'logging.StreamHandler',
                'formatter': 'message_only',
                'filters': ['stderr_filter'],
                'stream': 'ext://sys.stderr'
            },
        },
        'loggers': {
            '': {
                'handlers': ['stdout', 'stderr'],
                'level': level,
                'propagate': True
            }
        }
    }
    logging.config.dictConfig(logging_config)
