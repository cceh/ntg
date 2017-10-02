# -*- encoding: utf-8 -*-

""" This module contains some useful functions. """

from __future__ import print_function
from __future__ import unicode_literals

import datetime
import logging
import subprocess
import sys
import types

from .config import args

BOOKS = [
    # id, siglum, name, no. of chapters
    ( 1, "Mt",  "Matthew",        0),
    ( 2, "Mc",  "Mark",          16),
    ( 3, "L",   "Luke",           0),
    ( 4, "J",   "John",           0),
    ( 5, "Act", "Acts",          28),
    ( 6, "R",   "Romans",         0),
    ( 7, "1K",  "1Corinthians",   0),
    ( 8, "2K",  "2Corinthians",   0),
    ( 9, "G",   "Galatians",      0),
    (10, "E",   "Ephesians",      0),
    (11, "Ph",  "Philippians",    0),
    (12, "Kol", "Colossians",     0),
    (13, "1Th", "1Thessalonians", 0),
    (14, "2Th", "2Thessalonians", 0),
    (15, "1T",  "1Timothy",       0),
    (16, "2T",  "2Timothy",       0),
    (17, "Tt",  "Titus",          0),
    (18, "Phm", "Philemon",       0),
    (19, "H",   "Hebrews",        0),
    (20, "Jc",  "James",          0),
    (21, "1P",  "1Peter",         0),
    (22, "2P",  "2Peter",         0),
    (23, "1J",  "1John",          0),
    (24, "2J",  "2John",          0),
    (25, "3J",  "3John",          0),
    (26, "Jd",  "Jude",           0),
    (27, "Ap",  "Revelation",     0),
]
""" Titles of the NT books """

BYZ_HSNR = "(300010, 300180, 300350, 303300, 303980, 304240, 312410)"
"""Manuscripts attesting the Byzantine Text.

We use these manuscripts as templates to establish the Byzantine Text according
to our rules.

"""

FEHLVERSE = """
    (
      anfadr >= 50837002 and endadr <= 50837046 or
      anfadr >= 51534002 and endadr <= 51534012 or
      anfadr >= 52406020 and endadr <= 52408014 or
      anfadr >= 52829002 and endadr <= 52829024
    )
    """
"""Verses added in later times.

These verses were added to the NT in later times. Because they are not original
they are not included in the text of manuscript 'A'.

"""


logger = logging.getLogger ('server')

LOG_HILITE = {
    logging.ERROR : ('\x1B[1m', '\x1B[0m')
}

def quote (s):
    if ' ' in s:
        return '"' + s + '"'
    return s


def log (level, msg, *aargs, **kwargs):
    """
    Low level log function
    """

    d = {
        'delta': str (datetime.datetime.now () - args.start_time),
        'hilite' : LOG_HILITE.get (level, ('', ''))
    }
    logger.log (level, msg, *aargs, extra = d)


def graphviz_layout (dot, format = 'dot'):
    """Call the GraphViz dot program to generate an image but mostly to precompute
    the graph layout.

    """

    cmdline = ['dot', '-T%s' % format]

    p = subprocess.Popen (
        cmdline,
        stdin  = subprocess.PIPE,
        stdout = subprocess.PIPE,
        stderr = subprocess.PIPE)

    try:
        outs, errs = p.communicate (dot.encode ('utf-8'), timeout = 15)
    except subprocess.TimeoutExpired:
        p.kill ()
        outs, errs = p.communicate ()

    #if p.returncode != 0:
    #    raise subprocess.CalledProcessError (
    #        'Program terminated with status: %d. stderr is: %s' % (
    #            p.returncode, errs))
    if errs:
        log (logging.ERROR, errs)

    return outs


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
