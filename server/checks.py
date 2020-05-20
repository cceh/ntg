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


def congruence_list (conn, passage, range_id):
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
    WITH ranked AS (
      SELECT
        ms_id1,
        ms_id2,
        rank () OVER (PARTITION BY ms_id2 ORDER BY affinity DESC, common, older, newer DESC, ms_id1) AS rank,
        affinity
      FROM affinity_p_view aff
      WHERE ms_id1 NOT IN :exclude
        AND ms_id2 NOT IN :exclude
        AND aff.rg_id = :rg_id
        AND aff.newer < aff.older
        AND aff.common > aff.ms2_length / 2
      ORDER BY ms_id2, affinity DESC
    ),

    -- get readings
    readings AS (
      SELECT
        p.pass_id,
        p.begadr,
        p.endadr,
        r.ms_id1,
        r.ms_id2,
        r.rank,
        q1.labez AS labez1,
        q2.labez AS labez2,
        q1.clique AS clique1,
        q2.clique AS clique2,
        labez_clique (q1.labez, q1.clique) as lq1,
        labez_clique (q2.labez, q2.clique) as lq2,
        l.source_labez  as source_l2,
        l.source_clique as source_q2,
        labez_clique (l.source_labez, l.source_clique) as source_lq2,
        row_number () OVER (PARTITION BY p.pass_id, r.ms_id2 ORDER BY r.rank) as row_no,
        count (*) FILTER (WHERE q1.labez !~ '^z') OVER (
           PARTITION BY p.pass_id, r.ms_id2
           ORDER BY r.rank
           ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) as row_no_no_zz
      FROM passages p
        JOIN ranges rg ON (rg.rg_id = :range_id AND rg.passage @> p.passage)
      CROSS JOIN ranked r
        JOIN apparatus_cliques_view q1 ON q1.ms_id = r.ms_id1 AND q1.pass_id = p.pass_id
        JOIN apparatus_cliques_view q2 ON q2.ms_id = r.ms_id2 AND q2.pass_id = p.pass_id
        JOIN locstem l ON (l.pass_id, l.labez, l.clique) = (q2.pass_id, q2.labez, q2.clique)
      WHERE q1.certainty = 1.0
        AND q2.certainty = 1.0
        AND r.rank <= 2 * :connectivity -- speed things up
      ORDER BY pass_id, ms_id2, rank
    )

    -- output mss that fail both rules
    SELECT
      r.pass_id, r.begadr, r.endadr, ms1.hs AS hs1, ms2.hs AS hs2, r.ms_id1, r.ms_id2, r.lq1, r.lq2, r.rank
    FROM readings r
      JOIN manuscripts ms1 ON ms1.ms_id = r.ms_id1
      JOIN manuscripts ms2 ON ms2.ms_id = r.ms_id2
    WHERE r.lq2       != lq1
      AND r.labez1    !~ '^z'
      AND r.labez2    !~ '^z'
      AND r.source_l2 != '?'
      AND r.row_no    = 1
      -- ancestor ms1 reads different from descendant ms2
      AND -- ms2 fails rule 1 (muß einen pV(conn=5) der Lesart x haben)
        NOT EXISTS (
          SELECT 1 FROM readings c
          WHERE c.ms_id2  = r.ms_id2
            AND c.pass_id = r.pass_id
            AND c.lq1     = r.lq2
            AND c.row_no <= :connectivity
        )
      AND -- ms2 fails rule 2 (der höchste pV(!= zz) muß die Lesart y haben)
        NOT EXISTS (
          SELECT 1 FROM readings c
          WHERE c.ms_id2  = r.ms_id2
            AND c.pass_id = r.pass_id
            AND c.lq1     = r.source_lq2
            AND c.row_no_no_zz = 1
        )

    ORDER BY pass_id, ms1.hsnr
    """, dict (
        rg_id = passage.range_id ('All'),
        range_id = range_id,
        connectivity = 5,
        exclude = (1,2),
    ))

    Ranks = collections.namedtuple ('Ranks', 'pass_id begadr endadr ms1 ms2 ms_id1 ms_id2 labez1 labez2 rank')
    ranks = []
    for r in res:
        rank = Ranks._make (r)._asdict ()
        rank['hr'] = Passage.static_to_hr (rank['begadr'], rank['endadr'])
        ranks.append (rank)

    return ranks


@bp.route ('/checks/congruence.json/<passage_or_id>')
def congruence_json (passage_or_id):
    """ Endpoint: check the congruence """

    with current_app.config.dba.engine.begin () as conn:
        passage = Passage (conn, passage_or_id)
        return make_json_response (congruence (conn, passage))


@bp.route ('/checks/congruence_list.json/<range_id>')
def congruence_list_json (range_id):
    """ Endpoint: check the congruence """

    with current_app.config.dba.engine.begin () as conn:
        passage = Passage (conn, 1)
        return make_json_response (congruence_list (conn, passage, range_id))
