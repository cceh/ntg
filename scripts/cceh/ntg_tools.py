# -*- encoding: utf-8 -*-

""" This module contains some useful functions. """

from __future__ import print_function
from __future__ import unicode_literals

import datetime
import sys

import six
import MySQLdb


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


def cursor_get_value (cursor):
    for row in cursor.fetchall ():
        return row[0]


def execute (cursor, sql, parameters, debug_level = 3):
    sql = sql.format (**parameters)
    message (debug_level, sql.rstrip () + ';')
    cursor.execute (sql, parameters)
    message (debug_level, "%d rows" % cursor.rowcount)


def tabulate (cursor, stream = sys.stdout):
    """ Format and output a rowset

    Uses an output format similar to the one produced by the mysql commandline
    utility.

    """
    cols = range (0, len (cursor.description))
    rowlen = dict()

    def line ():
        for i in cols:
            stream.write ("+")
            stream.write ("-" * (rowlen[i] + 2))
        stream.write ("+\n")

    # convert database types to strings
    rows = []
    for row in cursor.fetchall():
        newrow = []
        for i in cols:
            if row[i] is None:
                newrow.append ('NULL')
            else:
                if cursor.description[i][1] == MySQLdb.STRING:
                    if isinstance (row[i], six.text_type):
                        newrow.append (row[i])
                    else:
                        newrow.append (row[i].decode ('utf-8'))
                else:
                    newrow.append (six.text_type (row[i]))
        rows.append (newrow)

    # calculate column widths
    for i in cols:
        rowlen[i] = len (cursor.description[i][0])

    for row in rows:
        for i in cols:
            rowlen[i] = max (rowlen[i], len (row[i]))

    # output header
    line ()
    for i in cols:
        stream.write ("| {:<{align}} ".format (cursor.description[i][0], align = rowlen[i]))
    stream.write ("|\n")
    line ()

    # output rows
    for row in rows:
        for i in cols:
            stream.write ("| {:<{align}} ".format (row[i], align = rowlen[i]))
        stream.write ("|\n")
    line ()
    stream.write ("%d rows\n" % len (rows))


def debug (cursor, msg, sql, parameters):
    # print values
    if args.verbose >= 3:
        execute (cursor, sql, parameters)
        if cursor.rowcount > 0:
            message (3, "*** DEBUG: {msg} ***".format (msg = msg), True)
            tabulate (cursor)


def fix (cursor, msg, check_sql, fix_sql, parameters):
    """Check and eventually fix errors.

    Executes the check_sql statement to check for error conditions and, if rows
    emerge, executes the fix_sql statement.  The fix_sql statement should be
    written as to fix the errors reported by the check_sql statement.  Finally
    it executes the check_sql statement again and reports an error if the
    condition still exists.

    """

    # print unfixed values
    execute (cursor, check_sql, parameters)
    if cursor.rowcount > 0:
        # apply fix
        if args.verbose >= 3:
            message (3, "*** WARNING: {msg} ***".format (msg = msg), True)
            tabulate (cursor)
        if fix_sql:
            execute (cursor, fix_sql, parameters)
            # print fixed values
            execute (cursor, check_sql, parameters)
            if cursor.rowcount > 0:
                message (0, "*** ERROR: {msg} ***".format (msg = msg), True)
                tabulate (cursor)


def print_stats (dba, parameters):
    cursor = dba.cursor ()

    cursor.execute ("SELECT count(distinct hs) FROM {att}".format (**parameters))
    hs = cursor_get_value (cursor)
    message (1, "hs       = {cnt}".format (cnt = hs))

    cursor.execute ("SELECT count(distinct anfadr, endadr) FROM {att}".format (**parameters))
    passages = cursor_get_value (cursor)
    message (1, "passages = {cnt}".format (cnt = passages))

    message (1, "hs * passages      = {cnt}".format (cnt = hs * passages))

    cursor.execute ("SELECT count(*) FROM {att}".format (**parameters))
    att = cursor_get_value (cursor)
    cursor.execute ("SELECT count(*) FROM {lac}".format (**parameters))
    lac = cursor_get_value (cursor)
    cursor.execute ("SELECT count(*) FROM {lab}".format (**parameters))
    lab = cursor_get_value (cursor)

    message (1, "rows in att        = {cnt}".format (cnt = att))
    message (1, "rows in lac        = {cnt}".format (cnt = lac))
    message (1, "rows in labez      = {cnt}".format (cnt = lab))
    message (1, "delta              = {cnt}".format (cnt = lab - (hs * passages)))

    # sum (passages in chapter * mss with chapter)

    cursor.execute ("""
    SELECT sum(pas_cnt * ch.ms_cnt)

    FROM
      (select kapanf, count(distinct anfadr, endadr) as pas_cnt FROM {att} GROUP BY kapanf) AS pas

    JOIN
      (select kapanf, count(distinct hs) as ms_cnt FROM {att} GROUP BY kapanf) AS ch

    ON ch.kapanf = pas.kapanf

    """.format (**parameters))
    pas = cursor_get_value (cursor)

    message (1, "chap * ms * pas    = {cnt}".format (cnt = pas))
