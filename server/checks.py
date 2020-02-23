# -*- encoding: utf-8 -*-

"""The API server for CBGM.  The checks module.

"""

import collections
import itertools
import logging

import flask
from flask import request, current_app

import numpy as np

from ntg_common.db_tools import execute
from ntg_common.cbgm_common import CBGM_Params, create_labez_matrix
from ntg_common import tools

from helpers import Passage, Manuscript, make_json_response, csvify


bp = flask.Blueprint ('checks', __name__)


def init_app (app):
    """ Init the Flask app. """

    pass


def congruence (conn, passage):
    """Check the congruence.

    "Das Prüfprogramm soll eine Inkongruenz anzeigen, wenn der Zeuge einer Lesart
    x, die im lokalen Stemma von y abhängt UND (bei x keinen pV mit Conn <= 5
    hat ODER bei y keinen pV mit höherem Rang hat als ein weiterer pV bei einer
    anderen Variante), nicht mit x ODER x(n) der Quelle "?" zugeordnet wird."
    -- email K. Wachtel 16.01.2020

    Wenn Lesart x im lokalen Stemma von y != ? abhängt, muß jeder Zeuge der
    Lesart x:

    1. einen pV(conn=5) der Lesart x haben, oder

    2. der höchste pV(!= zz) die Lesart y haben.

    Wenn Lesart x im lokalen Stemma von ? abhängt, ist keine Aussage möglich.

    """

    res = execute (conn, """
    -- get the closest ancestors ms1 for every manuscript ms2
    WITH ranks AS (
      SELECT
        aff.ms_id1,
        aff.ms_id2,
        ms1.hs as hs1,
        ms2.hs as hs2,
        q1.labez AS labez1,
        q2.labez AS labez2,
        q1.clique AS clique1,
        q2.clique AS clique2,
        labez_clique (q1.labez, q1.clique) as lq1,
        labez_clique (q2.labez, q2.clique) as lq2,
        l.source_labez,
        l.source_clique,
        labez_clique (l.source_labez, l.source_clique) as source_lq,
        rank () OVER (PARTITION BY ms_id2 ORDER BY affinity DESC, common, older, newer DESC, ms_id1) AS rank,
        affinity
      FROM affinity_p_view aff
        JOIN manuscripts ms1 ON ms1.ms_id = aff.ms_id1
        JOIN manuscripts ms2 ON ms2.ms_id = aff.ms_id2
        JOIN apparatus_cliques_view q1 ON q1.ms_id = aff.ms_id1 AND q1.pass_id = :pass_id
        JOIN apparatus_cliques_view q2 ON q2.ms_id = aff.ms_id2 AND q2.pass_id = :pass_id
        JOIN locstem l ON (l.pass_id, l.labez, l.clique) = (q2.pass_id, q2.labez, q2.clique)
      WHERE ms_id1 NOT IN :exclude
        AND ms_id2 NOT IN :exclude
        AND q1.labez != 'zz'
        AND q2.labez != 'zz'
        AND q1.certainty = 1.0
        AND q2.certainty = 1.0
        AND aff.rg_id = :rg_id
        AND aff.newer < aff.older
        AND aff.common > aff.ms2_length / 2
      ORDER BY affinity DESC
    )

    -- output mss that fail both rules
    SELECT hs1, hs2, ms_id1, ms_id2, lq1, lq2, rank
    FROM ranks r
    WHERE lq1 != lq2
      AND r.source_labez != '?'
      AND r.rank <= :connectivity
      AND -- ms2 fails rule 1
        NOT EXISTS (
          SELECT 1 FROM ranks rr
          WHERE rr.ms_id2 = r.ms_id2
            AND rr.lq1    = r.lq2
            AND rr.rank  <= :connectivity
        )
      AND -- ms2 fails rule 2
        NOT EXISTS (
          SELECT * FROM ranks rr
          WHERE rr.ms_id2     = r.ms_id2
            AND (rr.source_lq = r.lq1 OR rr.source_labez = '?')
            AND rr.rank <= 1
        )
    ORDER BY hs2, rank
    """, dict (
        rg_id   = passage.range_id ('All'),
        pass_id = passage.pass_id,
        connectivity = 5,
        exclude = (2,),
    ))

    Ranks = collections.namedtuple ('Ranks', 'ms1 ms2 ms_id1 ms_id2 labez1 labez2 rank')
    ranks = list (map (Ranks._make, res))

    tools.log (logging.INFO, 'rg_id: ' + str (passage.range_id ('All')))

    return ranks


@bp.route ('/checks/congruence.json/<passage_or_id>')
def congruence_json (passage_or_id = None):
    """ Endpoint: check the congruence """

    with current_app.config.dba.engine.begin () as conn:
        passage = Passage (conn, passage_or_id)
        return make_json_response (congruence (conn, passage))
