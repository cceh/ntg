# -*- encoding: utf-8 -*-

""" This module contains functions for database access. """

import collections
import csv
import configparser
import datetime
import io
import logging
import os
import os.path

import networkx as nx
import sqlalchemy
from sqlalchemy.sql import text

from .tools import log
from .config import args


# mimics mysql Ver 15.1 Distrib 10.1.29-MariaDB
MYSQL_DEFAULT_FILES  = ( '/etc/my.cnf', '/etc/mysql/my.cnf', '~/.my.cnf' )
MYSQL_DEFAULT_GROUPS = ( 'mysql', 'client', 'client-server', 'client-mariadb' )


def execute (conn, sql, parameters, debug_level = logging.DEBUG):
    sql = sql.strip ().format (**parameters)
    start_time = datetime.datetime.now ()
    result = conn.execute (text (sql), parameters)
    log (debug_level, '%d rows in %.3fs', result.rowcount, (datetime.datetime.now () - start_time).total_seconds ())
    return result


def executemany (conn, sql, parameters, param_array, debug_level = logging.DEBUG):
    sql = sql.strip ().format (**parameters)
    start_time = datetime.datetime.now ()
    result = conn.execute (text (sql), param_array)
    log (debug_level, '%d rows in %.3fs', result.rowcount, (datetime.datetime.now () - start_time).total_seconds ())
    return result


def executemany_raw (conn, sql, parameters, param_array, debug_level = logging.DEBUG):
    sql = sql.strip ().format (**parameters)
    start_time = datetime.datetime.now ()
    result = conn.execute (sql, param_array)
    log (debug_level, '%d rows in %.3fs', result.rowcount, (datetime.datetime.now () - start_time).total_seconds ())
    return result


def rollback (conn, debug_level = logging.DEBUG):
    start_time = datetime.datetime.now ()
    result = conn.execute ('ROLLBACK')
    log (debug_level, 'rollback in %.3fs', (datetime.datetime.now () - start_time).total_seconds ())
    return result


# def execute_pandas (conn, sql, parameters, debug_level = logging.DEBUG):
#     sql = sql.format (**parameters)
#     log (debug_level, sql.rstrip () + ';')
#     return pd.read_sql_query (text (sql), conn, parameters)

def _debug (conn, msg, sql, parameters, level):
    # print values
    if args.log_level <= level:
        result = execute (conn, sql, parameters)
        if result.rowcount > 0:
            log (level, msg + '\n' + tabulate (result))

def debug (conn, msg, sql, parameters):
    _debug (conn, msg, sql, parameters, logging.DEBUG)

def warn (conn, msg, sql, parameters):
    _debug (conn, msg, sql, parameters, logging.WARNING)


def fix (conn, msg, check_sql, fix_sql, parameters):
    """Check and eventually fix errors.

    Executes the check_sql statement to check for a possible error conditions
    and, if rows emerge, prints a warning and executes the fix_sql statement.
    The fix_sql statement should be written as to fix the errors reported by the
    check_sql statement.  Finally it executes the check_sql statement again and
    reports an error if the error condition still exists.

    :param str msg:       The warning / error message
    :param str check_sql: The sql statement that checks for the error condition.
    :param str fix_sql:   The sql statement that fixes the error condition.

    """

    # print unfixed values
    result = execute (conn, check_sql, parameters)
    if result.rowcount > 0:
        # apply fix
        if args.log_level <= logging.WARNING:
            log (logging.WARNING, msg + '\n' + tabulate (result))
        if fix_sql:
            execute (conn, fix_sql, parameters)
            # print fixed values
            result = execute (conn, check_sql, parameters)
            if result.rowcount > 0:
                log (logging.ERROR, msg + '\n' + tabulate (result))


def to_csv (fields, rows):
    fp = io.StringIO ()
    writer = csv.DictWriter (fp, fields, restval='', extrasaction='raise', dialect='excel')
    writer.writeheader ()
    for r in rows:
        writer.writerow (r._asdict ())
    return fp.getvalue ()


def tabulate (res):
    """ Format and output a rowset

    Uses an output format similar to the one produced by the mysql commandline
    utility.

    """
    cols = range (0, len (res.keys ()))
    rowlen = dict()
    a = []

    def line ():
        for i in cols:
            a.append ('+')
            a.append ('-' * (rowlen[i] + 2))
        a.append ('+\n')

    # convert database types to strings
    rows = []
    for row in res.fetchall():
        newrow = []
        for i in cols:
            if row[i] is None:
                newrow.append ('NULL')
            else:
                newrow.append (str (row[i]))
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
        a.append ('| {:<{align}} '.format (res.keys ()[i], align = rowlen[i]))
    a.append ('|\n')
    line ()

    # output rows
    for row in rows:
        for i in cols:
            a.append ('| {:<{align}} '.format (row[i], align = rowlen[i]))
        a.append ('|\n')
    line ()
    a.append ('%d rows\n' % len (rows))

    return ''.join (a)


