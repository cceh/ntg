# -*- encoding: utf-8 -*-

"""The commandline and configuration stuff."""

import datetime
import logging
import types

class Args:
    pass

args = Args ()
""" Globally accessible arguments from command line. """

COLORS = {
    logging.CRITICAL : ('\x1B[38;2;255;0;0m', '\x1B[0m'),
    logging.ERROR    : ('\x1B[38;2;255;0;0m', '\x1B[0m'),
    logging.WARN     : ('', ''),
    logging.INFO     : ('', ''),
    logging.DEBUG    : ('', ''),
}

# colorize error log
old_factory = logging.getLogRecordFactory ()

def record_factory (*args, **kwargs):
    record = old_factory (*args, **kwargs)
    record.esc0, record.esc1 = COLORS[record.levelno]
    return record

logging.setLogRecordFactory (record_factory)


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


def init_cmdline (parser):
    """ Init the commandline parameter stuff. """

    parser.parse_args (namespace = args)

    args.start_time = datetime.datetime.now ()
    LOG_LEVELS = {
        0: logging.CRITICAL,  #
        1: logging.ERROR,     # -v
        2: logging.WARN,      # -vv
        3: logging.INFO,      # -vvv
        4: logging.DEBUG      # -vvvv
    }
    args.log_level = LOG_LEVELS.get (args.verbose, logging.DEBUG)

    logging.getLogger ().setLevel (args.log_level)
    formatter = logging.Formatter (
        fmt = '{esc0}{relativeCreated:6.0f} - {levelname:7} - {message}{esc1}',
        style='{'
    )

    stderr_handler = logging.StreamHandler ()
    stderr_handler.setFormatter (formatter)
    logging.getLogger ().addHandler (stderr_handler)

    file_handler = logging.FileHandler ('ntg.log')
    file_handler.setFormatter (formatter)
    logging.getLogger ().addHandler (file_handler)

    if args.log_level == logging.INFO:
        # sqlalchemy is way too verbose on level INFO
        sqlalchemy_logger = logging.getLogger ('sqlalchemy.engine')
        sqlalchemy_logger.setLevel (logging.WARN)


    try:
        return args, config_from_pyfile (args.profile)
    except:
        return args, None
