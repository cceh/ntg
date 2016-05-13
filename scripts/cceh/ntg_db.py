# -*- encoding: utf-8 -*-

"""
Database interface

HOW TO CONFIGURE DATABASE ACCESS:

Edit ~/.my.cnf and add sections:

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

!!! Make sure ~/.my.cnf is readable only by you !!!

"""


import MySQLdb


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
  "check"     VARCHAR(1)    NULL
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

BYZ_HSNR = "(300010, 300180, 300350, 303300, 303980, 304240, 312410)"

class DBA (object):
    def __init__ (self, s):
        if s not in ("local", "remote"):
            s = "local"
        self.connection = MySQLdb.connect (read_default_group = "ntg-" + s)

    def cursor (self):
        return self.connection.cursor ()

    def commit (self):
        self.connection.commit ()

    def rollback (self):
        self.connection.rollback ()

    def close (self):
        self.connection.close ()
