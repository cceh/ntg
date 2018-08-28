# -*- encoding: utf-8 -*-

"""The commandline and configuration stuff."""

import datetime
import logging
import types

class Args:
    pass

args = Args ()
""" Globally accessible arguments from command line. """

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

    config = config_from_pyfile (args.profile)

    args.start_time = datetime.datetime.now ()
    LOG_LEVELS = {
        0: logging.CRITICAL,
        1: logging.ERROR,
        2: logging.WARN,
        3: logging.INFO,
        4: logging.DEBUG
    }
    args.log_level = LOG_LEVELS.get (args.verbose, logging.CRITICAL)

    logging.getLogger ().setLevel (args.log_level)
    formatter = logging.Formatter (fmt = '%(hilitestart)s%(relativeCreated)d - %(levelname)s - %(message)s%(hiliteend)s')

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

    return args, config
