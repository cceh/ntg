# -*- encoding: utf-8 -*-

"""Database Interface Module

How To Configure Database Access
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The MySQL database:

Edit (or create) your ~/.my.cnf and add these sections: ::

    [ntg-local]
    host="localhost"
    database="apparat"
    user="username"
    password="password"
    default-character-set="utf8"

    [ntg-remote]
    host="remote"
    database="apparat"
    user="username"
    password="password"
    default-character-set="utf8"

Replace *username* and *password* with your own username and password.
**Make sure ~/.my.cnf is readable only by yourself!**

The Postgres database:

1. Create a postgres user. Login to postgres as superuser and say: ::

    CREATE USER <username> CREATEDB PASSWORD '<password>';

2. Edit (or create) your ~/.pgpass and add this line: ::

    localhost:5432:ntg:<username>:<password>

Replace <username> and <password> with your own username and password.
**Make sure ~/.pgpass is readable only by yourself!**


"""

import os
import os.path

import sqlalchemy
import sqlalchemy.types

from sqlalchemy import *
from sqlalchemy.dialects import postgresql
from sqlalchemy.ext import compiler
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.schema import DDLElement
from sqlalchemy.sql import table, text

import sqlalchemy_utils
from sqlalchemy_utils import IntRangeType

# import pandas as pd

from .tools import message, tabulate
from .config import args

MYSQL_DEFAULT_GROUP  = "ntg-local"


class CoerceInteger (sqlalchemy.types.TypeDecorator):
    """ Coerce numpy integers to python integers
    before passing off to the database."""

    impl = sqlalchemy.types.Integer

    def process_bind_param (self, value, dialect):
        return int (value)

    def process_result_value (self, value, dialect):
        return value


class CreateView (DDLElement):
    def __init__ (self, name, sql):
        self.name = name
        self.sql = sql

class DropView (DDLElement):
    def __init__ (self, name):
        self.name = name

@compiler.compiles(CreateView)
def compile (element, compiler, **kw):
    return "CREATE OR REPLACE VIEW %s AS %s" % (element.name, element.sql.strip ())

@compiler.compiles(DropView)
def compile (element, compiler, **kw):
    return "DROP VIEW IF EXISTS %s" % (element.name)

def view (name, metadata, sql):
    CreateView (name, sql).execute_at ('after-create', metadata)
    DropView (name).execute_at ('before-drop', metadata)


def execute (conn, sql, parameters, debug_level = 3):
    sql = sql.strip ().format (**parameters)
    message (debug_level, sql.rstrip () + ';')
    result = conn.execute (text (sql), parameters)
    message (debug_level, "%d rows" % result.rowcount)
    return result


def executemany (conn, sql, parameters, param_array, debug_level = 3):
    sql = sql.strip ().format (**parameters)
    message (debug_level, sql.rstrip () + ';')
    result = conn.execute (text (sql), param_array)
    message (debug_level, "%d rows" % result.rowcount)
    return result


def executemany_raw (conn, sql, parameters, param_array, debug_level = 3):
    sql = sql.strip ().format (**parameters)
    message (debug_level, sql.rstrip () + ';')
    result = conn.execute (sql, param_array)
    message (debug_level, "%d rows" % result.rowcount)
    return result


# def execute_pandas (conn, sql, parameters, debug_level = 3):
#     sql = sql.format (**parameters)
#     message (debug_level, sql.rstrip () + ';')
#     return pd.read_sql_query (text (sql), conn, parameters)

def debug (conn, msg, sql, parameters):
    # print values
    if args.verbose >= 3:
        result = execute (conn, sql, parameters)
        if result.rowcount > 0:
            message (3, "*** DEBUG: {msg} ***".format (msg = msg), True)
            tabulate (result)


