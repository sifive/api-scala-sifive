#!/usr/bin/env python3

import logging
import sys
import argparse

VERBOSE = 15
TRACE = 5
SPAM = 3


def getLogger():
    """
    Get the logger
    """
    return logging.getLogger('api-scala-sifive')


class VerbosityAction(argparse._CountAction):
    def __call__(self, parser, namespace, values, option_string=None):
        # Delegate to built-in CountAction
        super().__call__(parser, namespace, values, option_string)

        count = getattr(namespace, self.dest, None)
        log = getLogger()
        if count >= 4:
            log.setLevel('SPAM')
        elif count == 3:
            log.setLevel('TRACE')
        elif count == 2:
            log.setLevel('DEBUG')
        elif count == 1:
            log.setLevel('VERBOSE')
        else:
            log.setLevel('INFO')


def add_verbosity_arg(parser):
    parser.add_argument('-v', '--verbose', action=VerbosityAction,
                        help='Specify level of verbosity\n'
                             '-v:    verbose\n'
                             '-vv:   debug\n'
                             '-vvv:  trace\n'
                             '-vvvv: spam\n')


class Formatter(logging.Formatter):
    """
    Custom formatter to prefix messages except for log.info
    """

    info_format = "%(msg)s"

    def __init__(self):
        super().__init__(fmt="[%(levelname)s] %(msg)s", datefmt=None, style='%')

    def format(self, record):

        orig_fmt = self._style._fmt
        if record.levelno == logging.INFO:
            self._style._fmt = Formatter.info_format

        result = logging.Formatter.format(self, record)
        self._style._fmt = orig_fmt

        return result


class Logger(logging.Logger):
    # See: https://stackoverflow.com/a/22586200/1785651

    def __init__(self, name, level=logging.NOTSET):
        super().__init__(name, level)
        # Use Formatter for info level
        _handler = logging.StreamHandler(sys.stdout)
        _handler.setFormatter(Formatter())
        logging.basicConfig(level=logging.INFO, handlers=[_handler])

        logging.addLevelName(VERBOSE, 'VERBOSE')
        logging.addLevelName(TRACE, 'TRACE')
        logging.addLevelName(SPAM, 'SPAM')

    def getLevelName(self):
        return logging.getLevelName(getLogger().getEffectiveLevel())

    def verbose(self, msg, *args, **kwargs):
        if self.isEnabledFor(VERBOSE):
            self._log(VERBOSE, msg, args, **kwargs)

    def trace(self, msg, *args, **kwargs):
        if self.isEnabledFor(TRACE):
            self._log(TRACE, msg, args, **kwargs)

    def spam(self, msg, *args, **kwargs):
        if self.isEnabledFor(SPAM):
            self._log(SPAM, msg, args, **kwargs)

    # for potential future -o flags (e.g. for `wit inspect --dot`)
    def output(self, msg):
        print(msg)


logging.setLoggerClass(Logger)
