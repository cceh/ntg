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
