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

import configparser
import datetime
import logging
import os
import os.path

import six
import sqlalchemy
import sqlalchemy.types

from sqlalchemy import String, Integer, Float, Boolean, DateTime, Column, Index, UniqueConstraint, ForeignKey
from sqlalchemy.dialects import postgresql
from sqlalchemy.ext import compiler
from sqlalchemy.ext.declarative import declarative_base, declared_attr
from sqlalchemy.schema import DDLElement
from sqlalchemy.sql import table, text

import sqlalchemy_utils
from sqlalchemy_utils import IntRangeType

from .tools import log, tabulate
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


class CreateFDW (DDLElement):
    def __init__ (self, name, pg_db, mysql_db):
        self.name     = name
        self.pg_db    = pg_db
        self.mysql_db = mysql_db

class DropFDW (DDLElement):
    def __init__ (self, name, pg_db, mysql_db):
        self.name     = name
        self.pg_db    = pg_db
        self.mysql_db = mysql_db

@compiler.compiles(CreateFDW)
def compile (element, compiler, **kw):
    pp = element.pg_db.params
    mp = element.mysql_db.params
    return """
    CREATE SCHEMA {name};
    CREATE SERVER {name}_server FOREIGN DATA WRAPPER mysql_fdw OPTIONS (host '{host}', port '{port}');
    CREATE USER MAPPING FOR {pg_user} SERVER {name}_server OPTIONS (username '{user}', password '{password}');
    IMPORT FOREIGN SCHEMA "{database}" FROM SERVER {name}_server INTO {name};
    """.format (name = element.name, pg_database = pp['database'], pg_user = pp['user'], **mp)

@compiler.compiles(DropFDW)
def compile (element, compiler, **kw):
    pp = element.pg_db.params
    mp = element.mysql_db.params
    return """
    DROP SCHEMA IF EXISTS {name} CASCADE;
    DROP USER MAPPING IF EXISTS FOR {pg_user} SERVER {name}_server;
    DROP SERVER IF EXISTS {name}_server;
    """.format (name = element.name, pg_database = pp['database'], pg_user = pp['user'], **mp)

def fdw (name, metadata, pg_database, mysql_db):
    CreateFDW (name, pg_database, mysql_db).execute_at ('after-create', metadata)
    DropFDW (name, pg_database, mysql_db).execute_at ('before-drop', metadata)



def execute (conn, sql, parameters, debug_level = logging.DEBUG):
    sql = sql.strip ().format (**parameters)
    start_time = datetime.datetime.now ()
    result = conn.execute (text (sql), parameters)
    log (debug_level, "%d rows in %.3fs", result.rowcount, (datetime.datetime.now () - start_time).total_seconds ())
    return result


def executemany (conn, sql, parameters, param_array, debug_level = logging.DEBUG):
    sql = sql.strip ().format (**parameters)
    start_time = datetime.datetime.now ()
    result = conn.execute (text (sql), param_array)
    log (debug_level, "%d rows in %.3fs", result.rowcount, (datetime.datetime.now () - start_time).total_seconds ())
    return result


def executemany_raw (conn, sql, parameters, param_array, debug_level = logging.DEBUG):
    sql = sql.strip ().format (**parameters)
    start_time = datetime.datetime.now ()
    result = conn.execute (sql, param_array)
    log (debug_level, "%d rows in %.3fs", result.rowcount, (datetime.datetime.now () - start_time).total_seconds ())
    return result


def rollback (conn, debug_level = logging.DEBUG):
    start_time = datetime.datetime.now ()
    result = conn.execute ("ROLLBACK")
    log (debug_level, "rollback in %.3fs", (datetime.datetime.now () - start_time).total_seconds ())
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
        if args.log_level >= logging.WARNING:
            log (logging.WARNING, msg + '\n' + tabulate (result))
        if fix_sql:
            execute (conn, fix_sql, parameters)
            # print fixed values
            result = execute (conn, check_sql, parameters)
            if result.rowcount > 0:
                log (logging.ERROR, msg + '\n' + tabulate (result))


