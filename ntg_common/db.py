# -*- encoding: utf-8 -*-

"""Database Interface Module

How To Configure Database Access
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The MySQL database:

Edit (or create) your ~/.my.cnf and add these sections: ::

    [ntg-local]
    host='localhost'
    database='apparat'
    user='username'
    password='password'
    default-character-set='utf8'

    [ntg-remote]
    host='remote'
    database='apparat'
    user='username'
    password='password'
    default-character-set='utf8'

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

from sqlalchemy import String, Integer, Float, Boolean, DateTime, Column, Index, ForeignKey
from sqlalchemy import UniqueConstraint, CheckConstraint, ForeignKeyConstraint, PrimaryKeyConstraint
from sqlalchemy.dialects import postgresql
from sqlalchemy.ext import compiler
from sqlalchemy.ext.declarative import declarative_base, declared_attr
from sqlalchemy.schema import DDLElement
from sqlalchemy.sql import table, text

import sqlalchemy_utils
from sqlalchemy_utils import IntRangeType

from .tools import log, tabulate
from .config import args

MYSQL_DEFAULT_GROUP  = 'ntg-local'


class CoerceInteger (sqlalchemy.types.TypeDecorator):
    """ Coerce numpy integers to python integers
    before passing off to the database."""

    impl = sqlalchemy.types.Integer

    def process_bind_param (self, value, dialect):
        return int (value)

    def process_result_value (self, value, dialect):
        return value

# let sqlalchemy manage our views

class CreateView (DDLElement):
    def __init__ (self, name, sql):
        self.name = name
        self.sql = sql.strip ()

class DropView (DDLElement):
    def __init__ (self, name):
        self.name = name

@compiler.compiles(CreateView)
def compile (element, compiler, **kw):
    return 'CREATE OR REPLACE VIEW %s AS %s' % (element.name, element.sql)

@compiler.compiles(DropView)
def compile (element, compiler, **kw):
    # Use CASCADE to drop dependent views because we drop the views in the same
    # order as we created them instead of correctly using the reverse order.
    return 'DROP VIEW IF EXISTS %s CASCADE' % (element.name)

def view (name, metadata, sql):
    CreateView (name, sql).execute_at ('after-create', metadata)
    DropView (name).execute_at ('before-drop', metadata)


# let sqlalchemy manage our functions

class CreateFunction (DDLElement):
    def __init__ (self, name, params, returns, sql, **kw):
        self.name       = name
        self.params     = params
        self.returns    = returns
        self.sql        = sql.strip ()
        self.language   = kw.get ('language', 'SQL')
        self.volatility = kw.get ('volatility', 'VOLATILE')

class DropFunction (DDLElement):
    def __init__ (self, name, params):
        self.name   = name
        self.params = params

@compiler.compiles(CreateFunction)
def compile (element, compiler, **kw):
    return 'CREATE OR REPLACE FUNCTION {name} ({params}) RETURNS {returns} LANGUAGE {language} {volatility} AS $$ {sql} $$'.format (**element.__dict__)

@compiler.compiles(DropFunction)
def compile (element, compiler, **kw):
    return 'DROP FUNCTION IF EXISTS {name} ({params}) CASCADE'.format (**element.__dict__)

def function (name, metadata, params, returns, sql, **kw):
    CreateFunction (name, params, returns, sql, **kw).execute_at ('after-create', metadata)
    DropFunction (name, params).execute_at ('before-drop', metadata)


# let sqlalchemy manage our foreign data wrappers

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
    return '''
    CREATE SCHEMA {name};
    CREATE SERVER {name}_server FOREIGN DATA WRAPPER mysql_fdw OPTIONS (host '{host}', port '{port}');
    CREATE USER MAPPING FOR {pg_user} SERVER {name}_server OPTIONS (username '{user}', password '{password}');
    IMPORT FOREIGN SCHEMA "{database}" FROM SERVER {name}_server INTO {name};
    '''.format (name = element.name, pg_database = pp['database'], pg_user = pp['user'], **mp)

@compiler.compiles(DropFDW)
def compile (element, compiler, **kw):
    pp = element.pg_db.params
    mp = element.mysql_db.params
    return '''
    DROP SCHEMA IF EXISTS {name} CASCADE;
    DROP USER MAPPING IF EXISTS FOR {pg_user} SERVER {name}_server;
    DROP SERVER IF EXISTS {name}_server;
    '''.format (name = element.name, pg_database = pp['database'], pg_user = pp['user'], **mp)

def fdw (name, metadata, pg_database, mysql_db):
    CreateFDW (name, pg_database, mysql_db).execute_at ('after-create', metadata)
    DropFDW (name, pg_database, mysql_db).execute_at ('before-drop', metadata)


# let sqlalchemy manage generic stuff

class CreateGeneric (DDLElement):
    def __init__ (self, create_cmd):
        self.create = create_cmd

class DropGeneric (DDLElement):
    def __init__ (self, drop_cmd):
        self.drop = drop_cmd

@compiler.compiles(CreateGeneric)
def compile (element, compiler, **kw):
    return element.create

@compiler.compiles(DropGeneric)
def compile (element, compiler, **kw):
    return element.drop

def generic (metadata, create_cmd, drop_cmd):
    CreateGeneric (create_cmd).execute_at ('after-create', metadata)
    DropGeneric (drop_cmd).execute_at ('before-drop', metadata)


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


class MySQLEngine (object):
    """ Database Interface """

    def __init__ (self, group = None, db = None):
        if group is None:
            group = MYSQL_DEFAULT_GROUP
        if db is None:
            db = ''

        log (logging.INFO, 'MySQLEngine: Reading init group: {group}'.format (group = group))
        log (logging.INFO, 'MySQLEngine: Connecting to db: {db}'.format (db = db))

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
            'mysql:///{db}?read_default_group={group}'.format (db = db, group = group))

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

        self.url = 'postgresql+psycopg2://{user}:{password}@{host}:{port}/{database}'.format (**args)

        if not sqlalchemy_utils.functions.database_exists (self.url):
            log (logging.INFO, "PostgreSQLEngine: Creating database '{database}'".format (**args))
            sqlalchemy_utils.functions.create_database (self.url)

        log (logging.INFO, "PostgreSQLEngine: Connecting to postgres database '{database}' as user '{user}'".format (**args))

        self.engine = sqlalchemy.create_engine (self.url + '?sslmode=disable&server_side_cursors')

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
        pgpass = os.path.expanduser ('~/.pgpass')
        try:
            with open (pgpass, 'r') as f:
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
            print ('Error: could not open %s for reading' % pgpass)

        return res


Base = declarative_base ()

class Att (Base):
    __tablename__ = 'att'

    id           = Column (Integer,       primary_key = True, autoincrement = True)
    hsnr         = Column (Integer,       nullable = False, index = True)
    hs           = Column (String(32),    nullable = False, index = True)
    anfadr       = Column (Integer,       nullable = False, index = True)
    endadr       = Column (Integer,       nullable = False, index = True)
    labez        = Column (String(32),    nullable = False, server_default = '')
    labezsuf     = Column (String(32),    server_default = '')
    certainty    = Column (Float(16),     nullable = False, server_default = '1.0')
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
    deleted      = Column (Boolean, nullable = False, server_default = 'false')

    __table_args__ = (
        Index ('unique_att_hs_irange', hs, irange, unique = True, postgresql_where = certainty == 1.0),
    )


class Lac (Base): # same as class Att
    __tablename__ = 'lac'

    id        = Column (Integer,       primary_key = True, autoincrement = True)
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
    deleted   = Column (Boolean, nullable = False, server_default = 'false')

    __table_args__ = (
        Index ('lac_irange_gist_idx', 'irange', postgresql_using = 'gist'),
        UniqueConstraint ('hs', 'irange', name = 'unique_lac_hs_irange')
    )


class SaveReadings (Base): # same as class Att
    __tablename__ = 'save_readings'

    id        = Column (Integer,       primary_key = True, autoincrement = True)

    anfadr    = Column (Integer,       nullable = False)
    endadr    = Column (Integer,       nullable = False)
    labez     = Column (String(32),    nullable = False, server_default = '')
    lemma     = Column (String(1024),  server_default = '')
    lesart    = Column (String(1024),  server_default = '')


function ('char_labez', Base.metadata, 'l INTEGER', 'CHAR (3)', '''
    SELECT CASE WHEN l > 0 THEN chr (l + 96) ELSE 'z' END
    ''', volatility = 'IMMUTABLE')

function ('ord_labez', Base.metadata, 'l CHAR (2)', 'INTEGER', '''
    SELECT CASE WHEN ascii (l) >= 122 THEN 0 ELSE ascii (l) - 96 END
    ''', volatility = 'IMMUTABLE')

function ('adr2bk_id', Base.metadata, 'adr INTEGER', 'INTEGER', '''
    SELECT (adr / 10000000) %% 10
    ''', volatility = 'IMMUTABLE')

function ('adr2chapter', Base.metadata, 'adr INTEGER', 'INTEGER', '''
    SELECT ((adr / 100000) %% 100)
    ''', volatility = 'IMMUTABLE')

function ('adr2verse', Base.metadata, 'adr INTEGER', 'INTEGER', '''
    SELECT ((adr / 1000) %% 100)
    ''', volatility = 'IMMUTABLE')

function ('adr2word', Base.metadata, 'adr INTEGER', 'INTEGER', '''
    SELECT (adr %% 1000)
    ''', volatility = 'IMMUTABLE')


Base2 = declarative_base ()

class Manuscripts (Base2):
    """A table that lists all the manuscripts.

    This table lists all the manuscripts of New Testament that we have collated
    for the edition.

    .. attribute:: ms_id

        The primary key of the table.

    .. attribute:: hsnr

        The project-internal number of the manuscript.

        This is a six-digit number. The first digit encodes the type of the
        manuscript: 1 = papyrus, 2 = uncial, 3 = minuscule, 4 = lectionary, 5 =
        patristic citations and versions.  The next 4 digits are taken from the
        digits of the Gregory-Aland number, eg. P45 would yield 0045.  The last
        digit encodes supplements: 0 = original, 1 = first supplement, 2 =
        second supplement.

        N.B. Patristic citations and versions are not used in the CBGM, and thus
        purged from the database.

    .. attribute:: hs

        The Gregory-Aland number of the manuscript. eg. 'P45', '03', or '1739'.

    """

    __tablename__ = 'manuscripts'

    ms_id     = Column (Integer,       primary_key = True, autoincrement = True)
    hsnr      = Column (Integer,       nullable = False, unique = True)
    hs        = Column (String (32),   nullable = False, unique = True)


class Books (Base2):
    """A table that lists all the books of the New Testament.

    This table lists all the books of the NT and the book id given to them.

    .. attribute:: bk_id

        The book id: 1 - 27 (Matthew - Revelation).

    .. attribute:: siglum

        The book siglum, eg. 'Mt'

    .. attribute:: book

        The book name, eg. 'Matthew'

    .. attribute:: irange

        The book extent in passages.

    """

    __tablename__ = 'books'

    bk_id     = Column (Integer,       primary_key = True, autoincrement = True)

    siglum    = Column (String,        nullable = False)
    book      = Column (String,        nullable = False)
    irange    = Column (IntRangeType,  nullable = False)

    __table_args__ = (
        UniqueConstraint ('siglum'),
        UniqueConstraint ('book'),
        Index ('books_irange_gist_idx', 'irange', postgresql_using = 'gist'),
    )


class Passages (Base2):
    """A table that lists the variant passages.

    This table lists all the passages we established during the collation of the
    manuscripts.  Passages that are the same in all manuscripts (invariant) are
    purged because they are irrelevant to the CBGM.

    .. attribute:: irange

        The extent of the passage.

        The beginning and end of every passage is encoded in this way:

          book id * 10,000,000 +
          chapter *    100,000 +
          verse   *      1,000 +
          word    *          2

        Words are always even and the space between to words is always odd.

    .. attribute:: lemma

        The lemma of the passage.  Usually the reconstructed original text.

    .. attribute:: spanning

        True if this passage is spanning other passages.

    .. attribute:: spanned

        True if this passage is spanned by other passages.

    .. attribute:: fehlvers

        True if this passage is a later addition, eg. the pericope adulterae.

    """

    __tablename__ = 'passages'

    pass_id   = Column (Integer,       primary_key = True, autoincrement = True)

    bk_id     = Column (Integer,       nullable = False)

    anfadr    = Column (Integer,       nullable = False)
    endadr    = Column (Integer,       nullable = False)

    irange    = Column (IntRangeType,  nullable = False)
    lemma     = Column (String (1024), nullable = False, server_default = '')
    spanning  = Column (Boolean,       nullable = False, server_default = 'False')
    spanned   = Column (Boolean,       nullable = False, server_default = 'False')
    fehlvers  = Column (Boolean,       nullable = False, server_default = 'False')

    __table_args__ = (
        UniqueConstraint ('irange', name = 'unique_passages_irange'), # needs name
        ForeignKeyConstraint (['bk_id'], ['books.bk_id']),
        Index ('passages_irange_gist_idx', 'irange', postgresql_using = 'gist'),
    )


class Readings (Base2):
    """A table that contains the different readings found at each passage.

    First scribal errors are corrected and orthographical differences are
    normalized, then equal readings are grouped.  Each group of readings is
    assigned an id, the 'labez'.

    .. attribute:: labez

        (LesArtBEZeichnung).  Usually 'a' indicates the original reading, while
        'b'...'y' indicate readings relegated to the apparatus, although this is
        not necessarily so.  Exceptions are the 'Fehlverse' and the cases where
        no original reading could be assessed.

        Readings starting with 'z' have special meaning:

        .. data:: zu

            Hier nicht zitierbar aufgrund einer übergreifenden Variante.  Diese
            umfaßte Variante wurde schon in der umfassenden Variante
            verzeichnet.  Entspricht in der ECM einem Pfeil nach oben.  In der
            CBGM ist 'zu' wie 'zz' zu behandeln.

        .. data:: zv

            There is an illegible addition in the manuscript(s) cited which
            makes it impossible to ascribe it to a known variant.

        .. data:: zw

            What remains of the text of the manuscript(s) cited would allow
            reconstruction in agreement with two or more different variants.
            Entspricht in der ECM einem Doppelpfeil nach links-rechts.

            labezsuf contains a '/'-separated list of the possible readings.

            N.B. not used any more, instead the readings will get a certainty <
            1.0.

        .. data:: zz

            The reading is too lacunose to be identified.

            Alle Verzeichnungen, die aus der Tabelle der Lacunae erzeugt wurden,
            erhalten labez = 'zz'.

            Ein Wort steht nicht in der systematischen Lückenliste wenn
            mindestens ein Buchstabe vorhanden ist.  In diesem Fall steht es in
            der stellenbezogenen Lückenliste.

        Caveat: die Lesart 'a' kann für dieselbe Passage mehrmals vergeben
        worden sein, immer dann wenn im Nestle-Aland ein positiver Apparat
        benutzt wurde.

    .. attribute:: lesart

        The normalized reading.  Scribal errors are silently corrected and
        orthographic variants are normalized.

    """

    __tablename__ = 'readings'

    pass_id   = Column (Integer,       nullable = False)
    labez     = Column (String (2),    nullable = False)

    lesart    = Column (String (1024), nullable = False)

    __table_args__ = (
        PrimaryKeyConstraint ('pass_id', 'labez'),
        ForeignKeyConstraint (['pass_id'], ['passages.pass_id']),
    )


class Cliques (Base2):
    """A table that contains the cliques at every passage

    A clique is a set of strongly related manuscripts that offer the same
    reading.  A reading may have been originated more than once, while a clique
    has been originated only once.

    .. attribute:: clique

        Name of the Clique. '0', '1', '2' ...

    """

    __tablename__ = 'cliques'

    pass_id   = Column (Integer,    nullable = False)
    labez     = Column (String (2), nullable = False)
    clique    = Column (String (2), nullable = False)

    __table_args__ = (
        PrimaryKeyConstraint ('pass_id', 'labez', 'clique'),
        ForeignKeyConstraint (['pass_id', 'labez'], ['readings.pass_id', 'readings.labez']),
    )


class Apparatus (Base2):
    """A table that contains the positive apparatus.

    .. attribute:: cbgm

        True if this entry is eligible for CBGM, eg. is by the orginal scribe
        and is 100% certain.  There can be only one entry eligible for CBGM for
        every manuscript and passage.

    .. attribute:: labezsuf

        Contains auxiliary information about the reading:

        .. data:: f

            Fehler.  The reading is considered a scribal error.

        .. data:: o

           Orthographicum.  The reading is considered an orthographical variant,
           eg. a variant place name.

        If the labez is 'zw' labezsuf contains a "/"-separated list of possible
        readings, eg. "a/b_o/c_f".

    .. attribute:: certainty

        Certainty of the reading. There can be only one reading of certainty 1.0,
        but multiple readings of certainty < 1.0.

    .. attribute:: lesart

        The actual reading offered by the manuscript if different from the
        normalized reading in readings.lesart.  Readings are NULL if they
        correspond exactly to the reading in the readings table.  For 'f' and
        'o' readings (errors and orthographic variants) the actual reading is
        inserted.

    .. attribute:: origin

        Where does this apparatus entry come from? For debugging purposes.

    """

    __tablename__ = 'apparatus'

    pass_id   = Column (Integer,       nullable = False)
    labez     = Column (String (2),    nullable = False)
    clique    = Column (String (2),    nullable = False, server_default = '0')
    ms_id     = Column (Integer,       nullable = False)

    cbgm      = Column (Boolean,       nullable = False)
    labezsuf  = Column (String (32),   nullable = False, server_default = '')
    certainty = Column (Float (16),    nullable = False, server_default = '1.0')
    lesart    = Column (String (1024), nullable = True,  server_default = None)
    origin    = Column (String (3),    nullable = False)

    __table_args__ = (
        PrimaryKeyConstraint ('pass_id', 'ms_id', 'labez'),
        Index ('apparatus_ms_id', 'ms_id'),
        Index ('apparatus_unique_cbgm', 'pass_id', 'ms_id', unique = True, postgresql_where = cbgm == True),
        ForeignKeyConstraint (['pass_id', 'labez', 'clique'], ['cliques.pass_id', 'cliques.labez', 'cliques.clique']),
        ForeignKeyConstraint (['ms_id'],                      ['manuscripts.ms_id']),
        CheckConstraint ('certainty > 0.0 AND certainty <= 1.0'),
        CheckConstraint ('(certainty = 1.0) >= cbgm'),  # cbgm implies 100% certainty
    )


class LocStem (Base2):
    """A table that contains the priority of the cliques at each passage

    This table contains the main output of the editors.  The editors decide
    which reading is derived from which other reading(s) at each passage.

    .. attribute:: labez, clique

        The younger reading which was derived from the older reading.

    .. attribute:: source_labez, source_clique

        The older reading that was the source of the younger reading or NULL if
        no source reading could be established.

    .. attribute:: original

        This reading was established as the original.  Must also have a
        source_labez of NULL.

    """
    __tablename__ = 'locstem'

    pass_id       = Column (Integer,    nullable = False)
    labez         = Column (String (2), nullable = False)
    clique        = Column (String (2), nullable = False)

    source_labez  = Column (String (2), nullable = True)
    source_clique = Column (String (2), nullable = True)

    original      = Column (Boolean,    nullable = False, server_default = 'false')

    __table_args__ = (
        PrimaryKeyConstraint ('pass_id', 'labez', 'clique'),
        Index ('unique_locstem_original', 'pass_id', unique = True, postgresql_where = original == True),
        ForeignKeyConstraint (['pass_id', 'labez', 'clique'], ['cliques.pass_id', 'cliques.labez', 'cliques.clique']),
        ForeignKeyConstraint (['pass_id', 'source_labez', 'source_clique'], ['cliques.pass_id', 'cliques.labez', 'cliques.clique']),
        CheckConstraint ('original <= (source_labez is null)'), # original implies source is null
    )


class Ranges (Base2):
    """A table that contains the ranges of passages for the CBGM.

    The CBGM is agnostic about the division in books and chapters of the NT.  It
    can be run on any range of passages (in theory even on sets of non-contiguous
    passages, although not yet in this implementation).

    This table contains all ranges we are interested in, that is, one range for
    each chapter of each book and also one range for each whole book.  The
    chapter ranges are named after the chapter mumber, the whole book range is
    called 'All'.

    .. attribute:: range

        The name of the range, eg. '1' for Chapter 1.

    .. attribute:: irange

        The extent of the range.

    """

    __tablename__ = 'ranges'

    rg_id     = Column (Integer,          primary_key = True, autoincrement = True)

    bk_id     = Column (Integer,          nullable = False)

    range_    = Column ('range', String,  nullable = False)

    irange    = Column (IntRangeType,     nullable = False)

    __table_args__ = (
        ForeignKeyConstraint (['bk_id'], ['books.bk_id']),
        UniqueConstraint ('bk_id', 'range'),
        Index ('ranges_irange_gist_idx', 'irange', postgresql_using = 'gist'),
    )


class Ms_Ranges (Base2):
    """A table that contains CBGM output related to each manuscript.

    Here we hold values that are calculated by CBGM related to one manuscript.

    .. attribute:: length

        Calculated: no. of defined passages in the manuscript inside this range.

    """

    __tablename__ = 'ms_ranges'

    rg_id      = Column (Integer,       ForeignKey ('ranges.rg_id'),      nullable = False)
    ms_id      = Column (Integer,       ForeignKey ('manuscripts.ms_id'), nullable = False)

    length     = Column (Integer)

    __table_args__ = (
        PrimaryKeyConstraint ('rg_id', 'ms_id'),
    )


class Affinity (Base2):
    """A table that contains CBGM output related to each pair of manuscripts.

    This table contains the actual results of applying the CBGM.  It has one row
    for each pair of manuscripts that have at least one passage in common and
    each range we are interested in.

    Two sets of data are included, one for the recursive interpretation of the
    locstem data, and one for the backward-compatible non-recurisve
    interpretation (with 'p\_' prefix).

    .. attribute:: common

        No. of passages defined in both manuscripts.

    .. attribute:: equal

        No. of passages that have the same reading in both manuscripts.

    .. attribute:: affinity

        equal / common

    .. attribute:: older

        No. of passages that have an older reading in ms1.

    .. attribute:: newer

        No. of passages that have an newer reading in ms1.

    .. attribute:: unclear

        No. of passages where it is unclear which reading is older.

    """

    __tablename__ = 'affinity'

    rg_id      = Column (Integer,       ForeignKey ('ranges.rg_id'),      nullable = False)
    ms_id1     = Column (Integer,       ForeignKey ('manuscripts.ms_id'), nullable = False)
    ms_id2     = Column (Integer,       ForeignKey ('manuscripts.ms_id'), nullable = False)

    affinity   = Column (Float,         nullable = False, server_default = '0')

    common     = Column (Integer,       nullable = False)
    equal      = Column (Integer,       nullable = False)

    older      = Column (Integer,       nullable = False)
    newer      = Column (Integer,       nullable = False)
    unclear    = Column (Integer,       nullable = False)

    p_older    = Column (Integer,       nullable = False)
    p_newer    = Column (Integer,       nullable = False)
    p_unclear  = Column (Integer,       nullable = False)

    __table_args__ = (
        PrimaryKeyConstraint ('rg_id', 'ms_id1', 'ms_id2'),
    )


function ('labez_array_to_string', Base2.metadata, 'a CHAR[]', 'CHAR', '''
SELECT array_to_string (a, '/', '')
''', volatility = 'IMMUTABLE')

function ('varnew2labez', Base2.metadata, 'varnew CHAR (2)', 'CHAR', '''
SELECT REGEXP_REPLACE (varnew, '[0-9]+$', '')
''', volatility = 'IMMUTABLE')

function ('varnew2clique', Base2.metadata, 'varnew CHAR (2)', 'CHAR', '''
SELECT COALESCE (NULLIF (REGEXP_REPLACE (varnew, '^[^0-9]+', ''), ''), '0')
''', volatility = 'IMMUTABLE')

function ('source2labez', Base2.metadata, 'source CHAR (2)', 'CHAR', '''
SELECT CASE WHEN source IN ('*', '?', '') THEN NULL ELSE varnew2labez (source) END
''', volatility = 'IMMUTABLE')

function ('source2clique', Base2.metadata, 'source CHAR (2)', 'CHAR', '''
SELECT CASE WHEN source IN ('*', '?', '') THEN NULL ELSE varnew2clique (source) END
''', volatility = 'IMMUTABLE')

function ('source2original', Base2.metadata, 'source CHAR (2)', 'BOOLEAN', '''
SELECT CASE WHEN source = '*' THEN true ELSE false END
''', volatility = 'IMMUTABLE')

function ('labez_clique', Base2.metadata, 'labez CHAR, clique CHAR', 'CHAR', '''
SELECT labez || COALESCE (clique, '0')
''', volatility = 'IMMUTABLE')

generic (Base2.metadata, '''
CREATE AGGREGATE labez_agg (CHAR) (
  sfunc = array_append,
  stype = char[],
  initcond = '{}',
  finalfunc = labez_array_to_string
)
''', '''
DROP AGGREGATE IF EXISTS labez_agg (CHAR) CASCADE
'''
)

view ('ranges_view', Base2.metadata, '''
    SELECT bk.bk_id, bk.siglum, bk.book, ch.rg_id, ch.range, ch.irange
    FROM books bk
    JOIN ranges ch USING (bk_id)
    ''')

view ('ms_ranges_view', Base2.metadata, '''
    SELECT ch.*, mc.ms_id, mc.length
    FROM ms_ranges mc
    JOIN ranges_view ch USING (rg_id)
    ''')

view ('passages_view', Base2.metadata, '''
    SELECT b.bk_id, b.siglum, b.book,
           adr2chapter (p.anfadr) AS chapter,
           adr2verse   (p.anfadr) AS verse,
           adr2word    (p.anfadr) AS word,
           p.anfadr, p.endadr, p.irange, p.lemma
    FROM passages p
    JOIN books b USING (bk_id)
    ''')

view ('locstem_view', Base2.metadata, '''
    SELECT p.anfadr, p.endadr, locstem.*
    FROM locstem
    JOIN passages p USING (pass_id)
    ''')

view ('readings_view', Base2.metadata, '''
    SELECT p.anfadr, p.endadr, p.irange, p.lemma, r.*
    FROM readings r
    JOIN passages p USING (pass_id)
    ''')

view ('cliques_view', Base2.metadata, '''
    SELECT r.anfadr, r.endadr, r.irange, r.lemma, r.lesart, q.*
    FROM cliques q
    JOIN readings_view r USING (pass_id, labez)
    ''')

view ('apparatus_view', Base2.metadata, '''
    SELECT p.pass_id, p.anfadr, p.endadr, p.irange, p.spanning, p.spanned, p.fehlvers,
           ms.ms_id, ms.hs, ms.hsnr,
           a.labez, a.clique, labez_clique (a.labez, a.clique) AS labez_clique,
           a.cbgm, a.labezsuf, a.certainty, a.origin,
           COALESCE (a.lesart, r.lesart) AS lesart
    FROM apparatus a
    JOIN readings r     USING (pass_id, labez)
    JOIN passages p     USING (pass_id)
    JOIN manuscripts ms USING (ms_id)
    ''')

view ('apparatus_view_agg', Base2.metadata, '''
   SELECT pass_id, ms_id, labez_agg (labez ORDER BY labez) as labez
   FROM apparatus
   GROUP BY pass_id, ms_id
   ''')

view ('affinity_view', Base2.metadata, '''
    SELECT ch.bk_id, ch.rg_id, ms_id1, ms_id2, common, equal,
           older, newer, unclear,
           affinity,
           ch1.length AS ms1_length,
           ch2.length AS ms2_length
    FROM affinity aff
    JOIN ranges_view ch USING (rg_id)
    JOIN ms_ranges ch1 ON (aff.ms_id1, aff.rg_id) = (ch1.ms_id, ch1.rg_id)
    JOIN ms_ranges ch2 ON (aff.ms_id2, aff.rg_id) = (ch2.ms_id, ch2.rg_id)
    ''')

view ('affinity_p_view', Base2.metadata, '''
    SELECT ch.bk_id, ch.rg_id, ms_id1, ms_id2, common, equal,
           p_older as older, p_newer as newer, p_unclear as unclear,
           affinity,
           ch1.length AS ms1_length,
           ch2.length AS ms2_length
    FROM affinity aff
    JOIN ranges_view ch USING (rg_id)
    JOIN ms_ranges ch1 ON (aff.ms_id1, aff.rg_id) = (ch1.ms_id, ch1.rg_id)
    JOIN ms_ranges ch2 ON (aff.ms_id2, aff.rg_id) = (ch2.ms_id, ch2.rg_id)
    ''')


generic (Base2.metadata, '''
CREATE UNIQUE INDEX IF NOT EXISTS readings_unique_pass_id_lesart ON readings (pass_id, lesart) WHERE labez !~ '^z'
''', '''
DROP INDEX IF EXISTS readings_unique_pass_id_lesart
'''
)


LOCSTEM_REC = '''
WITH RECURSIVE locstem_rec (pass_id, labez, clique, source_labez, source_clique, original) AS (
  SELECT pass_id, labez, clique, source_labez, source_clique, original
  FROM locstem i
  WHERE i.pass_id = passage_id AND i.labez = labez1 AND i.clique = clique1
  UNION
  SELECT l.pass_id, l.labez, l.clique, l.source_labez, l.source_clique, l.original
  FROM locstem l, locstem_rec r
  WHERE l.pass_id = r.pass_id AND l.labez = r.source_labez AND l.clique = r.source_clique
  )
'''

function ('is_older', Base2.metadata, 'passage_id INTEGER, labez2 CHAR, clique2 CHAR, labez1 CHAR, clique1 CHAR', 'BOOLEAN', LOCSTEM_REC + '''
SELECT EXISTS (SELECT * FROM locstem_rec WHERE source_labez = labez2 AND source_clique = clique2);
''', volatility = 'STABLE')

function ('is_unclear', Base2.metadata, 'passage_id INTEGER, labez1 CHAR, clique1 CHAR', 'BOOLEAN', LOCSTEM_REC + '''
SELECT EXISTS (SELECT * FROM locstem_rec WHERE source_labez IS NULL AND original = false);
''', volatility = 'STABLE')


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
