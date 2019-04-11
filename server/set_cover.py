# -*- encoding: utf-8 -*-

"""An application server for CBGM.  Set cover module.

See: CBGM_Pres.pdf p. 490ff.

"""

import collections
import itertools
import logging
import re

import flask
from flask import request, current_app
import flask_login

import numpy as np
import networkx as nx
import sqlalchemy

from ntg_common import tools
from ntg_common import db_tools
from ntg_common.db_tools import execute
from ntg_common.cbgm_common import CBGM_Params, create_labez_matrix, \
    calculate_mss_similarity_preco, calculate_mss_similarity_postco

from .helpers import parameters, Passage, Manuscript, make_json_response, make_text_response


MAX_COVER_SIZE = 12

app = flask.Blueprint ('set_cover', __name__)

def get_ancestors (conn, rg_id, ms_id):
    """ Get all ancestors of ms. """

    mode = 'sim'
    view = 'affinity_view' if mode == 'rec' else 'affinity_p_view'

    res = execute (conn, """
    SELECT aff.ms_id2 as ms_id,
           aff.ms2_length,
           aff.common,
           aff.equal,
           aff.older,
           aff.newer,
           aff.unclear,
           aff.common - aff.equal - aff.older - aff.newer - aff.unclear as norel,
           aff.affinity
    FROM
      {view} aff
    WHERE aff.ms_id1 = :ms_id1 AND aff.rg_id = :rg_id
          AND aff.common > 0 AND aff.older < aff.newer
    ORDER BY affinity DESC, newer DESC, older DESC
    """, dict (ms_id1  = ms_id,
               rg_id   = rg_id,
               view    = view))

    ancestors = collections.namedtuple (
        'Ancestors',
        'ms_id length common equal older newer unclear norel affinity'
    )

    return frozenset ([r[0] for r in res])


def powerset (iterable):
    """powerset([1,2,3]) --> () (1,) (2,) (3,) (1,2) (1,3) (2,3) (1,2,3)"""
    s = list (iterable)
    return itertools.chain.from_iterable (itertools.combinations (s, r) for r in range (len (s) + 1))


WITH_SELECT = """
  SELECT pass_id, labez, clique,
         (1 << (ROW_NUMBER () OVER (PARTITION BY pass_id ORDER BY labez, clique)::integer)) AS rn
  FROM cliques
  WHERE labez !~ '^z'
"""

def init (db):
    val = CBGM_Params ()
    parameters = {}

    with db.engine.begin () as conn:
        # get max number of different cliques in any one passage
        res = execute (conn, """
        SELECT MAX (c)
        FROM (
          SELECT COUNT ((labez, clique)) AS c
          FROM locstem
          WHERE labez !~ '^z'
          GROUP BY pass_id
        ) AS foo
        """, {})
        n_cliques = res.fetchone ()[0]
        # see that the bitmask fits into uint64
        # one bit is reserved for 'unknown' derivation
        assert n_cliques < 64

        # load all attestations into one big numpy array
        create_labez_matrix (db, parameters, val)

        # build a mask of all readings of all mss.
        # every labez_clique gets an id (in the range 0..63)

        # Matrix mss x passages containing the bitmask of all manuscripts readings
        val.mask_matrix = np.zeros ((val.n_mss, val.n_passages), dtype = np.uint64)

        res = execute (conn, """
        WITH rn AS (
          {with}
        )
        SELECT msq.ms_id, msq.pass_id, rn1.rn
        FROM ms_cliques AS msq
        JOIN (select * from rn) as rn1
          USING (pass_id, labez, clique)
        """, { 'with' : WITH_SELECT })

        mask_row = collections.namedtuple ('Mask_Row', 'ms_id, pass_id, shift')
        for r in res:
            mask = mask_row._make (r)
            val.mask_matrix[mask.ms_id - 1, mask.pass_id - 1] = np.uint64 (mask.shift)

    return val