class MySQLEngine (object):
    """ Database Interface """

    def __init__ (self, group = None, db = None):
        if group is None:
            group = MYSQL_DEFAULT_GROUP
        if db is None:
            db = ''

        log (logging.INFO, "MySQLEngine: Reading init group: {group}".format (group = group))
        log (logging.INFO, "MySQLEngine: Connecting to db: {db}".format (db = db))

        config = configparser.ConfigParser ()
        config.read (('/etc/my.cnf', os.path.expanduser ('~/.my.cnf')))

        section = config[group]
        self.params = {
            'host' :     section.get ('host', 'localhost').strip ('"'),
            'port' :     section.get ('port', '3306').strip ('"'),
            'user' :     section.get ('user', '').strip ('"'),
            'password' : section.get ('password', '').strip ('"'),
            'database' : db,
        }

        self.engine = sqlalchemy.create_engine (
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

        self.url = "postgresql+psycopg2://{user}:{password}@{host}:{port}/{database}".format (**args)

        if not sqlalchemy_utils.functions.database_exists (self.url):
            log (logging.INFO, "PostgreSQLEngine: Creating database '{database}'".format (**args))
            sqlalchemy_utils.functions.create_database (self.url)

        log (logging.INFO, "PostgreSQLEngine: Connecting to postgres database '{database}' as user '{user}'".format (**args))

        self.engine = sqlalchemy.create_engine (self.url + "?sslmode=disable&server_side_cursors")

        self.params = args


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

        for p in params:
            pu = 'PG' + p.upper ()
            res[p] = args.get (p) or args.get (pu) or os.environ.get (pu) or defaults[p]

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

    id           = Column (Integer,       primary_key = True, autoincrement = True)
    buch         = Column (Integer,       nullable = False)
    kapanf       = Column (Integer,       nullable = False)
    versanf      = Column (Integer,       nullable = False)
    wortanf      = Column (Integer,       nullable = False)
    kapend       = Column (Integer,       nullable = False)
    versend      = Column (Integer,       nullable = False)
    wortend      = Column (Integer,       nullable = False)
    hsnr         = Column (Integer,       nullable = False, index = True)
    hs           = Column (String(32),    nullable = False, index = True)
    anfadr       = Column (Integer,       nullable = False, index = True)
    endadr       = Column (Integer,       nullable = False, index = True)
    labez        = Column (String(32),    nullable = False, server_default = '')
    labezsuf     = Column (String(32),    server_default = '')
    lemma        = Column (String(1024),  server_default = '')
    lesart       = Column (String(1024),  server_default = '')
    labezorig    = Column (String(32),    nullable = False, server_default = '')
    labezsuforig = Column (String(32),    server_default = '')
    suffix2      = Column (String(32),    server_default = '')
    kontrolle    = Column (String(1),     server_default = '')
    fehler       = Column (Integer,       server_default = '0')
    suff         = Column (String(32),    server_default = '')
    vid          = Column (String(32),    server_default = '')
    vl           = Column (String(32),    server_default = '')
    korr         = Column (String(32),    server_default = '')
    lekt         = Column (String(32),    server_default = '')
    komm         = Column (String(32),    server_default = '')
    anfalt       = Column (Integer)
    endalt       = Column (Integer)
    labezalt     = Column (String(32),    server_default = '')
    lasufalt     = Column (String(32),    server_default = '')
    base         = Column (String(1),     server_default = '')
    over         = Column (String(1),     server_default = '')
    comp         = Column (String(1),     server_default = '')
    over1        = Column (String(1),     server_default = '')
    comp1        = Column (String(1),     server_default = '')
    printout     = Column (String(32),    server_default = '')
    category     = Column (String(1),     server_default = '')
    irange       = Column (IntRangeType,  nullable = False)
    created      = Column (DateTime)

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


view ('locstemed_view', Base2.metadata, """
    SELECT p.anfadr, p.endadr, locstemed.*
    FROM locstemed
    JOIN passages p  ON locstemed.pass_id = p.id
    """)

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

# Tables for flask_login / flask_user / flask_security / whatever

Base3 = declarative_base ()

class _User ():
    __tablename__ = 'user'

    id           = Column (Integer,      primary_key = True)
    username     = Column (String (50),  nullable = False, unique = True)
    password     = Column (String (255), nullable = False, server_default = '')
    email        = Column (String (255), nullable = False, unique = True)
    active       = Column (Boolean,      nullable = False, server_default = '0')
    confirmed_at = Column (DateTime)
    first_name   = Column (String (100), nullable = False, server_default = '')
    last_name    = Column (String (100), nullable = False, server_default = '')


class _Role ():
    __tablename__ = 'role'

    id          = Column (Integer,      primary_key = True)
    name        = Column (String  (80), unique = True)
    description = Column (String (255), nullable = False, server_default = '')


class _Roles_Users ():
    __tablename__ = 'roles_users'

    id      = Column (Integer, primary_key = True)

    @declared_attr
    def user_id (cls):
        return Column (Integer, ForeignKey ('user.id', ondelete='CASCADE'))

    @declared_attr
    def role_id (cls):
        return Column (Integer, ForeignKey ('role.id', ondelete='CASCADE'))


class User (_User, Base3):
    pass

class Role (_Role, Base3):
    pass

class Roles_Users (_Roles_Users, Base3):
    pass
