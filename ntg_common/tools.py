# -*- encoding: utf-8 -*-

""" This module contains some useful functions. """

import logging
import subprocess

BOOKS = [
    # id, siglum, name,            no. of chapters
    ( 1, "Mt",   "Matthew",        28),
    ( 2, "Mc",   "Mark",           16),
    ( 3, "L",    "Luke",           24),
    ( 4, "J",    "John",           21),
    ( 5, "Acts", "Acts",           28),
    ( 6, "R",    "Romans",         16),
    ( 7, "1K",   "1 Corinthians",  16),
    ( 8, "2K",   "2 Corinthians",  13),
    ( 9, "G",    "Galatians",       6),
    (10, "E",    "Ephesians",       6),
    (11, "Ph",   "Philippians",     4),
    (12, "Kol",  "Colossians",      4),
    (13, "1Th",  "1 Thessalonians", 5),
    (14, "2Th",  "2 Thessalonians", 3),
    (15, "1T",   "1 Timothy",       6),
    (16, "2T",   "2 Timothy",       4),
    (17, "Tt",   "Titus",           3),
    (18, "Phm",  "Philemon",        1),
    (19, "H",    "Hebrews",        13),
    (20, "Jc",   "James",           5),
    (21, "1P",   "1 Peter",         5),
    (22, "2P",   "2 Peter",         3),
    (23, "1J",   "1 John",          5),
    (24, "2J",   "2 John",          1),
    (25, "3J",   "3 John",          1),
    (26, "Jd",   "Jude",            1),
    (27, "Ap",   "Revelation",     22),
]
""" Titles of the NT books """

BYZ_HSNR_ACTS = "(300010, 300180, 300350, 303300, 303980, 304240, 312410)"
"""Manuscripts attesting the Byzantine Text.

We use these manuscripts as templates to establish the Byzantine Text according
to our rules.

"""

BYZ_HSNR_CL   = "(300010, 300180, 300350, 303300, 303980, 304240, 312410)"

BYZ_HSNR_JOHN = "(200070, 200280, 200450, 300180, 300350, 302260, 313200)"

BYZ_HSNR_MARK = "(300030, 300180, 300350, 301050, 302610, 303510, 326070)"

# Mk  7:16, 9:44, 9:46, 11:26, 15:28, 16:9-20

FEHLVERSE = """
    (
      begadr >= 20716000 and endadr <= 20716999 or
      begadr >= 20944000 and endadr <= 20944999 or
      begadr >= 20946000 and endadr <= 20946999 or
      begadr >= 21126000 and endadr <= 21126999 or
      begadr >= 21528000 and endadr <= 21528999 or
      begadr >= 21609000 and endadr <= 21620999 or
      begadr >= 21608068 and endadr <= 21620999 or

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


logger = logging.getLogger ()

def quote (s):
    if ' ' in s:
        return '"' + s + '"'
    return s


def log (level, msg, *aargs, **_kwargs):
    """
    Low level log function
    """

    logger.log (level, msg, *aargs)


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
