# -*- encoding: utf-8 -*-

""" This module contains some useful functions. """

from __future__ import print_function
from __future__ import unicode_literals

import datetime
import sys

import six

from .config import args

DEFAULTS = {
    #'att'    : 'ActsAtt_3',
    #'lac'    : 'ActsLac_3',
    #'attlac' : 'ActsAttLac_3',
    #'tmp'    : 'ActsTmp_3',

    'att'       : 'Att',
    'lac'       : 'Lac',
    'labez'     : 'Labez',
    'ms'        : 'Manuscripts',
    'chap'      : 'Chapters',
    'pass'      : 'Passages',
    'npass'     : 'NestedPassages',
    'aff'       : 'Affinity',
    'vp'        : 'VP',
    'rdg'       : 'Rdg',
    'witn'      : 'Witn',
    'listval'   : 'MsListVal',
    'vg'        : 'VG',
    'tmp'       : 'Tmp',
    'g_nodes'   : 'nodes',
    'g_edges'   : 'edges',
    'locstemed' : 'LocStemEd',
    'locstemedtmp' : 'LocStemEdTmp',
}
""" Defaults for init_parameters () """


BOOKS = (
    ("Mt", "Matthew"),
	("Mc", "Mark"),
    ("L", "Luke"),
	("J", "John"),
	("Act", "Acts"),
	("R", "Romans"),
	("1K", "1Corinthians"),
	("2K", "2Corinthians"),
	("G", "Galatians"),
	("E", "Ephesians"),
	("Ph", "Philippians"),
	("Kol", "Colossians"),
	("1Th", "1Thessalonians"),
	("2Th", "2Thessalonians"),
	("1T", "1Timothy"),
	("2T", "2Timothy"),
	("Tt", "Titus"),
	("Phm", "Philemon"),
	("H", "Hebrews"),
	("Jc", "James"),
	("1P", "1Peter"),
	("2P", "2Peter"),
	("1J", "1John"),
	("2J", "2John"),
	("3J", "3John"),
	("Jd", "Jude"),
	("Ap", "Revelation")
)
""" Titles of the NT books """

def init_parameters (defaults):

    def quote (s):
        if ' ' in s:
            return '"' + s + '"'
        return s

    parameters = dict ()

    target_db = quote (args.target_db) + '.'

    for k, v in defaults.items ():
        parameters['target_table_' + k] = quote (v)
        parameters[k] = target_db + quote (v)

    parameters['source_db']  = quote (args.source_db)
    parameters['target_db']  = quote (args.target_db)
    parameters['src_vg_db']  = quote (args.src_vg_db)
    parameters['table_mask'] = "Acts%02d%%" % args.chapter if args.chapter else "Acts%"

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
