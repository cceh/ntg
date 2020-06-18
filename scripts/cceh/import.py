# -*- encoding: utf-8 -*-

"""Import databases from mysql.

This script initializes the postgres database and then imports data from one or
more mysql databases.

.. note::

   Make sure to follow the steps in `database-access` first.

The source databases are:

1. a database containing the apparatus of the *Editio Critica Maior*
   publication (ECM).

2. a database containing the editorial decisions regarding the priority of the
   readings (VarGen).

3. a database containing the “Leitzeile” (Nestle).

The source tables for Acts are partitioned into 28 chapters.  This is a
historical incident: The software used when the CBGM was first implemented could
not handle big tables.  The import script is able to join partitioned tables.

After running this script should run the `prepare.py` script.

"""

import argparse
import collections
import logging
import re

import sqlalchemy

from ntg_common import db
from ntg_common import db_tools
from ntg_common.config import args, init_logging, config_from_pyfile
from ntg_common.db_tools import execute, warn, debug
from ntg_common.tools import log


def copy_table_fdw (conn, dest_table, fdw, source_table):
    """Copy a table. """

    execute (conn, """
    DROP TABLE IF EXISTS {dest_table};
    """, dict (parameters, dest_table = dest_table))

    execute (conn, """
    SELECT * INTO {dest_table} FROM  {fdw}."{source_table}"
    """, dict (parameters, fdw = fdw, dest_table = dest_table, source_table = source_table))


def concat_tables_fdw (conn, meta, dest_table, fdw, table_mask):
    """Concatenate multiple tables into one."""

    table_mask = re.compile ('^%s$' % table_mask)

    # find the set of fields common to all input tables.  check types also.  it
    # is ridiculous that we have to do this but the table structures are highly
    # inconsistent even between chapters of the same book.
    source_table = None
    column_set = collections.OrderedDict ()
    for t in sorted (meta.tables.keys ()):
        if table_mask.match (t):
            source_model = sqlalchemy.Table (t, meta, autoload = True)
            if source_table is None:
                source_table = t
                for c in source_model.columns:
                    column_set[c.name] = c.type.python_type
            else:
                col_set = { c.name : c.type.python_type for c in source_model.columns }
                for name, type_ in list (column_set.items ()):
                    if col_set.get (name, '') != type_:
                        del column_set[name]

    # create a table with those fields common to all input tables, lowercase the
    # field names
    execute (conn, """
    DROP TABLE IF EXISTS {dest_table}
    """, dict (parameters, dest_table = dest_table))

    execute (conn, """
    CREATE TABLE {dest_table} ( LIKE {fdw}."{source_table}" )
    """, dict (parameters, dest_table = dest_table, source_table = source_table, fdw = fdw))

    source_model = sqlalchemy.Table (source_table, meta, autoload = True)
    cols = [column.name for column in source_model.columns]

    for column in cols:
        if column in column_set:
            if column != column.lower ():
                execute (conn, 'ALTER TABLE {dest_table} RENAME COLUMN "{source_column}" TO "{dest_column}"',
                         dict (parameters, dest_table = dest_table, source_column = column, dest_column = column.lower ()))
        else:
            execute (conn, 'ALTER TABLE {dest_table} DROP COLUMN "{source_column}"',
                     dict (parameters, dest_table = dest_table, source_column = column, dest_column = column.lower ()))

    execute (conn, """COMMIT""", parameters);

    # concat the input tables
    for source_table in sorted (meta.tables.keys ()):
        if not table_mask.match (source_table):
            continue
        log (logging.DEBUG, "    Copying table %s" % source_table)

        source_columns = ['"' + column + '"'          for column in column_set.keys ()]
        dest_columns   = ['"' + column.lower () + '"' for column in column_set.keys ()]

        execute (conn, """
        INSERT INTO {dest_table} ({dest_columns})
        SELECT {source_columns}
        FROM {fdw}."{source_table}"
        """, dict (parameters, source_table = source_table, dest_table = dest_table, fdw = fdw,
                   source_columns = ', '.join (source_columns),
                   dest_columns = ', '.join (dest_columns)))


def import_att_fdw (dbsrc, dbdest, parameters):
    """Import att and lac tables from mysql.

    Import the (28 * 2) mysql tables to 2 tables in the postgres database.

    """

    log (logging.INFO, "  Importing mysql att tables ...")

    dbsrc_meta = sqlalchemy.schema.MetaData (bind = dbsrc.engine)
    dbsrc_meta.reflect ()

    with dbdest.engine.begin () as dest:
        concat_tables_fdw (dest, dbsrc_meta, 'original_att', 'app_fdw', config['MYSQL_ATT_TABLES'])

    with dbdest.engine.begin () as dest:
        if config.get ('MYSQL_LAC_TABLES'):
            log (logging.INFO, "  Importing mysql lac tables ...")
            concat_tables_fdw (dest, dbsrc_meta, 'original_lac', 'app_fdw', config['MYSQL_LAC_TABLES'])
        else:
            # no lacuna tables provided (eg. John)
            execute (dest, """
	        DROP TABLE IF EXISTS original_lac;
	        CREATE TABLE original_lac (LIKE original_att);
            """, parameters)

    with dbdest.engine.begin () as dest:
        execute (dest, """
        ALTER TABLE original_att RENAME COLUMN anfadr TO begadr;
        ALTER TABLE original_lac RENAME COLUMN anfadr TO begadr;
        """, parameters)