def build_explain_matrix (conn, val, ms_id):
    """Build the explain matrix.

    A matrix of 1 x n_passages containing the bitmask of all those readings that
    would explain the reading in the manuscript under scrutiny.

    Bit 1 means: the reading stems from an unknown source.
    Bit 2..64 are the bitmask.

    """

    explain_matrix = np.zeros (val.n_passages, dtype = np.uint64)

    res = execute (conn, """
    WITH RECURSIVE
    rn AS (
      {with}
    ),
    lsrn AS (
      SELECT ls.pass_id, ls.labez, ls.clique,
        -- set 1 as flag for unknown derivation
        CASE WHEN (ls.source_labez IS NULL) AND NOT ls.original THEN rn1.rn + 1 ELSE rn1.rn END AS rn1,
        rn2.rn AS rn2
      FROM locstem ls
      JOIN rn as rn1
        USING (pass_id, labez, clique)
      LEFT JOIN rn as rn2
        ON (ls.pass_id, ls.source_labez, ls.source_clique) = (rn2.pass_id, rn2.labez, rn2.clique)
    ),
    lsrec (pass_id, rn1, rn2) AS (
      SELECT lsrn.pass_id, lsrn.rn1, lsrn.rn2
      FROM ms_cliques AS msq
        JOIN lsrn USING (pass_id, labez, clique)
      WHERE ms_id = :ms_id
    UNION
      SELECT lsrn.pass_id, lsrn.rn1, lsrn.rn2
      FROM lsrec
      JOIN lsrn
        ON (lsrn.pass_id = lsrec.pass_id AND lsrn.rn1 = lsrec.rn2)
    )
    SELECT pass_id, SUM (rn1) AS rn
    FROM lsrec
    GROUP BY pass_id
    ORDER BY pass_id;
    """, { 'with' : WITH_SELECT, 'ms_id' : ms_id })

    explain_row = collections.namedtuple ('Explain_Row', 'pass_id, mask')
    for r in res:
        mask = explain_row._make (r)
        explain_matrix[mask.pass_id - 1] = np.uint64 (mask.mask)

    return explain_matrix


def init_app (app):
    app.config.val = None
    app.config.set_cover_rg_id = None

    with app.config.dba.engine.begin () as conn:
        try:
            res = execute (conn, """
            SELECT bk_id
            FROM books
            WHERE book = :book
            """, { 'book' : app.config['BOOK'] })
            bk_id = res.fetchone ()[0]

            res = execute (conn, """
            SELECT rg_id
            FROM ranges
            WHERE bk_id = :bk_id AND range = 'All'
            """, { 'bk_id' : bk_id })
            rg_id = res.fetchone ()[0]

            app.config.set_cover_rg_id = rg_id
        except:
            pass # FIXME


@app.endpoint ('set-cover.json')
def set_cover_json (hs_hsnr_id):
    """ Approximate the minimum set cover for a manuscript.

    See: https://en.wikipedia.org/wiki/Set_cover_problem
    """

    response = {}

    with current_app.config.dba.engine.begin () as conn:
        if current_app.config.val is None:
            current_app.config.val = init (current_app.config.dba)
        val = current_app.config.val

        parameters = {}
        cover = []

        ms = Manuscript (conn, hs_hsnr_id)
        response['ms'] = ms.to_json ()
        ms_id = ms.ms_id - 1  # numpy indices start at 0

        # allow user to pre-select a set of manuscripts
        pre_selected = [ Manuscript (conn, anc_id)
                      for anc_id in (request.args.get ('pre_select') or '').split () ]
        response['mss'] = [s.to_json () for s in pre_selected]

        np.set_printoptions (edgeitems = 8, linewidth = 100)

        b_common = np.logical_and (val.def_matrix, val.def_matrix[ms_id])
        b_common[ms_id] = False  # don't find original ms.
        b_common[0]     = False  # don't find A
        b_common[1]     = False  # don't find MT

        # eliminate descendants from the matrix
        ancestors = get_ancestors (conn, current_app.config.set_cover_rg_id, ms.ms_id)
        for i in range (0, val.n_mss):
            if ((i + 1) not in ancestors) :
                b_common[i] = 0

        n_defined = np.count_nonzero (val.def_matrix[ms_id])
        response['ms']['open'] = n_defined

        explain_matrix = build_explain_matrix (conn, val, ms.ms_id)

        explain_equal_matrix = val.mask_matrix[ms_id]

        # The mss x passages boolean matrix that is TRUE whenever the inspected ms.
        # agrees with the potential source ms.
        b_equal = np.bitwise_and (val.mask_matrix, explain_equal_matrix) > 0
        b_equal = np.logical_and (b_equal, b_common)

        # The mss x passages boolean matrix that is TRUE whenever the inspected ms.
        # agrees with the potential source ms. or is posterior to it.
        b_post = np.bitwise_and (val.mask_matrix, explain_matrix) > 0
        b_post = np.logical_and (b_post, b_common)

        n_explained = 0

        for n in range (0, MAX_COVER_SIZE):
            if n < len (pre_selected):
                # use manuscript pre-selected by user
                ms_id_most_similar = pre_selected[n].ms_id - 1
            else:
                # find manuscript that explains the most passages
                ms_id_most_similar = int (np.argmax (np.sum (b_post, axis = 1)))

            b_explained        = np.copy (b_post[ms_id_most_similar])
            b_explained_equal  = np.copy (b_equal[ms_id_most_similar])
            ms_most_similar    = Manuscript (conn, 'id' + str (ms_id_most_similar + 1))
            d = ms_most_similar.to_json ()

            # exit if no passages could be explained
            n_explains = int (np.count_nonzero (b_explained))
            n_equal    = int (np.count_nonzero (b_explained_equal))
            if n_explains == 0:
                break
            n_explained += n_explains

            # remove "explained" readings, so they will not be matched again
            b_post[:,b_explained] = False
            b_equal[:,b_explained] = False
            explain_matrix[b_explained] = 0
            # explain_equal_matrix[b_explained] = 0

            n_unknown = np.count_nonzero (np.bitwise_and (explain_matrix, 0x1))

            d['explains']  = n_explains
            d['equal']     = n_equal
            d['post']      = n_explains - n_equal
            d['explained'] = n_explained
            d['unknown']   = n_unknown
            d['open']      = n_defined - n_explained - n_unknown
            d['n']         = n + 1
            cover.append (d)

        # output list
        response['cover'] = cover
        return make_json_response (response)


