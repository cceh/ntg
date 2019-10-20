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
from ntg_common.db_tools import execute, executemany, warn, info, fix
from ntg_common.tools import log
from ntg_common.config import init_cmdline


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
    args, config = init_cmdline (build_parser ())

    parameters = dict ()
    db = db_tools.PostgreSQLEngine (**config)

    tree = lxml.etree.parse (args.input if args.input != '-' else sys.stdin)

    with db.engine.begin () as conn:
        db_tools.truncate_editor_tables (conn)

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

        info (conn, "Discarded cliques", """
        SELECT passage, ARRAY_AGG (labez_clique (labez, clique) ORDER BY labez, clique) AS old_clique
        FROM import_cliques
        WHERE pass_id IS NULL AND UPPER_INF (sys_period)
        GROUP BY passage
        ORDER BY passage
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

        -- default entries
        INSERT INTO cliques (pass_id, labez, clique, user_id_start)
        SELECT pass_id, labez, '1', 0
        FROM readings r
        ON CONFLICT (pass_id, labez, clique) DO NOTHING;

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

        # do not refer to cliques_view as it may not contain cliques in the history table
        execute (conn, """
        UPDATE import_ms_cliques u
        SET ms_id = a.ms_id, pass_id = a.pass_id
        FROM apparatus_view a
        WHERE (u.passage, u.labez, u.hsnr) = (a.passage, a.labez, a.hsnr)
        """, parameters)

        info (conn, "Discarded ms_cliques", """
        SELECT passage, labez_clique (labez, clique) AS old_clique, ARRAY_AGG (hsnr ORDER BY hsnr) AS hsnr
        FROM import_ms_cliques
        WHERE (pass_id IS NULL OR ms_id IS NULL) AND UPPER_INF (sys_period)
        GROUP BY passage, labez, clique
        ORDER BY passage, labez, clique
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
        WHERE UPPER_INF (sys_period);

        INSERT INTO ms_cliques_tts AS u (ms_id, pass_id, labez, clique,
                                         sys_period, user_id_start, user_id_stop)
        SELECT ms_id, pass_id, labez, clique,
               sys_period, user_id_start, user_id_stop
        FROM import_ms_cliques
        WHERE NOT UPPER_INF (sys_period);

        -- default entries
        INSERT INTO ms_cliques AS u (ms_id, pass_id, labez, clique, user_id_start)
        SELECT a.ms_id, a.pass_id, a.labez, '1', 0
        FROM apparatus a
        ON CONFLICT (ms_id, pass_id, labez) DO NOTHING;

        ALTER TABLE ms_cliques ENABLE TRIGGER ms_cliques_trigger;
        """, parameters)


    log (logging.INFO, "Loading locstem ...")

    values = []
    for row in tree.xpath ('/sql/export_locstem/row'):
        values.append ({ e.tag : e.text for e in row })

    with db.engine.begin () as conn:
        execute (conn, """
        TRUNCATE import_locstem;
        """, parameters)

        executemany (conn, """
        INSERT INTO import_locstem (passage, labez, clique, source_labez, source_clique,
                                   sys_period, user_id_start, user_id_stop)
        VALUES (:passage, :labez, :clique, :source_labez, :source_clique,
                :sys_period, :user_id_start, :user_id_stop)
        """, parameters, values)

        # set the pass_id
        execute (conn, """
        UPDATE import_locstem u
        SET pass_id = p.pass_id
        FROM passages p
        WHERE u.passage = p.passage;
        """, parameters)

        warn (conn, "Discarded Passages", """
        SELECT passage AS old_passage,
               ARRAY_AGG (labez_clique (labez, clique) ORDER BY labez, clique) AS old_clique
        FROM import_locstem
        WHERE pass_id IS NULL AND UPPER_INF (sys_period)
        GROUP BY passage
        ORDER BY passage
        """, parameters)

        execute (conn, """
        DELETE FROM import_locstem
        WHERE pass_id IS NULL;
        """, parameters)

        # list all new passages
        warn (conn, "New Passages", """
        SELECT passage AS new_passage,
               ARRAY_AGG (DISTINCT labez ORDER BY labez) AS new_labez
        FROM readings_view
        WHERE pass_id NOT IN (
          SELECT pass_id
          FROM import_locstem
        )
        AND labez !~ '^zz'
        GROUP BY passage
        ORDER BY passage
        """, parameters)

        # list all new readings (except where already listed as passage before)
        warn (conn, "New Readings", """
        SELECT passage AS old_passage,
               ARRAY_AGG (DISTINCT labez ORDER BY labez) AS new_labez
        FROM readings_view
        WHERE pass_id IN (
          SELECT pass_id
          FROM import_locstem
        )
        AND (pass_id, labez) NOT IN (
          SELECT pass_id, labez
          FROM import_locstem
        )
        AND labez !~ '^z[u-z]'
        GROUP BY passage
        ORDER BY passage
        """, parameters)

        # delete obsolete stuff
        execute (conn, """
        DELETE FROM import_locstem
        WHERE (pass_id, labez, clique) NOT IN (
          SELECT pass_id, labez, clique
          FROM cliques
        );

        DELETE FROM import_locstem
        WHERE source_labez NOT IN ('*', '?')
        AND (pass_id, source_labez, source_clique) NOT IN (
          SELECT pass_id, labez, clique
          FROM cliques
        );
        """, parameters)


    with db.engine.begin () as conn:
        execute (conn, """
        ALTER TABLE locstem DISABLE TRIGGER locstem_trigger;

        INSERT INTO locstem AS u (pass_id, labez, clique, source_labez, source_clique,
                                  sys_period, user_id_start, user_id_stop)
        SELECT i.pass_id, i.labez, i.clique, i.source_labez, i.source_clique,
               i.sys_period, i.user_id_start, i.user_id_stop
        FROM import_locstem i
        WHERE UPPER_INF (i.sys_period);

        INSERT INTO locstem_tts AS u (pass_id, labez, clique, source_labez, source_clique,
                                     sys_period, user_id_start, user_id_stop)
        SELECT i.pass_id, i.labez, i.clique, i.source_labez, i.source_clique,
               i.sys_period, i.user_id_start, i.user_id_stop
        FROM import_locstem i
        WHERE NOT UPPER_INF (i.sys_period);

        -- insert default dependency: 'a1' is original
        INSERT INTO locstem (pass_id, labez, clique, source_labez, source_clique, user_id_start)
        SELECT pass_id, 'a', '1', '*', '1', 0
        FROM cliques q
        WHERE labez = 'a' AND clique = '1'
        AND (pass_id, labez, clique) NOT IN (
          SELECT pass_id, labez, clique
          FROM locstem
        );

        -- insert default dependency: not 'a1' depends on 'a1'
        INSERT INTO locstem (pass_id, labez, clique, source_labez, source_clique, user_id_start)
        SELECT pass_id, labez, clique, '?', '1', 0
        FROM cliques q
        WHERE NOT (labez = 'a' AND clique = '1') AND labez !~ '^z[u-z]'
        -- on conflict do nothing would not work here because
        -- one reading may depend on arbitrary many readings
        -- and we'd just make everybody also depend on 'a'
        AND (pass_id, labez, clique) NOT IN (
          SELECT pass_id, labez, clique
          FROM locstem
        );

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
        SELECT passage, note
        FROM import_notes
        WHERE pass_id IS NULL AND UPPER_INF (sys_period)
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
