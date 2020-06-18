#/bin/bash

DB=$1

psql -d postgres <<EOF
CREATE DATABASE "$DB" OWNER ntg

EOF

psql -d $DB <<EOF
CREATE SCHEMA ntg AUTHORIZATION ntg;
ALTER DATABASE "$DB" SET search_path = ntg, public;

CREATE EXTENSION mysql_fdw;
GRANT USAGE ON FOREIGN DATA WRAPPER mysql_fdw TO ntg;

GRANT CONNECT ON DATABASE "$DB" TO ntg_readonly;
GRANT USAGE ON SCHEMA ntg TO ntg_readonly;
GRANT SELECT ON ALL TABLES IN SCHEMA ntg TO ntg_readonly;

EOF
