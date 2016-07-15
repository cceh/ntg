# -*- encoding: utf-8 -*-

"""Database Interface Module

How To Configure Database Access
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Edit your ~/.my.cnf and add these sections: ::

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

"""

import sqlalchemy
from sqlalchemy import create_engine, MetaData, Table
from sqlalchemy.sql import text

from .tools import message, tabulate
from .config import args

MYSQL_DEFAULT_GROUP  = "ntg-local"


def execute (conn, sql, parameters, debug_level = 3):
    sql = sql.format (**parameters)
    message (debug_level, sql.rstrip () + ';')
    result = conn.execute (text (sql), parameters)
    message (debug_level, "%d rows" % result.rowcount)
    return result


def executemany (conn, sql, parameters, param_array, debug_level = 3):
    sql = sql.format (**parameters)
    message (debug_level, sql.rstrip () + ';')
    result = conn.execute (text (sql), param_array)
    message (debug_level, "%d rows" % result.rowcount)
    return result


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


CREATE_TABLE_ATT = """
(
  "id"          INTEGER       AUTO_INCREMENT PRIMARY KEY,
  "buch"        INTEGER       DEFAULT NULL,
  "kapanf"      INTEGER       DEFAULT NULL,
  "versanf"     INTEGER       DEFAULT NULL,
  "wortanf"     INTEGER       DEFAULT NULL,
  "kapend"      INTEGER       DEFAULT 0,
  "versend"     INTEGER       DEFAULT 0,
  "wortend"     INTEGER       DEFAULT NULL,
  "hsnr"        INTEGER       DEFAULT NULL,
  "hs"          VARCHAR(32)   DEFAULT NULL,
  "anfadr"      INTEGER       DEFAULT NULL,
  "endadr"      INTEGER       DEFAULT NULL,
  "labez"       VARCHAR(32)   DEFAULT '',
  "labezsuf"    VARCHAR(32)   DEFAULT '',
  "lemma"       VARCHAR(1024) DEFAULT '',
  "lesart"      VARCHAR(1024) DEFAULT '',
  "suffix2"     VARCHAR(255)  DEFAULT '',
  "kontrolle"   VARCHAR(1)    DEFAULT '',
  "fehler"      INTEGER       DEFAULT 0,
  "suff"        VARCHAR(32)   DEFAULT '',
  "vid"         VARCHAR(32)   DEFAULT '',
  "vl"          VARCHAR(32)   DEFAULT '',
  "korr"        VARCHAR(32)   DEFAULT '',
  "lekt"        VARCHAR(32)   DEFAULT '',
  "komm"        VARCHAR(32)   DEFAULT '',
  "anfalt"      INTEGER       DEFAULT NULL,
  "endalt"      INTEGER       DEFAULT NULL,
  "labezalt"    VARCHAR(32)   DEFAULT '',
  "lasufalt"    VARCHAR(32)   DEFAULT '',
  "base"        VARCHAR(1)    DEFAULT '',
  "over"        VARCHAR(1)    DEFAULT '',
  "comp"        VARCHAR(1)    DEFAULT '',
  "over1"       VARCHAR(1)    DEFAULT '',
  "comp1"       VARCHAR(1)    DEFAULT '',
  "printout"    VARCHAR(32)   DEFAULT '',
  "category"    VARCHAR(1)    DEFAULT '',
  "created"     DATE          DEFAULT NULL
)
"""