class Combination (object):
    def __init__ (self, iter):
        """ Init from an iterable of Manuscripts. """
        self.mss = list (iter)
        self.len = len (self.mss)
        self.vec = np.array ([ ms.ms_id - 1 for ms in self.mss ])
        self.n_explained_equal = 0
        self.n_explained_post  = 0
        self.n_unknown         = 0
        self.n_open            = 0
        self.hint              = False

    def score (self):
        return 10 * self.n_explained_equal + 5 * self.n_explained_post

    def explained (self):
        return self.n_explained_equal + self.n_explained_post

    def to_json (self):
        return {
            'mss'    : [ms.to_json () for ms in self.mss],
            'count'  : self.len,
            'equal'  : self.n_explained_equal,
            'post'   : self.n_explained_post,
            'unknown': self.n_unknown,
            'open'   : self.n_open,
            'hint'   : self.hint
        }


@app.endpoint ('exhaustive-search.json')
def exhaustive_search_json (hs_hsnr_id):
    """Do an exhaustive search for the combination among a given set of ancestors
    that best explains a given manuscript.

    """

    response = {}

    with current_app.config.dba.engine.begin () as conn:
        if current_app.config.val is None:
            current_app.config.val = init (current_app.config.dba)
        val = current_app.config.val

        cover = []

        ms = Manuscript (conn, hs_hsnr_id) # the manuscript to explain
        response['ms'] = ms.to_json ()
        ms_id = ms.ms_id - 1  # numpy indices start at 0

        # get the selected set of ancestors
        selected = [ Manuscript (conn, anc_id)
                     for anc_id in (request.args.get ('selection') or '').split () ]
        response['mss'] = [s.to_json () for s in selected]

        np.set_printoptions (edgeitems = 8, linewidth = 100)

        b_common = np.logical_and (val.def_matrix, val.def_matrix[ms_id])
        b_common[ms_id] = False  # don't find original ms.
        b_common[0]     = False  # don't find A
        b_common[1]     = False  # don't find MT

        # eliminate descendants from the matrix
        ancestors = get_ancestors (conn, current_app.config.set_cover_rg_id, ms.ms_id)
        for i in range (0, val.n_mss):
            if ((i + 1) not in ancestors) :
                b_common[i] = 0

        n_defined = np.count_nonzero (val.def_matrix[ms_id])
        response['ms']['open'] = n_defined

        explain_matrix = build_explain_matrix (conn, val, ms.ms_id)

        explain_equal_matrix = val.mask_matrix[ms_id]

        # The mss x passages boolean matrix that is TRUE whenever the inspected ms.
        # agrees with the potential source ms.
        b_equal = np.bitwise_and (val.mask_matrix, explain_equal_matrix) > 0
        b_equal = np.logical_and (b_equal, b_common)

        # The mss x passages boolean matrix that is TRUE whenever the inspected ms.
        # agrees with the potential source ms. or is posterior to it.
        b_post = np.bitwise_and (val.mask_matrix, explain_matrix) > 0
        b_post = np.logical_and (b_post, b_common)

        for l in range (len (selected)):
            for c in itertools.combinations (selected, l + 1):
                comb = Combination (c)

                # how many passages does this combination explain?
                b_explained_equal = np.logical_or.reduce (b_equal[comb.vec])
                b_explained_post  = np.logical_or.reduce (b_post[comb.vec])
                b_explained_post  = np.logical_and (b_explained_post, np.logical_not (b_explained_equal))

                comb.n_explained_equal = np.count_nonzero (b_explained_equal)
                comb.n_explained_post  = np.count_nonzero (b_explained_post)

                unk_matrix = np.copy (explain_matrix)
                unk_matrix[b_explained_equal] = 0
                unk_matrix[b_explained_post] = 0
                comb.n_unknown = np.count_nonzero (np.bitwise_and (unk_matrix, 0x1))

                comb.n_open = n_defined - comb.n_explained_equal - comb.n_explained_post - comb.n_unknown

                cover.append (comb)

        def key_len (c):
            return c.len

        def key_explained (c):
            return -c.explained ()

        # add the 'hint' column
        for k, g in itertools.groupby (sorted (cover, key = key_len), key = key_len):
            sorted (g, key = key_explained)[0].hint = True

        response['cover'] = [ c.to_json () for c in cover ]
        return make_json_response (response)