def fix (conn, msg, check_sql, fix_sql, parameters):
    """Check and eventually fix errors.

    Executes the check_sql statement to check for error conditions and, if rows
    emerge, executes the fix_sql statement.  The fix_sql statement should be
    written as to fix the errors reported by the check_sql statement.  Finally
    it executes the check_sql statement again and reports an error if the
    condition still exists.

    """

    # print unfixed values
    result = execute (conn, check_sql, parameters)
    if result.rowcount > 0:
        # apply fix
        if args.verbose >= 3:
            message (3, "*** WARNING: {msg} ***".format (msg = msg), True)
            tabulate (result)
        if fix_sql:
            execute (conn, fix_sql, parameters)
            # print fixed values
            result = execute (conn, check_sql, parameters)
            if result.rowcount > 0:
                message (0, "*** ERROR: {msg} ***".format (msg = msg), True)
                tabulate (result)


class DBA (object):
    """ Database Interface """

    def __init__ (self, group = None, db = None):
        if group is None:
            group = MYSQL_DEFAULT_GROUP
        if db is None:
            db = ''

        message (3, "Connecting to db and reading init group: {group}".format (group = group), True)

        self.engine = create_engine (
            "mysql:///{db}?read_default_group={group}".format (db = db, group = group))

        sqlalchemy.event.listen (self.engine, 'connect', on_connect)

        self.connection = self.connect ()

    def connect (self):
        connection = self.engine.connect ()
        # Make MySQL more compatible with other SQL databases
        connection.execute ("SET sql_mode='ANSI'")
        return connection