CREATE_TABLE_LAC = """
(
  "id"        INTEGER       AUTO_INCREMENT PRIMARY KEY,
  "buch"      INTEGER       NOT NULL,
  "kapanf"    INTEGER       NOT NULL,
  "versanf"   INTEGER       NOT NULL,
  "wortanf"   INTEGER       NOT NULL,
  "wortend"   INTEGER       DEFAULT NULL,
  "hsnr"      INTEGER       DEFAULT NULL,
  "hs"        VARCHAR(32)   DEFAULT NULL,
  "anfadr"    INTEGER       DEFAULT NULL,
  "endadr"    INTEGER       DEFAULT NULL,
  "labez"     VARCHAR(32)   NOT NULL,
  "labezsuf"  VARCHAR(32)   DEFAULT NULL,
  "lemma"     VARCHAR(1024) NOT NULL,
  "lesart"    VARCHAR(1024) DEFAULT NULL,
  "suffix2"   VARCHAR(32)   DEFAULT NULL,
  "kontrolle" VARCHAR(1)    DEFAULT NULL,
  "kapend"    INTEGER       DEFAULT 0,
  "versend"   INTEGER       DEFAULT 0,
  "fehler"    INTEGER       DEFAULT 0,
  "suff"      VARCHAR(32)   DEFAULT NULL,
  "vid"       VARCHAR(32)   DEFAULT NULL,
  "vl"        VARCHAR(32)   DEFAULT NULL,
  "korr"      VARCHAR(32)   DEFAULT NULL,
  "lekt"      VARCHAR(32)   DEFAULT NULL,
  "komm"      VARCHAR(32)   DEFAULT NULL,
  "anfalt"    INTEGER       DEFAULT NULL,
  "endalt"    INTEGER       DEFAULT NULL,
  "labezalt"  VARCHAR(32)   DEFAULT NULL,
  "lasufalt"  VARCHAR(32)   DEFAULT NULL,
  "printout"  VARCHAR(32)   DEFAULT NULL,
  "category"  VARCHAR(1)    DEFAULT NULL,
  "base"      VARCHAR(1)    DEFAULT '',
  "over"      VARCHAR(1)    DEFAULT '',
  "comp"      VARCHAR(1)    DEFAULT '',
  "over1"     VARCHAR(1)    DEFAULT '',
  "comp1"     VARCHAR(1)    DEFAULT '',
  "created"   DATE          DEFAULT NULL
)
"""

CREATE_TABLE_LABEZ = """
(
  "id"        INTEGER       AUTO_INCREMENT PRIMARY KEY,
  "ms_id"     INTEGER       NOT NULL,
  "pass_id"   INTEGER       NOT NULL,
  "labez"     INTEGER       NOT NULL DEFAULT 0,
  "labezsuf"  VARCHAR(32)   DEFAULT NULL,
  UNIQUE KEY (ms_id, pass_id, labez, labezsuf)
)
"""

CREATE_TABLE_VP = """
(
  "id"        INTEGER       AUTO_INCREMENT PRIMARY KEY,
  "anfadr"    INTEGER       NOT NULL,
  "endadr"    INTEGER       NOT NULL,
  "bzdef"     INTEGER       NOT NULL DEFAULT 0,
  "check"     VARCHAR(1)    NULL
)
"""

CREATE_TABLE_RDG = """
(
  "id"        INTEGER       AUTO_INCREMENT PRIMARY KEY,
  "anfadr"    INTEGER       NOT NULL,
  "endadr"    INTEGER       NOT NULL,
  "labez"     VARCHAR(32)   NOT NULL,
  "labezsuf"  VARCHAR(32)   NOT NULL,
  "lesart"    VARCHAR(1024) NOT NULL,
  "bz"        INTEGER       NOT NULL DEFAULT 0,
  "bzdef"     INTEGER       NOT NULL DEFAULT 0,
  "byz"       VARCHAR(1)    NOT NULL DEFAULT '',
  "check"     VARCHAR(1)    NULL,
  UNIQUE KEY (anfadr, endadr, labez)
)
"""

CREATE_TABLE_WITN = """
(
  "id"        INTEGER       AUTO_INCREMENT PRIMARY KEY,
  "anfadr"    INTEGER       NOT NULL,
  "endadr"    INTEGER       NOT NULL,
  "labez"     VARCHAR(32)   NOT NULL,
  "labezsuf"  VARCHAR(32)   NOT NULL,
  "hsnr"      INTEGER       NOT NULL,
  "hs"        VARCHAR(32)   NOT NULL
)
"""

