# -*- encoding: utf-8 -*-

"""The commandline and configuration stuff."""

import logging
import types

class Args:
    pass

args = Args ()
""" Globally accessible arguments from command line. """


class Formatter (logging.Formatter):
    """ Allows colorful formatting of log lines. """
    COLORS = {
        logging.CRITICAL : ('\x1B[38;2;255;0;0m',  '\x1B[0m'),
        logging.ERROR    : ('\x1B[38;2;255;0;0m',  '\x1B[0m'),
        logging.WARN     : ('\x1B[38;2;255;64;0m', '\x1B[0m'),
        logging.INFO     : ('', ''),
        logging.DEBUG    : ('', ''),
    }

    def format (self, record):
        record.esc0, record.esc1 = self.COLORS[record.levelno]
        return super ().format (record)


def config_from_pyfile (filename):
    """Mimic Flask config files.

    Emulate the Flask config file parser so we can use the same config files for both,
    the server and this script.

    """

    d = types.ModuleType ('config')
    d.__file__ = filename
    try:
        with open (filename) as config_file:
            exec (compile (config_file.read (), filename, 'exec'), d.__dict__)
    except IOError as e:
        e.strerror = 'Unable to load configuration file (%s)' % e.strerror
        raise

    conf = {}
    for key in dir (d):
        if key.isupper ():
            conf[key] = getattr (d, key)
    return conf


def init_logging (args, *handlers):
    """ Init the logging stuff. """

    LOG_LEVELS = {
        0: logging.CRITICAL,  #
        1: logging.ERROR,     # -v
        2: logging.WARN,      # -vv
        3: logging.INFO,      # -vvv
        4: logging.DEBUG      # -vvvv
    }
    args.log_level = LOG_LEVELS.get (args.verbose, logging.DEBUG)

    root = logging.getLogger ()
    root.setLevel (args.log_level)

    formatter = Formatter (
        fmt = '{esc0}{relativeCreated:6.0f} - {levelname:7} - {message}{esc1}',
        style='{'
    )

    if not handlers:
        handlers = [logging.StreamHandler ()] # stderr

    for handler in handlers:
        handler.setFormatter (formatter)
        root.addHandler (handler)

    if args.log_level == logging.INFO:
        # sqlalchemy is way too verbose on level INFO
        sqlalchemy_logger = logging.getLogger ('sqlalchemy.engine')
        sqlalchemy_logger.setLevel (logging.WARN)
