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
    """ Check the congruence.

    See: email Wachtel 16.01.2020

    """

    # query to get the closest ancestor for every ms

    res = execute (conn, """
    /* get the closest ancestor ms1 for every manuscript ms2 */
    WITH ranks AS (
      SELECT ms_id1, ms_id2,
        rank () OVER (PARTITION BY ms_id2 ORDER BY affinity DESC, common, older, newer DESC, ms_id1) AS rank,
        affinity
      FROM affinity_p_view aff
      WHERE ms_id1 NOT IN :exclude
        AND ms_id2 NOT IN :exclude
        AND aff.rg_id = :rg_id
        AND newer < older
        AND aff.common > aff.ms2_length / 2
      ORDER BY affinity DESC
    )

    SELECT ms1.hs, ms2.hs,
           ms1.ms_id, ms2.ms_id,
           labez_clique (q1.labez, q1.clique) as labez1,
           labez_clique (q2.labez, q2.clique) as labez2
    FROM ranks r
      JOIN manuscripts ms1 ON ms1.ms_id = r.ms_id1
      JOIN manuscripts ms2 ON ms2.ms_id = r.ms_id2
      JOIN apparatus_cliques_view q1 ON q1.ms_id = r.ms_id1 AND q1.pass_id = :pass_id
      JOIN apparatus_cliques_view q2 ON q2.ms_id = r.ms_id2 AND q2.pass_id = :pass_id
    WHERE r.rank <= 1
      AND labez_clique (q1.labez, q1.clique) != labez_clique (q2.labez, q2.clique)
      AND q1.labez != 'zz'
      AND q2.labez != 'zz'
      AND q1.certainty = 1.0
      AND q2.certainty = 1.0
      AND NOT EXISTS (
        SELECT * FROM locstem l
        WHERE (l.pass_id, l.labez, l.clique) = (:pass_id, q2.labez, q2.clique)
          AND (
            (l.source_labez, l.source_clique) = (q1.labez, q1.clique)
            OR l.source_labez = '?'
          )
      )
    ORDER BY ms1.hsnr
    """, dict (
        rg_id   = passage.range_id ('All'),
        pass_id = passage.pass_id,
        exclude = (2,),
    ))

    Ranks = collections.namedtuple ('Ranks', 'ms1 ms2 ms_id1 ms_id2 labez1 labez2')
    ranks = list (map (Ranks._make, res))

    tools.log (logging.INFO, 'rg_id: ' + str (passage.range_id ('All')))

    return ranks


@bp.route ('/checks/congruence.json/<passage_or_id>')
def congruence_json (passage_or_id = None):
    """ Endpoint: check the congruence """

    with current_app.config.dba.engine.begin () as conn:
        passage = Passage (conn, passage_or_id)
        return make_json_response (congruence (conn, passage))