def truncate_editor_tables (conn):
    execute (conn, """
    TRUNCATE cliques_tts, ms_cliques_tts, locstem_tts, notes_tts RESTART IDENTITY;
    TRUNCATE cliques, ms_cliques, locstem, notes RESTART IDENTITY;
    """, {})


def init_default_cliques (conn):
    """Generate a default cliques table.

    In a default cliques table there is a default clique '1' for every reading
    in the readings table.

    """

    execute (conn, """
    ALTER TABLE cliques DISABLE TRIGGER cliques_trigger;
    INSERT INTO cliques (pass_id, labez, clique, user_id_start)
    SELECT pass_id, labez, '1', 0
    FROM readings r;
    ALTER TABLE cliques ENABLE TRIGGER cliques_trigger;
    """, {})


def init_default_ms_cliques (conn):
    """Generate a default ms_cliques table.

    In a default ms_cliques table there is a default clique '1' for every reading
    in the apparatus table.

    """

    execute (conn, """
    ALTER TABLE ms_cliques DISABLE TRIGGER ms_cliques_trigger;
    INSERT INTO ms_cliques (ms_id, pass_id, labez, clique, user_id_start)
    SELECT a.ms_id, a.pass_id, a.labez, '1', 0
    FROM apparatus a;
    ALTER TABLE ms_cliques ENABLE TRIGGER ms_cliques_trigger;
    """, {})


def init_default_locstem (conn):
    """Generate a default locstem table.

    In a default LocStemEd, labez 'a' is the original reading and every other
    reading depends on labez 'a', except in a Fehlvers, where 'b' is of unknown
    origin and every other reading depends on 'b'.

    """

    execute (conn, """
    ALTER TABLE locstem DISABLE TRIGGER locstem_trigger;
    """, {})

    # insert 'a' as original reading (or 'b' as unknown if Fehlvers)
    execute (conn, """
    INSERT INTO locstem (pass_id, labez, clique, source_labez, source_clique, original, user_id_start)
    SELECT pass_id, 'a', '1', NULL, NULL, true, 0
    FROM passages p
    WHERE NOT fehlvers;

    INSERT INTO locstem (pass_id, labez, clique, source_labez, source_clique, original, user_id_start)
    SELECT pass_id, 'b', '1', NULL, NULL, false, 0
    FROM passages p
    WHERE fehlvers;
    """, {})

    # make other readings dependent on 'a' (or 'b' in Fehlvers)
    execute (conn, """
    INSERT INTO locstem (pass_id, labez, clique, source_labez, source_clique, original, user_id_start)
    SELECT c.pass_id, c.labez, c.clique, 'a', '1', false, 0
    FROM cliques_view c
      JOIN passages p USING (pass_id)
    WHERE NOT p.fehlvers AND c.labez != 'a' AND c.labez !~ '^z[u-z]';

    INSERT INTO locstem (pass_id, labez, clique, source_labez, source_clique, original, user_id_start)
    SELECT c.pass_id, c.labez, c.clique, 'b', '1', false, 0
    FROM cliques_view c
      JOIN passages p USING (pass_id)
    WHERE p.fehlvers AND c.labez != 'b' AND c.labez !~ '^z[u-z]'
    """, {})

    execute (conn, """
    ALTER TABLE locstem ENABLE TRIGGER locstem_trigger;
    """, {})


class MySQLEngine ():
    """ Database Interface """

    def __init__ (self, fn = MYSQL_DEFAULT_FILES, group = MYSQL_DEFAULT_GROUPS, db = ''):
        # self.params is only needed to configure the MySQL FDW in Postgres
        self.params = self.get_connection_params (fn, group)
        self.params['database'] = db

        url = sqlalchemy.engine.url.URL (**(dict (self.params, password = 'password')))
        log (logging.DEBUG, 'MySQLEngine: Connecting to URL: {url}'.format (url = url))
        url = sqlalchemy.engine.url.URL (**self.params)
        self.engine = sqlalchemy.create_engine (url)

        self.connection = self.connect ()


    @staticmethod
    def get_connection_params (filenames, groups):
        if isinstance (filenames, str):
            filenames = [ filenames ]
        if isinstance (groups, str):
            groups = [ groups ]

        filenames = map (os.path.expanduser, filenames)
        config = configparser.ConfigParser ()
        config.read (filenames)
        parameters = {
            'drivername' : 'drivername',
            'host' : 'host',
            'port' : 'port',
            'database' : 'database',
            'user' : 'username',
            'password' : 'password',
        }
        options = {
            'default-character-set' : 'charset',
        }
        params = {
            'drivername' : 'mysql',
            'host' : 'localhost',
            'port' : '3306',
            'query' : {
                'charset' : 'utf8mb4',
            }
        }

        for group in groups:
            section = config[group]
            for key, alias in parameters.items ():
                if key in section:
                    params[alias] = section[key].strip ('"')
            for key, alias in options.items ():
                if key in section:
                    params['query'][alias] = section[key].strip ('"')
        return params


    def connect (self):
        connection = self.engine.connect ()
        # Make MySQL more compatible with other SQL databases
        connection.execute ("SET sql_mode='ANSI'")
        return connection


