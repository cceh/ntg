.. -*- encoding: utf-8; bidi-paragraph-direction: left-to-right; fill-column: 72 -*-

Postgres
========

MySQL Foreign Data Wrapper
--------------------------

Allows Postgres to access Mysql databases in the prepare4cbgm.py script.

As postgres superuser do::

  $ psql -U postgres -h /var/run/postgresql/ -d ntg

  CREATE EXTENSION mysql_fdw;
  # grant rights to user ntg
  GRANT USAGE ON FOREIGN DATA WRAPPER mysql_fdw TO ntg;