def import_genealogical_fdw (dbsrc, dbdest, parameters):
    """Import genealogical tables from mysql.

    Import the (28 * 3) mysql tables to 3 tables in the postgres database.

    """

    if not config.get ('MYSQL_VG_DB'):
        return

    dbsrc_meta = sqlalchemy.schema.MetaData (bind = dbsrc.engine)
    dbsrc_meta.reflect ()

    with dbdest.engine.begin () as dest:
        if config.get ('MYSQL_LOCSTEM_TABLES'):
            log (logging.INFO, "  Importing mysql locstem tables ...")
            concat_tables_fdw (dest, dbsrc_meta, 'original_locstemed', 'var_fdw', config['MYSQL_LOCSTEM_TABLES'])

    with dbdest.engine.begin () as dest:
        if config.get ('MYSQL_RDG_TABLES'):
            log (logging.INFO, "  Importing mysql rdg tables ...")
            concat_tables_fdw (dest, dbsrc_meta, 'original_rdg',       'var_fdw', config['MYSQL_RDG_TABLES'])

    with dbdest.engine.begin () as dest:
        if config.get ('MYSQL_VAR_TABLES'):
            log (logging.INFO, "  Importing mysql var tables ...")
            concat_tables_fdw (dest, dbsrc_meta, 'original_var',       'var_fdw', config['MYSQL_VAR_TABLES'])

    with dbdest.engine.begin () as dest:
        if config.get ('MYSQL_MEMO_TABLE'):
            log (logging.INFO, "  Importing mysql memo table ...")
            copy_table_fdw    (dest,             'original_memo',      'var_fdw', config['MYSQL_MEMO_TABLE'])
            execute (dest, """
            ALTER TABLE original_memo RENAME COLUMN anfadr TO begadr;
            """, parameters)


def import_nestle_fdw (dbsrc, dbdest, parameters):
    """Import Nestle table from mysql."""

    if config.get ('MYSQL_NESTLE_TABLE'):
        with dbdest.engine.begin () as dest:
            log (logging.INFO, "  Importing mysql nestle table ...")
            copy_table_fdw (dest, 'original_nestle', 'nestle_fdw', config['MYSQL_NESTLE_TABLE'])


def build_parser ():
    parser = argparse.ArgumentParser (description = __doc__)

    parser.add_argument ('profile', metavar='path/to/file.conf',
                         help="a .conf file (required)")
    parser.add_argument ('-v', '--verbose', dest='verbose', action='count',
                         help='increase output verbosity', default=0)
    return parser


if __name__ == '__main__':

    build_parser ().parse_args (namespace = args)
    config = config_from_pyfile (args.profile)

    init_logging (
        args,
        logging.StreamHandler (),
        logging.FileHandler ('import.log')
    )

    parameters = dict ()

    dbsrc1 = db_tools.MySQLEngine      (config['MYSQL_CONF'], config['MYSQL_GROUP'], config['MYSQL_ECM_DB'])
    dbsrc2 = db_tools.MySQLEngine      (config['MYSQL_CONF'], config['MYSQL_GROUP'], config['MYSQL_VG_DB'])
    dbsrc3 = db_tools.MySQLEngine      (config['MYSQL_CONF'], config['MYSQL_GROUP'], config['MYSQL_NESTLE_DB'])
    dbdest = db_tools.PostgreSQLEngine (**config)

    db.fdw ('app_fdw',    db.Base.metadata,  dbdest, dbsrc1)
    db.fdw ('var_fdw',    db.Base2.metadata, dbdest, dbsrc2)
    db.fdw ('nestle_fdw', db.Base4.metadata, dbdest, dbsrc3)

    log (logging.INFO, "Creating Database Schema ...")

    db.Base.metadata.drop_all  (dbdest.engine)
    db.Base2.metadata.drop_all (dbdest.engine)
    db.Base4.metadata.drop_all (dbdest.engine)

    db.Base.metadata.create_all  (dbdest.engine)
    db.Base2.metadata.create_all (dbdest.engine)
    db.Base4.metadata.create_all (dbdest.engine)

    log (logging.INFO, "Importing mysql tables ...")

    import_att_fdw (dbsrc1, dbdest, parameters)

    import_genealogical_fdw (dbsrc2, dbdest, parameters)

    import_nestle_fdw (dbsrc3, dbdest, parameters)

    log (logging.INFO, "Done")
