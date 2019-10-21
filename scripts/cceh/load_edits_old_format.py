# -*- encoding: utf-8 -*-

"""Load a saved state of the editor tables.

This script loads the state of the tables with the editorial decisions as saved
by the save_edits.py script.  It does not touch the apparatus tables.

While loading, it checks for errors and discrepancies, eg. different passage
addresses.  Passages in the apparatus that are not in the save state are reset
to the default of: reading 'a' is original and every other reading is derived
from 'a'.

"""

import argparse
import logging
import sys

import lxml

from ntg_common import db
from ntg_common import db_tools
from ntg_common.db_tools import execute, executemany, warn
from ntg_common.tools import log
from ntg_common.config import args, init_logging, config_from_pyfile


def build_parser ():
    parser = argparse.ArgumentParser (description = __doc__)

    parser.add_argument ('-v', '--verbose', dest='verbose', action='count',
                         help='increase output verbosity', default=0)
    parser.add_argument ('-i', '--input', metavar='path/to/input.xml',
                         help="the input file (required)", required=True)
    parser.add_argument ('profile', metavar='path/to/file.conf',
                         help="a .conf file (required)")
    return parser


if __name__ == '__main__':

    build_parser ().parse_args (namespace = args)
    config = config_from_pyfile (args.profile)

    init_logging (
        args,
        logging.StreamHandler (), # stderr
        logging.FileHandler ('load_edits.log')
    )

    parameters = dict ()
    db = db_tools.PostgreSQLEngine (**config)

    tree = lxml.etree.parse (args.input if args.input != '-' else sys.stdin)

    with db.engine.begin () as conn:
        db_tools.truncate_editor_tables (conn)

        log (logging.INFO, "Build default cliques ...")
        db_tools.init_default_cliques (conn)
        log (logging.INFO, "Build default ms_cliques ...")
        db_tools.init_default_ms_cliques (conn)
        log (logging.INFO, "Build default locstem ...")
        db_tools.init_default_locstem (conn)
        # default notes is an empty table

    log (logging.INFO, "Loading cliques ...")

    with db.engine.begin () as conn:
        values = []
        for row in tree.xpath ('/sql/export_cliques/row'):
            values.append ({ e.tag : e.text for e in row })

        execute (conn, """
        TRUNCATE import_cliques;
        """, parameters)

        executemany (conn, """
        INSERT INTO import_cliques (passage, labez, clique,
                                    sys_period, user_id_start, user_id_stop)
        VALUES (:passage, :labez, :clique,
                :sys_period, :user_id_start, :user_id_stop)
        """, parameters, values)

        execute (conn, """
        UPDATE import_cliques u
        SET pass_id = r.pass_id
        FROM readings_view r
        WHERE (u.passage, u.labez) = (r.passage, r.labez)
        """, parameters)

        warn (conn, "Discarded cliques", """
        SELECT passage, labez, clique
        FROM import_cliques
        WHERE pass_id IS NULL
        ORDER BY passage, labez, clique
        """, parameters)

        execute (conn, """
        DELETE FROM import_cliques
        WHERE pass_id IS NULL
        """, parameters)

    with db.engine.begin () as conn:
        execute (conn, """
        ALTER TABLE cliques DISABLE TRIGGER cliques_trigger;

        INSERT INTO cliques (pass_id, labez, clique,
                             sys_period, user_id_start, user_id_stop)
        SELECT pass_id, labez, clique,
               sys_period, user_id_start, user_id_stop
        FROM import_cliques
        WHERE UPPER_INF (sys_period);

        INSERT INTO cliques_tts (pass_id, labez, clique,
                                 sys_period, user_id_start, user_id_stop)
        SELECT pass_id, labez, clique,
               sys_period, user_id_start, user_id_stop
        FROM import_cliques
        WHERE NOT UPPER_INF (sys_period);

        ALTER TABLE cliques ENABLE TRIGGER cliques_trigger;
        """, parameters)


    log (logging.INFO, "Loading ms_cliques ...")

    with db.engine.begin () as conn:
        values = []
        for row in tree.xpath ('/sql/export_ms_cliques/row'):
            values.append ({ e.tag : e.text for e in row })

        execute (conn, """
        TRUNCATE import_ms_cliques;
        """, parameters)

        executemany (conn, """
        INSERT INTO import_ms_cliques (hsnr, passage, labez, clique,
                                       sys_period, user_id_start, user_id_stop)
        VALUES (:hsnr, :passage, :labez, :clique,
                :sys_period, :user_id_start, :user_id_stop)
        """, parameters, values)

        # do not refer to cliques_view as that could kill entries in the history
        execute (conn, """
        UPDATE import_ms_cliques u
        SET ms_id = a.ms_id, pass_id = a.pass_id
        FROM apparatus_view a
        WHERE (u.passage, u.labez, u.hsnr) = (a.passage, a.labez, a.hsnr)
        """, parameters)

        warn (conn, "Discarded ms_cliques", """
        SELECT hsnr, passage, labez, clique
        FROM import_ms_cliques
        WHERE pass_id IS NULL OR ms_id IS NULL
        ORDER BY hsnr, passage, labez, clique
        """, parameters)

        execute (conn, """
        DELETE FROM import_ms_cliques
        WHERE pass_id IS NULL OR ms_id IS NULL
        """, parameters)

    with db.engine.begin () as conn:
        execute (conn, """
        ALTER TABLE ms_cliques DISABLE TRIGGER ms_cliques_trigger;

        INSERT INTO ms_cliques AS u (ms_id, pass_id, labez, clique,
                                     sys_period, user_id_start, user_id_stop)
        SELECT ms_id, pass_id, labez, clique,
               sys_period, user_id_start, user_id_stop
        FROM import_ms_cliques
        WHERE UPPER_INF (sys_period)
        ON CONFLICT (ms_id, pass_id, labez) DO
        UPDATE
        SET (clique, sys_period, user_id_start, user_id_stop) =
            (EXCLUDED.clique, EXCLUDED.sys_period, EXCLUDED.user_id_start, EXCLUDED.user_id_stop)
        WHERE (u.ms_id, u.pass_id, u.labez) = (EXCLUDED.ms_id, EXCLUDED.pass_id, EXCLUDED.labez);

        INSERT INTO ms_cliques_tts AS u (ms_id, pass_id, labez, clique,
                                         sys_period, user_id_start, user_id_stop)
        SELECT ms_id, pass_id, labez, clique,
               sys_period, user_id_start, user_id_stop
        FROM import_ms_cliques
        WHERE NOT UPPER_INF (sys_period);

        ALTER TABLE ms_cliques ENABLE TRIGGER ms_cliques_trigger;
        """, parameters)


    log (logging.INFO, "Loading locstem ...")

    with db.engine.begin () as conn:
        values = []
        for row in tree.xpath ('/sql/export_locstem/row'):
            values.append ({ e.tag : e.text for e in row })

        # fix schema changed in #79
        for v in values:
            if v['source_labez'] is None:
                v['source_labez']  = '*' if v['original'] == 'true' else '?'
                v['source_clique'] = '1'

        execute (conn, """
        TRUNCATE import_locstem;
        """, parameters)

        executemany (conn, """
        INSERT INTO import_locstem (passage, labez, clique, source_labez, source_clique,
                                   sys_period, user_id_start, user_id_stop)
        VALUES (:passage, :labez, :clique, :source_labez, :source_clique,
                :sys_period, :user_id_start, :user_id_stop)
        """, parameters, values)

        # do not refer to cliques_view as that could kill entries in the history
        execute (conn, """
        UPDATE import_locstem u
        SET pass_id = r.pass_id
        FROM readings_view r
        WHERE (u.passage, u.labez) = (r.passage, r.labez)
        """, parameters)

        warn (conn, "Discarded LocStem", """
        SELECT passage, labez, clique
        FROM import_locstem
        WHERE pass_id IS NULL
        ORDER BY passage, labez, clique
        """, parameters)

        execute (conn, """
        DELETE FROM import_locstem
        WHERE pass_id IS NULL
        """, parameters)

        execute (conn, """
        UPDATE locstem
        SET source_labez = '?'
        WHERE pass_id = 1477
        """, parameters)

    with db.engine.begin () as conn:
        execute (conn, """
        ALTER TABLE locstem DISABLE TRIGGER locstem_trigger;
        CREATE UNIQUE INDEX ix_locstem_import ON locstem (pass_id, labez, clique);

        INSERT INTO locstem AS u (pass_id, labez, clique, source_labez, source_clique,
                                  sys_period, user_id_start, user_id_stop)
        SELECT pass_id, labez, clique, source_labez, source_clique,
               sys_period, user_id_start, user_id_stop
        FROM import_locstem
        WHERE UPPER_INF (sys_period)
        ORDER BY source_labez DESC
        ON CONFLICT (pass_id, labez, clique) DO
        UPDATE
        SET (source_labez, source_clique, sys_period, user_id_start, user_id_stop) =
            (EXCLUDED.source_labez, EXCLUDED.source_clique,
             EXCLUDED.sys_period, EXCLUDED.user_id_start, EXCLUDED.user_id_stop)
        WHERE (u.pass_id, u.labez, u.clique) = (EXCLUDED.pass_id, EXCLUDED.labez, EXCLUDED.clique);

        INSERT INTO locstem_tts AS u (pass_id, labez, clique, source_labez, source_clique,
                                     sys_period, user_id_start, user_id_stop)
        SELECT pass_id, labez, clique, source_labez, source_clique,
               sys_period, user_id_start, user_id_stop
        FROM import_locstem
        WHERE NOT UPPER_INF (sys_period);

        DROP INDEX ix_locstem_import;
        ALTER TABLE locstem ENABLE TRIGGER locstem_trigger;
        """, parameters)


    log (logging.INFO, "Loading notes ...")

    with db.engine.begin () as conn:
        values = []
        for row in tree.xpath ('/sql/export_notes/row'):
            values.append ({ e.tag : e.text for e in row })

        execute (conn, """
        TRUNCATE import_notes;
        """, parameters)

        executemany (conn, """
        INSERT INTO import_notes (passage, note,
                                  sys_period, user_id_start, user_id_stop)
        VALUES (:passage, COALESCE (:note, ''),
                :sys_period, :user_id_start, :user_id_stop)
        """, parameters, values)

        execute (conn, """
        UPDATE import_notes u
        SET pass_id = p.pass_id
        FROM passages p
        WHERE u.passage = p.passage
        """, parameters)

        warn (conn, "Discarded Notes", """
        SELECT passage
        FROM import_notes
        WHERE pass_id IS NULL
        ORDER BY passage
        """, parameters)

        execute (conn, """
        DELETE FROM import_notes
        WHERE pass_id IS NULL
        """, parameters)

    with db.engine.begin () as conn:
        execute (conn, """
        ALTER TABLE notes DISABLE TRIGGER notes_trigger;

        INSERT INTO notes AS u (pass_id, note,
                                sys_period, user_id_start, user_id_stop)
        SELECT pass_id, note,
               sys_period, user_id_start, user_id_stop
        FROM import_notes
        WHERE UPPER_INF (sys_period);

        INSERT INTO notes_tts AS u (pass_id, note,
                                    sys_period, user_id_start, user_id_stop)
        SELECT pass_id, note,
               sys_period, user_id_start, user_id_stop
        FROM import_notes
        WHERE NOT UPPER_INF (sys_period);

        ALTER TABLE notes ENABLE TRIGGER notes_trigger;
        """, parameters)


    log (logging.INFO, "Done")