CREATE_TABLE_MSLISTVAL = """
(
  "id"        INTEGER       AUTO_INCREMENT PRIMARY KEY,
  "hsnr"      INTEGER       NOT NULL,
  "hs"        VARCHAR(32)   NOT NULL,
  "chapter"   INTEGER       NOT NULL,
  "sumtxt"    INTEGER       NOT NULL DEFAULT 0,
  "summt"     INTEGER       NOT NULL DEFAULT 0,
  "uemt"      INTEGER       NOT NULL DEFAULT 0,
  "qmt"       FLOAT         NOT NULL DEFAULT 0.0,
  "check"     VARCHAR(1)    NULL
)
"""

CREATE_TABLE_VG = """
(
  "id"        INTEGER       AUTO_INCREMENT PRIMARY KEY,
  "hsnr"      INTEGER       NOT NULL,
  "hsnr2"     INTEGER       NOT NULL,
  "chapter"   INTEGER       NOT NULL,
  "sumtxt"    INTEGER       NOT NULL DEFAULT 0,
  "summt"     INTEGER       NOT NULL DEFAULT 0,
  "uemt"      INTEGER       NOT NULL DEFAULT 0,
  "qmt"       FLOAT         NOT NULL DEFAULT 0.0,
  "check"     VARCHAR(1)    NULL
)
"""

CREATE_TABLE_MANUSCRIPTS = """
(
  "id"        INTEGER       AUTO_INCREMENT PRIMARY KEY,
  "hsnr"      INTEGER       NOT NULL,
  "hs"        VARCHAR(32)   NOT NULL,
  "length"    INTEGER       ,
  UNIQUE KEY (hsnr),
  UNIQUE KEY (hs)
)
"""

CREATE_TABLE_AFFINITY = """
(
  "chapter"   INTEGER       NOT NULL,
  "id1"       INTEGER       NOT NULL,
  "id2"       INTEGER       NOT NULL,
  "common"    INTEGER       NOT NULL,
  "equal"     INTEGER       NOT NULL,
  "older"     INTEGER       NOT NULL,
  "affinity"  FLOAT         NOT NULL,
  PRIMARY KEY (chapter, id1, id2)
)
"""

CREATE_TABLE_GEPHI_NODES = """
(
  "id"        VARCHAR(32)   NOT NULL,
  "label"     VARCHAR(32)   ,
  "color"     VARCHAR(32)   ,
  "nodecolor" VARCHAR(32)   ,
  "nodesize"  FLOAT         ,
  "x"         FLOAT         ,
  "y"         FLOAT         ,
  "size"      FLOAT         ,
  PRIMARY KEY (id)
)
"""

CREATE_TABLE_GEPHI_EDGES = """
(
  "id"        VARCHAR(65)   NOT NULL,
  "label"     VARCHAR(32)   ,
  "source"    VARCHAR(32)   NOT NULL,
  "target"    VARCHAR(32)   NOT NULL,
  "weight"    FLOAT         NOT NULL DEFAULT 1.0,
  PRIMARY KEY (source, target)
)
"""

CREATE_TABLE_LOCSTEMED = """
(
  "id"     INTEGER      NOT NULL AUTO_INCREMENT,
  "begadr" INTEGER      NOT NULL,
  "endadr" INTEGER      NOT NULL,
  "varid"  VARCHAR(2)   NOT NULL,
  "varnew" VARCHAR(2)   NOT NULL DEFAULT '',
  "s1"     VARCHAR(2)   NOT NULL DEFAULT '',
  "s2"     VARCHAR(2)   NOT NULL DEFAULT '',
  "pred"   VARCHAR(256) NOT NULL DEFAULT '',
  "prs1"   VARCHAR(2)   NOT NULL DEFAULT '',
  "prs2"   VARCHAR(2)   NOT NULL DEFAULT '',
  "check"  VARCHAR(2)   NOT NULL DEFAULT '',
  "check2" VARCHAR(2)   NOT NULL DEFAULT '',
  "w"      varchar(1)   NOT NULL DEFAULT '',
  PRIMARY KEY (id)
)
"""


BYZ_HSNR = "(300010, 300180, 300350, 303300, 303980, 304240, 312410)"
"""Manuscripts that contain the Byzantine Text.

We use these manuscripts to establish the Byzantine Text according to our rules.

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
