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
    ( 1, "Mt",  "Matthew",       28),
    ( 2, "Mc",  "Mark",          16),
    ( 3, "L",   "Luke",          24),
    ( 4, "J",   "John",          21),
    ( 5, "Act", "Acts",          28),
    ( 6, "R",   "Romans",        16),
    ( 7, "1K",  "1Corinthians",  16),
    ( 8, "2K",  "2Corinthians",  13),
    ( 9, "G",   "Galatians",      6),
    (10, "E",   "Ephesians",      6),
    (11, "Ph",  "Philippians",    4),
    (12, "Kol", "Colossians",     4),
    (13, "1Th", "1Thessalonians", 5),
    (14, "2Th", "2Thessalonians", 3),
    (15, "1T",  "1Timothy",       6),
    (16, "2T",  "2Timothy",       4),
    (17, "Tt",  "Titus",          3),
    (18, "Phm", "Philemon",       1),
    (19, "H",   "Hebrews",       13),
    (20, "Jc",  "James",          5),
    (21, "1P",  "1Peter",         5),
    (22, "2P",  "2Peter",         3),
    (23, "1J",  "1John",          5),
    (24, "2J",  "2John",          1),
    (25, "3J",  "3John",          1),
    (26, "Jd",  "Jude",           1),
    (27, "Ap",  "Revelation",    22),
]
""" Titles of the NT books """

BYZ_HSNR = "(300010, 300180, 300350, 303300, 303980, 304240, 312410)"
"""Manuscripts attesting the Byzantine Text.

We use these manuscripts as templates to establish the Byzantine Text according
to our rules.

"""

FEHLVERSE = """
    (
      begadr >= 50837002 and endadr <= 50837047 or
      begadr >= 51534002 and endadr <= 51534013 or
      begadr >= 52406020 and endadr <= 52408015 or
      begadr >= 52829002 and endadr <= 52829025
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
