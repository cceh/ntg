# -*- encoding: utf-8 -*-

from __future__ import unicode_literals

import datetime
import sys

import six
import MySQLdb


def init_parameters (parameters):
    parameters['source_db']           = args.source_db
    parameters['target_db']           = args.target_db

    parameters['source_db']           = '"{source_db}"'.format (**parameters)
    parameters['target_db']           = '"{target_db}"'.format (**parameters)

    parameters['target_table']        = '"{target_table}"'.format (**parameters)
    parameters['target_table_lac']    = '"{target_table_lac}"'.format (**parameters)
    parameters['target_table_attlac'] = '"{target_table_attlac}"'.format (**parameters)
    parameters['target_table_tmp']    = '"{target_table_tmp}"'.format (**parameters)

    parameters['target']        = '{target_db}.{target_table}'.format (**parameters)
    parameters['target_lac']    = '{target_db}.{target_table_lac}'.format (**parameters)
    parameters['target_attlac'] = '{target_db}.{target_table_attlac}'.format (**parameters)
    parameters['target_tmp']    = '{target_db}.{target_table_tmp}'.format (**parameters)

    parameters['table_mask']    = "Acts%02d%%" % args.chapter if args.chapter else "Acts%"

    return parameters


def message (level, s):
    """
    Print information if needed.
    """
    if args.verbose >= level:
        delta = datetime.datetime.now () - args.start_time
        print ("[{time}] {msg}".format (time = delta, msg = s))


def cursor_get_value (cursor):
    for row in cursor.fetchall ():
        return row[0]


def execute (cursor, sql, parameters):
    sql = sql.format (**parameters)
    message (3, sql.rstrip () + ';')
    cursor.execute (sql, parameters)
    message (3, "%d rows" % cursor.rowcount)


def tabulate(cursor, stream = sys.stdout):
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


def fix (cursor, msg, sql, sql_fix, parameters):
    # print unfixed values
    if args.verbose >= 3:
        execute (cursor, sql, parameters)
        if cursor.rowcount > 0:
            message (3, "*** WARNING: {msg} ***".format (msg = msg))
            tabulate (cursor)
    # apply fix
    if sql_fix:
        execute (cursor, sql_fix, parameters)
        # print fixed values
        execute (cursor, sql, parameters)
        if cursor.rowcount > 0:
            message (0, "*** ERROR: {msg} ***".format (msg = msg))
            tabulate (cursor)


def print_stats (dba, parameters):
    cursor = dba.cursor ()

    cursor.execute ("SELECT count(distinct hs) FROM {target}".format (**parameters))
    hs = cursor_get_value (cursor)
    message (1, "hs       = {cnt}".format (cnt = hs))

    cursor.execute ("SELECT count(distinct anfadr, endadr) FROM {target}".format (**parameters))
    passages = cursor_get_value (cursor)
    message (1, "passages = {cnt}".format (cnt = passages))

    message (1, "hs * passages      = {cnt}".format (cnt = hs * passages))

    cursor.execute ("SELECT count(*) FROM {target}".format (**parameters))
    att = cursor_get_value (cursor)
    cursor.execute ("SELECT count(*) FROM {target_lac}".format (**parameters))
    lac = cursor_get_value (cursor)
    cursor.execute ("SELECT count(*) FROM {target_attlac}".format (**parameters))
    attlac = cursor_get_value (cursor)

    message (1, "rows in att        = {cnt}".format (cnt = att))
    message (1, "rows in lac        = {cnt}".format (cnt = lac))
    message (1, "rows in attlac     = {cnt}".format (cnt = attlac))
    message (1, "rows in att+attlac = {cnt}".format (cnt = att + attlac))
    message (1, "delta              = {cnt}".format (cnt = (att + attlac) - (hs * passages)))

    # sum (passages in chapter * mss with chapter)

    cursor.execute ("""
    SELECT sum(pas_cnt * ch.ms_cnt)

    FROM
      (select kapanf, count(distinct anfadr, endadr) as pas_cnt FROM {target} GROUP BY kapanf) AS pas

    JOIN
      (select kapanf, count(distinct hs) as ms_cnt FROM {target} GROUP BY kapanf) AS ch

    ON ch.kapanf = pas.kapanf

    """.format (**parameters))
    pas = cursor_get_value (cursor)

    message (1, "chap * ms * pas    = {cnt}".format (cnt = pas))
