# -*- encoding: utf-8 -*-

""" This module contains some useful functions. """

from __future__ import print_function
from __future__ import unicode_literals

import datetime
import os
import subprocess
import sys

import six

from .config import args

DEFAULTS = {
    #'att'    : 'ActsAtt_3',
    #'lac'    : 'ActsLac_3',
    #'attlac' : 'ActsAttLac_3',
    #'tmp'    : 'ActsTmp_3',

    'att'       : 'att',
    'lac'       : 'lac',
    'pass'      : 'passages',
    'chap'      : 'chapters',
    'ms'        : 'manuscripts',
    'var'       : 'var',
    'read'      : 'readings',
    'aff'       : 'affinity',
    'tmp'       : 'tmp',
    'g_nodes'   : 'nodes',
    'g_edges'   : 'edges',
    'locstemed' : 'locstemed',
    'locstemedtmp' : 'locstemedtmp',
}
""" Defaults for init_parameters () """


BOOKS = (
    ("Mt",  "Matthew"),
	("Mc",  "Mark"),
    ("L",   "Luke"),
	("J",   "John"),
	("Act", "Acts"),
	("R",   "Romans"),
	("1K",  "1Corinthians"),
	("2K",  "2Corinthians"),
	("G",   "Galatians"),
	("E",   "Ephesians"),
	("Ph",  "Philippians"),
	("Kol", "Colossians"),
	("1Th", "1Thessalonians"),
	("2Th", "2Thessalonians"),
	("1T",  "1Timothy"),
	("2T",  "2Timothy"),
	("Tt",  "Titus"),
	("Phm", "Philemon"),
	("H",   "Hebrews"),
	("Jc",  "James"),
	("1P",  "1Peter"),
	("2P",  "2Peter"),
	("1J",  "1John"),
	("2J",  "2John"),
	("3J",  "3John"),
	("Jd",  "Jude"),
	("Ap",  "Revelation")
)
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


def quote (s):
    if ' ' in s:
        return '"' + s + '"'
    return s

def init_parameters (defaults):

    parameters = dict ()

    for k, v in defaults.items ():
        parameters[k] = quote (v)

    parameters['fehlverse'] = FEHLVERSE
    parameters['byzlist']   = BYZ_HSNR

    return parameters


def message (level, s, hilite = False):
    """
    Print information if needed.
    """
    if args.verbose >= level:
        delta = six.text_type (datetime.datetime.now () - args.start_time)
        print ('[' + delta + ']', end = " ")
        if hilite:
            print ("\x1B[1m" + s + "\x1B[0m");
        else:
            print (s);


def tabulate (res, stream = sys.stdout):
    """ Format and output a rowset

    Uses an output format similar to the one produced by the mysql commandline
    utility.

    """
    cols = range (0, len (res.keys ()))
    rowlen = dict()

    def line ():
        for i in cols:
            stream.write ("+")
            stream.write ("-" * (rowlen[i] + 2))
        stream.write ("+\n")

    # convert database types to strings
    rows = []
    for row in res.fetchall():
        newrow = []
        for i in cols:
            if row[i] is None:
                newrow.append ('NULL')
            else:
                newrow.append (six.text_type (row[i]))
        rows.append (newrow)

    # calculate column widths
    for i in cols:
        rowlen[i] = len (res.keys ()[i])

    for row in rows:
        for i in cols:
            rowlen[i] = max (rowlen[i], len (row[i]))

    # output header
    line ()
    for i in cols:
        stream.write ("| {:<{align}} ".format (res.keys ()[i], align = rowlen[i]))
    stream.write ("|\n")
    line ()

    # output rows
    for row in rows:
        for i in cols:
            stream.write ("| {:<{align}} ".format (row[i], align = rowlen[i]))
        stream.write ("|\n")
    line ()
    stream.write ("%d rows\n" % len (rows))


def graphviz_layout (dot):
    """ Call the GraphViz dot program to precompute the graph layout. """

    cmdline = ['dot', '-Tdot']

    p = subprocess.Popen (
        cmdline,
        stdin  = subprocess.PIPE,
        stdout = subprocess.PIPE,
        stderr = subprocess.PIPE,
        universal_newlines = True)

    try:
        outs, errs = p.communicate (dot, timeout = 15)
    except subprocess.TimeoutExpired:
        p.kill ()
        outs, errs = p.communicate ()

    if p.returncode != 0:
        raise subprocess.CalledProcessError (
            'Program terminated with status: %d. stderr is: %s' % (
                p.returncode, errs))
    elif errs:
        message (3, errs)

    return outs
