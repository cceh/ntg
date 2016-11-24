.. -*- encoding: utf-8; bidi-paragraph-direction: left-to-right; fill-column: 72 -*-

Postgres
========

MySQL Foreign Data Wrapper
--------------------------

As database superuser do:

$ psql -U postgres -h /var/run/postgresql/ -d ntg

CREATE EXTENSION mysql_fdw;
# CREATE FOREIGN DATA WRAPPER mysql_fdw;
GRANT USAGE ON FOREIGN DATA WRAPPER mysql_fdw TO ntg;

then as user ntg do:

$ psql

CREATE SERVER mysql_server FOREIGN DATA WRAPPER mysql_fdw OPTIONS (host '127.0.0.1', port '3306');
CREATE USER MAPPING FOR ntg SERVER mysql_server OPTIONS (username 'user', password 'secret');

CREATE SCHEMA mysql;
IMPORT FOREIGN SCHEMA "VarGenAtt_ActPh3_Initial" LIMIT TO (var) FROM SERVER mysql_server INTO mysql;