#@event.listens_for(eng, "first_connect", insert=True)  # make sure we're the very first thing
#@event.listens_for(eng, "connect")
def on_connect (dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor ()
    cursor.execute ("SET sql_mode = 'ANSI'")


class MySQLEngine (object):
    """ Database Interface """

    def __init__ (self, group = None, db = None):
        if group is None:
            group = MYSQL_DEFAULT_GROUP
        if db is None:
            db = ''

        message (3, "MySQLEngine: Reading init group: {group}".format (group = group), True)
        message (3, "MySQLEngine: Connecting to db: {db}".format (db = db), True)

        self.engine = create_engine (
            "mysql:///{db}?read_default_group={group}".format (db = db, group = group))

        self.connection = self.connect ()

    def connect (self):
        connection = self.engine.connect ()
        # Make MySQL more compatible with other SQL databases
        connection.execute ("SET sql_mode='ANSI'")
        return connection


class PostgreSQLEngine (object):
    """ PostgreSQL Database Interface """

    def __init__ (self, **kwargs):

        args = self.get_connection_params (kwargs)

        url = "postgresql+psycopg2://{user}:{password}@{host}:{port}/{database}?sslmode=disable".format (**args)

        if (not sqlalchemy_utils.functions.database_exists (url)):
            message (3, "PostgreSQLEngine: Creating database '{database}'".format (**args), True)
            sqlalchemy_utils.functions.create_database (url)

        message (3, "PostgreSQLEngine: Connecting to postgres database '{database}' as user '{user}'"
                 .format (**args), True)

        self.engine = create_engine (url + "?server_side_cursors")


    def connect (self):
        return self.engine.connect ()


    def get_connection_params (self, args = None):
        """ Get connection parameters from environment. """

        defaults = {
            'host'     : 'localhost',
            'port'     : '5432',
            'database' : 'ntg',
            'user'     : 'ntg',
        }

        if args is None:
            args = {}

        params = ('host', 'port', 'database', 'user') # order must match ~/.pgpass
        res = {}

        for param in params:
            res[param] = args.get (param) or os.environ.get ('PG' + param.upper ()) or defaults[param]

        # scan ~/.pgpass for password
        pgpass = os.path.expanduser ("~/.pgpass")
        try:
            with open (pgpass, "r") as f:
                for line in f.readlines ():
                    line = line.strip ()
                    if line == '' or line.startswith ('#'):
                        continue
                    # format: hostname:port:database:username:password
                    fields = line.split (':')
                    if all ([field == '*' or field == res[param]
                             for field, param in zip (fields, params)]):
                        res['password'] = fields[4]
                        break

        except IOError:
            print ("Error: could not open %s for reading" % pgpass)

        return res


def create_functions (dest, parameters):
    execute (dest, """
    DROP FUNCTION IF EXISTS char_labez (INTEGER)
    """, parameters)

    execute (dest, """
    DROP FUNCTION IF EXISTS ord_labez (CHAR (2))
    """, parameters)

    execute (dest, """
    CREATE FUNCTION char_labez (l INTEGER) RETURNS CHAR (3) AS
    $$
        SELECT CASE WHEN l > 0 THEN chr (l + 96) ELSE 'z' END;
    $$
    LANGUAGE SQL IMMUTABLE;
    """, parameters)

    execute (dest, """
    CREATE FUNCTION ord_labez (l CHAR (2)) RETURNS INTEGER AS
    $$
        SELECT CASE WHEN ascii (l) >= 122 THEN 0 ELSE ascii (l) - 96 END;
    $$
    LANGUAGE SQL IMMUTABLE;
    """, parameters)


Base = declarative_base ()

class Att (Base):
    __tablename__ = 'att'

    id        = Column (Integer,       primary_key = True, autoincrement = True)
    buch      = Column (Integer,       nullable = False)
    kapanf    = Column (Integer,       nullable = False)
    versanf   = Column (Integer,       nullable = False)
    wortanf   = Column (Integer,       nullable = False)
    kapend    = Column (Integer,       nullable = False)
    versend   = Column (Integer,       nullable = False)
    wortend   = Column (Integer,       nullable = False)
    hsnr      = Column (Integer,       nullable = False, index = True)
    hs        = Column (String(32),    nullable = False, index = True)
    anfadr    = Column (Integer,       nullable = False, index = True)
    endadr    = Column (Integer,       nullable = False, index = True)
    labez     = Column (String(32),    nullable = False, server_default = '')
    labezsuf  = Column (String(32),    server_default = '')
    lemma     = Column (String(1024),  server_default = '')
    lesart    = Column (String(1024),  server_default = '')
    suffix2   = Column (String(32),    server_default = '')
    kontrolle = Column (String(1),     server_default = '')
    fehler    = Column (Integer,       server_default = '0')
    suff      = Column (String(32),    server_default = '')
    vid       = Column (String(32),    server_default = '')
    vl        = Column (String(32),    server_default = '')
    korr      = Column (String(32),    server_default = '')
    lekt      = Column (String(32),    server_default = '')
    komm      = Column (String(32),    server_default = '')
    anfalt    = Column (Integer)
    endalt    = Column (Integer)
    labezalt  = Column (String(32),    server_default = '')
    lasufalt  = Column (String(32),    server_default = '')
    base      = Column (String(1),     server_default = '')
    over      = Column (String(1),     server_default = '')
    comp      = Column (String(1),     server_default = '')
    over1     = Column (String(1),     server_default = '')
    comp1     = Column (String(1),     server_default = '')
    printout  = Column (String(32),    server_default = '')
    category  = Column (String(1),     server_default = '')
    irange    = Column (IntRangeType,  nullable = False)
    created   = Column (DateTime)

    __table_args__ = (
        UniqueConstraint ('hs', 'irange', name = 'unique_att_hs_irange'),
    )


class Lac (Base): # same as class Att
    __tablename__ = 'lac'

    id        = Column (Integer,       primary_key = True, autoincrement = True)
    buch      = Column (Integer,       nullable = False)
    kapanf    = Column (Integer,       nullable = False)
    versanf   = Column (Integer,       nullable = False)
    wortanf   = Column (Integer,       nullable = False)
    kapend    = Column (Integer,       nullable = False)
    versend   = Column (Integer,       nullable = False)
    wortend   = Column (Integer,       nullable = False)
    hsnr      = Column (Integer,       nullable = False)
    hs        = Column (String(32),    nullable = False)
    anfadr    = Column (Integer,       nullable = False)
    endadr    = Column (Integer,       nullable = False)
    labez     = Column (String(32),    nullable = False, server_default = '')
    labezsuf  = Column (String(32),    server_default = '')
    lemma     = Column (String(1024),  server_default = '')
    lesart    = Column (String(1024),  server_default = '')
    suffix2   = Column (String(32),    server_default = '')
    kontrolle = Column (String(1),     server_default = '')
    fehler    = Column (Integer,       server_default = '0')
    suff      = Column (String(32),    server_default = '')
    vid       = Column (String(32),    server_default = '')
    vl        = Column (String(32),    server_default = '')
    korr      = Column (String(32),    server_default = '')
    lekt      = Column (String(32),    server_default = '')
    komm      = Column (String(32),    server_default = '')
    anfalt    = Column (Integer)
    endalt    = Column (Integer)
    labezalt  = Column (String(32),    server_default = '')
    lasufalt  = Column (String(32),    server_default = '')
    base      = Column (String(1),     server_default = '')
    over      = Column (String(1),     server_default = '')
    comp      = Column (String(1),     server_default = '')
    over1     = Column (String(1),     server_default = '')
    comp1     = Column (String(1),     server_default = '')
    printout  = Column (String(32),    server_default = '')
    category  = Column (String(1),     server_default = '')
    irange    = Column (IntRangeType,  nullable = False)
    created   = Column (DateTime)

    __table_args__ = (
        Index ('lac_irange_gist_idx', 'irange', postgresql_using = 'gist'),
        UniqueConstraint ('hs', 'irange', name = 'unique_lac_hs_irange')
    )

if 0:
    class VP (Base):
        __tablename__ = 'vp'

        id        = Column (Integer,       primary_key = True, autoincrement = True)
        anfadr    = Column (Integer,       nullable = False)
        endadr    = Column (Integer,       nullable = False)
        bzdef     = Column (Integer,       nullable = False, server_default = '0')
        check     = Column (String (1),    nullable = False, server_default = '')


    class Rdg (Base):
        __tablename__ = 'rdg'

        id        = Column (Integer,       primary_key = True, autoincrement = True)
        anfadr    = Column (Integer,       nullable = False)
        endadr    = Column (Integer,       nullable = False)
        labez     = Column (String (32),   nullable = False, server_default = '')
        labezsuf  = Column (String (32),   nullable = False, server_default = '')
        lesart    = Column (String (1024), nullable = False, server_default = '')
        bz        = Column (Integer,       nullable = False, server_default = '0')
        bzdef     = Column (Integer,       nullable = False, server_default = '0')
        byz       = Column (String (1),    nullable = False, server_default = '')
        check     = Column (String (1),    nullable = False, server_default = '')

        __table_args__ = (
            UniqueConstraint ('anfadr', 'endadr', 'labez', name = 'unique_rdg_anfadr_endadr_labez'),
        )


    class Witn (Base):
        __tablename__ = 'witn'

        id        = Column (Integer,       primary_key = True, autoincrement = True)
        anfadr    = Column (Integer,       nullable = False)
        endadr    = Column (Integer,       nullable = False)
        labez     = Column (String (32),   nullable = False, server_default = '')
        labezsuf  = Column (String (32),   nullable = False, server_default = '')
        hsnr      = Column (Integer,       nullable = False)
        hs        = Column (String (32),   nullable = False)


    class MsListVal (Base):
        __tablename__ = 'mslistval'

        id        = Column (Integer,       primary_key = True, autoincrement = True)
        hsnr      = Column (Integer,       nullable = False)
        hs        = Column (String (32),   nullable = False)
        chapter   = Column (Integer,       nullable = False)
        sumtxt    = Column (Integer,       nullable = False, server_default = '0')
        summt     = Column (Integer,       nullable = False, server_default = '0')
        uemt      = Column (Integer,       nullable = False, server_default = '0')
        qmt       = Column (Float,         nullable = False, server_default = '0.0')
        check     = Column (String (1),    nullable = False, server_default = '')


    class VG (Base):
        __tablename__ = 'vg'

        id        = Column (Integer,       primary_key = True, autoincrement = True)
        hsnr      = Column (Integer,       nullable = False)
        hsnr2     = Column (Integer,       nullable = False)
        chapter   = Column (Integer,       nullable = False)
        sumtxt    = Column (Integer,       nullable = False, server_default = '0')
        summt     = Column (Integer,       nullable = False, server_default = '0')
        uemt      = Column (Integer,       nullable = False, server_default = '0')
        qmt       = Column (Float,         nullable = False, server_default = '0.0')
        check     = Column (String (1),    nullable = False, server_default = '')


Base2 = declarative_base ()

class Manuscripts (Base2):
    __tablename__ = 'manuscripts'

    id        = Column (Integer,       primary_key = True, autoincrement = True)
    hsnr      = Column (Integer,       nullable = False, unique = True)
    hs        = Column (String (32),   nullable = False, unique = True)
    length    = Column (Integer)


class Chapters (Base2):
    __tablename__ = 'chapters'

    id        = Column (Integer,       primary_key = True, autoincrement = True)
    ms_id     = Column (Integer,       nullable = False)
    hsnr      = Column (Integer,       nullable = False)
    hs        = Column (String (32),   nullable = False)
    chapter   = Column (Integer,       nullable = False)
    length    = Column (Integer)

    __table_args__ = (
        UniqueConstraint ('ms_id', 'chapter', name = 'unique_chapters_ms_id_chapter'),
        UniqueConstraint ('hsnr',  'chapter', name = 'unique_chapters_hsnr_chapter'),
    )


class Passages (Base2):
    __tablename__ = 'passages'

    id        = Column (Integer,       primary_key = True, autoincrement = True)
    buch      = Column (Integer,       nullable = False)
    kapanf    = Column (Integer,       nullable = False)
    versanf   = Column (Integer,       nullable = False)
    wortanf   = Column (Integer,       nullable = False)
    kapend    = Column (Integer,       nullable = False)
    versend   = Column (Integer,       nullable = False)
    wortend   = Column (Integer,       nullable = False)
    anfadr    = Column (Integer,       nullable = False)
    endadr    = Column (Integer,       nullable = False)
    irange    = Column (IntRangeType,  nullable = False)
    lemma     = Column (String(1024),  nullable = False, server_default = '')
    comp      = Column (Boolean,       nullable = False, server_default = 'False')
    fehlvers  = Column (Boolean,       nullable = False, server_default = 'False')

    __table_args__ = (
        UniqueConstraint ('irange', name = 'unique_passages_irange'),
    )


class Readings (Base2):
    __tablename__ = 'readings'

    id        = Column (Integer,       primary_key = True, autoincrement = True)
    pass_id   = Column (Integer,       ForeignKey ('passages.id'), nullable = False, index = True)
    labez     = Column (String (2),    nullable = False, server_default = '')
    labezsuf  = Column (String (32),   nullable = False, server_default = '')
    lesart    = Column (String(1024),  nullable = False, server_default = '')

    __table_args__ = (
        UniqueConstraint ('pass_id', 'labez', 'labezsuf', name = 'unique_readings_pass_id_labez_labezsuf'),
    )


class Variants (Base2):
    __tablename__ = 'var'

    id        = Column (Integer,       primary_key = True, autoincrement = True)
    ms_id     = Column (Integer,       ForeignKey ('manuscripts.id'), nullable = False, index = True)
    pass_id   = Column (Integer,       ForeignKey ('passages.id'),    nullable = False, index = True)
    labez     = Column (String (2),    nullable = False, server_default = '')
    labezsuf  = Column (String (32),   nullable = False, server_default = '')
    varid     = Column (String (2),    nullable = False, server_default = '')
    varnew    = Column (String (2),    nullable = False, server_default = '')

    __table_args__ = (
        UniqueConstraint ('ms_id', 'pass_id', name = 'unique_var_ms_id_pass_id'),
    )


class LocStemEd (Base2):
    __tablename__ = 'locstemed'

    id         = Column (Integer,       primary_key = True, autoincrement = True)
    pass_id    = Column (Integer,       ForeignKey ('passages.id'), nullable = False, index = True)
    varid      = Column (String (2),    nullable = False)
    varnew     = Column (String (2),    nullable = False, server_default = '')
    s1         = Column (String (2),    nullable = False, server_default = '')
    s2         = Column (String (2),    nullable = False, server_default = '')
    parents    = Column (Integer,       nullable = False, server_default = '0')
    ancestors  = Column (Integer,       nullable = False, server_default = '0')
    varnewmask = Column (Integer,       nullable = False, server_default = '0')
    s1mask     = Column (Integer,       nullable = False, server_default = '0')
    s2mask     = Column (Integer,       nullable = False, server_default = '0')
    prs1       = Column (String (2),    nullable = False, server_default = '')
    prs2       = Column (String (2),    nullable = False, server_default = '')
    check      = Column (String (2),    nullable = False, server_default = '')
    check2     = Column (String (2),    nullable = False, server_default = '')
    w          = Column (String (1),    nullable = False, server_default = '')

    __table_args__ = (
        UniqueConstraint ('pass_id', 'varnew', 's1', name = 'unique_locstemed_pass_id_varnew_s1'),
        Index ('index_locstemed_pass_id_varnew', 'pass_id', 'varnew'),
    )


class Affinity (Base2):
    __tablename__ = 'affinity'

    id        = Column (Integer,       primary_key = True, autoincrement = True)
    chapter   = Column (Integer,       nullable = False)
    id1       = Column (Integer,       ForeignKey ('manuscripts.id'), nullable = False)
    id2       = Column (Integer,       ForeignKey ('manuscripts.id'), nullable = False)
    common    = Column (Integer,       nullable = False)
    equal     = Column (Integer,       nullable = False)
    older     = Column (Integer,       nullable = False)
    newer     = Column (Integer,       nullable = False)
    unclear   = Column (Integer,       nullable = False)
    p_older   = Column (Integer,       nullable = False)
    p_newer   = Column (Integer,       nullable = False)
    p_unclear = Column (Integer,       nullable = False)
    affinity  = Column (Float,         nullable = False, index = True)

    __table_args__ = (
        UniqueConstraint ('chapter', 'id1', 'id2', name = 'unique_affinity_chapter_id1_id2'),
    )


view ('var_view', Base2.metadata, """
    SELECT ms.hs, ms.hsnr, p.anfadr, p.endadr, var.*
    FROM var
    JOIN passages p     ON var.pass_id = p.id
    JOIN manuscripts ms ON var.ms_id   = ms.id
    """)


class GephiNodes (Base2):
    __tablename__ = 'nodes'

    id        = Column (String (32),   primary_key = True)
    label     = Column (String (32))
    color     = Column (String (32))
    nodecolor = Column (String (32))
    nodesize  = Column (Float)
    x         = Column (Float)
    y         = Column (Float)
    size      = Column (Float)


class GephiEdges (Base2):
    __tablename__ = 'edges'

    id        = Column (String (65),   primary_key = True)
    label     = Column (String (32))
    source    = Column (String (32),   nullable = False)
    target    = Column (String (32),   nullable = False)
    weight    = Column (Float,         nullable = False, server_default = '1.0')

    __table_args__ = (
        UniqueConstraint ('source', 'target', name = 'unique_gephi_edges_source_target'),
    )