class PostgreSQLEngine ():
    """ PostgreSQL Database Interface """

    @staticmethod
    def receive_checkout (dbapi_connection, connection_record, connection_proxy):
        """Set a default for the postgres variable ntg.user_id that is used by
        :ref:`tts` tables.

        """

        # just give a default value so postgres won't choke.  the actual user is
        # set in editor.py
        dbapi_connection.cursor ().execute ("SET ntg.user_id = 0")


    def __init__ (self, **kwargs):

        args = self.get_connection_params (kwargs)

        self.url = 'postgresql+psycopg2://{user}@{host}:{port}/{database}?sslmode=disable&server_side_cursors'.format (**args)

        log (logging.DEBUG, "PostgreSQLEngine: Connecting to URL: {url}".format (url = self.url))

        self.engine = sqlalchemy.create_engine (
            self.url,
            use_batch_mode = True
        )

        self.params = args

        sqlalchemy.event.listen (self.engine, 'checkout', self.receive_checkout)


    def connect (self):
        return self.engine.connect ()


    def get_connection_params (self, args = {}):
        """Get sqlalchemy connection parameters.

        Try to get the connection parameters in turn from these sources:

        1. get host, port, database, user from args
        2. get PGHOST, PGPORT, PGDATABASE, PGUSER from args
        3. get PGHOST, PGPORT, PGDATABASE, PGUSER from environment
        4. use defaults

        N.B. The postgres client library automatically reads the password from
        the file :file:`~/.pgpass`.  It should be configured there.

        """

        defaults = {
            'host'     : 'localhost',
            'port'     : '5432',
            'database' : 'ntg',
            'user'     : 'ntg',
        }
        res = {}

        for p in defaults:
            pu = 'PG' + p.upper ()
            res[p] = args.get (p) or args.get (pu) or os.environ.get (pu) or defaults[p]

        return res

    def vacuum (self):
        """Vacuum the database."""

        # turn off auto-transaction because vacuum won't work in a transaction
        connection = self.engine.raw_connection ()
        connection.set_isolation_level (0)
        connection.cursor ().execute ("VACUUM FULL ANALYZE")
        log (logging.INFO, ''.join (connection.notices))


def local_stemma_to_nx (conn, pass_id, add_isolated_roots = False):
    """Load a passage from the database into an nx Graph.

    :param bool add_isolated_roots: Add an '*' or '?' node even if they are
                                    isolated.  Needed in edit mode.

    """

    res = execute (conn, """
    SELECT labez,
           clique,
           labez_clique (labez, clique) AS labez_clique,
           source_labez,
           source_clique,
           labez_clique (source_labez, source_clique) AS source_labez_clique,
           original
    FROM locstem l
    WHERE labez !~ '^z[u-z]' AND pass_id = :pass_id
    ORDER BY labez, clique
    """, dict (pass_id = pass_id))

    Variant = collections.namedtuple ('stemma_json_variant',
                                      'labez clique labez_clique source_labez source_clique source_labez_clique original')

    rows = list (map (Variant._make, res))

    graph = nx.DiGraph ()

    more_params = dict ()
    if add_isolated_roots:
        more_params['draggable'] = '1'
        more_params['droptarget'] = '1'

    for row in rows:
        graph.add_node (row.labez_clique, label = row.labez_clique,
                    labez = row.labez, clique = row.clique, labez_clique = row.labez_clique,
                    **more_params)

        if row.source_labez_clique is None:
            if row.original:
                graph.add_edge ('*', row.labez_clique)
            else:
                graph.add_edge ('?', row.labez_clique)
        else:
            graph.add_edge (row.source_labez_clique, row.labez_clique)

    more_params = dict ()
    if add_isolated_roots:
        # Add '*' and '?' nodes
        graph.add_node ('*')
        graph.add_node ('?')
        more_params['droptarget'] = '1'

    if '*' in graph:
        graph.node['*'].update (label = '*', labez='*', clique='0', labez_clique='*', **more_params)
    if '?' in graph:
        graph.node['?'].update (label = '?', labez='?', clique='0', labez_clique='?', **more_params)

    return graph
