# -*- encoding: utf-8 -*-

"""Perform the CBGM.

This script

- rebuilds the 'A' text from the local stemmas,
- calculates the pre-coherence similarity of manuscripts, and
- calculates the post-coherence ancestrality of manuscripts.

This script updates the tables shown in red in the `overview <db-overwiew>`.
It also updates the Apparatus table where manuscript 'A is concerned.

"""

import argparse
import collections
import logging

import networkx as nx
import numpy as np

from ntg_common import db
from ntg_common import db_tools
from ntg_common.db_tools import execute, executemany, executemany_raw, warn, debug
from ntg_common.tools import log
from ntg_common.config import init_cmdline

from ntg_common.cbgm_common import CBGM_Params, create_labez_matrix, \
    calculate_mss_similarity_preco, calculate_mss_similarity_postco, write_affinity_table

MS_ID_A  = 1

def build_A_text (dba, parameters):
    """Build the 'A' text

    The editors' reconstruction of the archetype is recorded in the locstem
    table. This functions generates a virtual manuscript 'A' from those choices.

    The designation of a passage as 'Fehlvers' is an editorial decision that the
    verse is not original, so we set 'zu'.

    If the editors came to no final decision, no 'original' reading will be
    found in locstem.  In this case we set 'A' to 'zz' and there will be a gap
    in the reconstructed text.

    The Lesart of 'A' is always NULL, because it is a virtual manuscript.

    """

    with dba.engine.begin () as conn:

        execute (conn, """
        DELETE FROM ms_cliques     WHERE ms_id = :ms_id;
        DELETE FROM ms_cliques_tts WHERE ms_id = :ms_id;
        DELETE FROM apparatus      WHERE ms_id = :ms_id;
        """, dict (parameters, ms_id = MS_ID_A))

        # Fill with the original reading in locstem or 'zz' if none found
        execute (conn, """
        INSERT INTO apparatus_cliques_view (ms_id, pass_id, labez, clique, cbgm, origin, lesart)
          SELECT :ms_id, p.pass_id, COALESCE (l.labez, 'zz'), COALESCE (l.clique, '1'), true, 'LOC', NULL
          FROM passages p
          LEFT JOIN locstem l ON (l.pass_id, l.original) = (p.pass_id, true)
          WHERE NOT p.fehlvers
        """, dict (parameters, ms_id = MS_ID_A))

        # Fill Fehlverse with labez 'zu'
        execute (conn, """
        INSERT INTO apparatus_cliques_view (ms_id, pass_id, labez, clique, cbgm, origin, lesart)
          SELECT :ms_id, p.pass_id, 'zu', '1', true, 'LOC', NULL
          FROM passages p
          WHERE p.fehlvers
        """, dict (parameters, ms_id = MS_ID_A))


def build_parser ():
    parser = argparse.ArgumentParser (description = __doc__)

    parser.add_argument ('profile', metavar='path/to/file.conf',
                         help="a .conf file (required)")
    parser.add_argument ('-v', '--verbose', dest='verbose', action='count',
                         help='increase output verbosity', default=0)
    return parser


if __name__ == '__main__':
    args, config = init_cmdline (build_parser ())

    db = db_tools.PostgreSQLEngine (**config)
    parameters = dict ()
    v = CBGM_Params ()

    log (logging.INFO, "Rebuilding the 'A' text ...")
    build_A_text (db, parameters)

    log (logging.INFO, "Creating the labez matrix ...")
    create_labez_matrix (db, parameters, v)

    log (logging.INFO, "Calculating mss similarity pre-co ...")
    calculate_mss_similarity_preco (db, parameters, v)

    log (logging.INFO, "Calculating mss similarity post-co ...")
    calculate_mss_similarity_postco (db, parameters, v)

    log (logging.INFO, "Writing affinity table ...")
    write_affinity_table (db, parameters, v)

    log (logging.INFO, "Vacuum ...")
    db.vacuum ()

    log (logging.INFO, "Done")
