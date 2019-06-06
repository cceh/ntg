# -*- encoding: utf-8 -*-

"""The API server for CBGM.  The optimal substemma and set cover module.

See: CBGM_Pres.pdf p. 490ff.

"""

import collections
import itertools

import flask
from flask import request, current_app

import numpy as np

from ntg_common.db_tools import execute
from ntg_common.cbgm_common import CBGM_Params, create_labez_matrix

from helpers import Passage, Manuscript, make_json_response, csvify


MAX_COVER_SIZE = 12


bp = flask.Blueprint ('set_cover', __name__)


def get_ancestors (conn, rg_id, ms_id):
    """ Get all ancestors of ms. """

    mode = 'sim'
    view = 'affinity_view' if mode == 'rec' else 'affinity_p_view'

    res = execute (conn, """
    SELECT aff.ms_id2 as ms_id
    FROM
      {view} aff
    WHERE aff.ms_id1 = :ms_id1 AND aff.rg_id = :rg_id
          AND aff.common > 0 AND aff.older < aff.newer
    ORDER BY affinity DESC, newer DESC, older DESC
    """, dict (ms_id1  = ms_id,
               rg_id   = rg_id,
               view    = view))

    return frozenset ([r[0] for r in res])


def powerset (iterable):
    """powerset([1,2,3]) --> () (1,) (2,) (3,) (1,2) (1,3) (2,3) (1,2,3)"""
    s = list (iterable)
    return itertools.chain.from_iterable (
        itertools.combinations (s, r) for r in range (len (s) + 1))


WITH_SELECT = """
  SELECT pass_id, labez, clique,
         (1 << (ROW_NUMBER () OVER (PARTITION BY pass_id ORDER BY labez, clique)::integer)) AS rn
  FROM cliques
  WHERE labez !~ '^z'
"""

def init (db):
    """ Do some preparative calculations and cache the results. """

    val = CBGM_Params ()

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
        create_labez_matrix (db, {}, val)

        # build a mask of all readings of all mss.
        # every labez_clique gets an id (in the range 1..63)

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
    Bit 2..64 are the bitmask of all cliques.

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
        CASE WHEN (ls.source_labez IS NULL) AND NOT ls.original THEN rn1.rn | 1 ELSE rn1.rn END AS rn1,
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
        ON (lsrn.pass_id = lsrec.pass_id AND (lsrn.rn1 & ~B'1'::integer) = lsrec.rn2)
    )
    SELECT pass_id, BIT_OR (rn1) AS rn
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
    """ Init the Flask app. """

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


@bp.route ('/set-cover.json/<hs_hsnr_id>')
def set_cover_json (hs_hsnr_id):
    """ Approximate the minimum set cover for a manuscript.

    See: https://en.wikipedia.org/wiki/Set_cover_problem
    """

    response = {}

    with current_app.config.dba.engine.begin () as conn:
        if current_app.config.val is None:
            current_app.config.val = init (current_app.config.dba)
        val = current_app.config.val

        cover = []

        ms = Manuscript (conn, hs_hsnr_id)
        response['ms'] = ms.to_json ()
        ms_id = ms.ms_id - 1  # numpy indices start at 0

        # allow user to pre-select a set of manuscripts
        pre_selected = [ Manuscript (conn, anc_id)
                         for anc_id in (request.args.get ('pre_select') or '').split () ]
        response['mss'] = [s.to_json () for s in pre_selected]

        np.set_printoptions (edgeitems = 8, linewidth = 100)

        # The mss x passages boolean matrix that is TRUE whenever the inspected
        # ms. and the source ms. are both defined.
        b_common = np.logical_and (val.def_matrix, val.def_matrix[ms_id])

        # Remove mss. we don't want to compare
        b_common[ms_id] = False  # don't find original ms.
        b_common[0]     = False  # don't find A
        b_common[1]     = False  # don't find MT
        # also eliminate all descendants
        ancestors = get_ancestors (conn, current_app.config.set_cover_rg_id, ms.ms_id)
        for i in range (0, val.n_mss):
            if (i + 1) not in ancestors:
                b_common[i] = False

        n_defined = np.count_nonzero (val.def_matrix[ms_id])
        response['ms']['open'] = n_defined

        # mask_matrix ist the mss x passages matrix containing the bitmask of
        # all readings
        explain_matrix       = build_explain_matrix (conn, val, ms.ms_id)
        explain_equal_matrix = val.mask_matrix[ms_id]

        # The mss x passages boolean matrix that is TRUE whenever the inspected ms.
        # agrees with the potential source ms.
        b_equal = np.bitwise_and (val.mask_matrix, explain_equal_matrix) > 0
        b_equal = np.logical_and (b_equal, b_common)

        # The mss x passages boolean matrix that is TRUE whenever the inspected ms.
        # agrees with the potential source ms. or is posterior to it.
        b_post = np.bitwise_and (val.mask_matrix, explain_matrix) > 0
        b_post = np.logical_and (b_post, b_common)

        # The 1 x passages boolean matrix that is TRUE whenever the passage is
        # still unexplained.
        b_open = np.copy (val.def_matrix[ms_id])

        # The 1 x passages boolean matrix that is TRUE whenever the source of
        # the reading in the inspected ms. is unknown
        b_unknown = np.bitwise_and (explain_matrix, 0x1)
        b_unknown = np.logical_and (b_unknown, b_open)

        n_explained = 0

        for n in range (0, MAX_COVER_SIZE):
            if n < len (pre_selected):
                # use manuscript pre-selected by user
                ms_id_most_similar = pre_selected[n].ms_id - 1
            else:
                # find manuscript that explains the most passages by agreement
                ms_id_most_similar = int (np.argmax (np.sum (b_equal, axis = 1)))

            ms_most_similar = Manuscript (conn, 'id' + str (ms_id_most_similar + 1))
            d = ms_most_similar.to_json ()

            b_explained = np.copy (b_post[ms_id_most_similar])
            n_explains = int (np.count_nonzero (b_explained))
            # exit if no passages could be explained
            if n_explains == 0:
                break

            n_equal = int (np.count_nonzero (b_equal[ms_id_most_similar]))

            # remove "explained" readings, so they will not be matched again
            b_post[:,b_explained] = False
            b_equal[:,b_explained] = False
            b_unknown[b_explained] = False
            b_open[b_explained]    = False

            n_explained += n_explains
            n_unknown = int (np.count_nonzero (b_unknown))
            n_open    = int (np.count_nonzero (b_open))

            d['explains']  = n_explains
            d['explained'] = n_explained
            d['equal']     = n_equal
            d['post']      = n_explains - n_equal
            d['unknown']   = n_unknown
            d['open']      = n_open - n_unknown
            d['n']         = n + 1
            cover.append (d)

        # output list
        response['cover'] = cover
        return make_json_response (response)


class Combination ():
    """ Represents a combination of manuscripts. """

    def __init__ (self, iterator, index):
        """ Init from an iterable of Manuscripts. """

        self.mss   = list (iterator)
        self.index = index
        self.len   = len (self.mss)
        self.vec   = np.array ([ ms.ms_id - 1 for ms in self.mss ])
        self.n_explained_equal = 0
        self.n_explained_post  = 0
        self.n_unknown         = 0
        self.n_open            = 0
        self.hint              = False
        self.unknown_indices   = tuple ([-1])
        self.open_indices      = tuple ([-1])


    def score (self):
        """ Calculate the score for the given combination. """

        return 10 * self.n_explained_equal + 5 * self.n_explained_post

    def explained (self):
        """ Calculate how many variants are explained by this combination. """

        return self.n_explained_equal + self.n_explained_post

    def to_json (self):
        """ Output the combination in JSON format. """

        return {
            'index'  : self.index,
            'mss'    : [ms.to_json () for ms in self.mss],
            'count'  : self.len,
            'equal'  : self.n_explained_equal,
            'post'   : self.n_explained_post,
            'unknown': self.n_unknown,
            'open'   : self.n_open,
            'hint'   : self.hint
        }

    def to_csv (self):
        """ Output the combination in CSV format. """

        return [
            ' '.join ([ms.hs for ms in self.mss]),
            self.len,
            self.n_explained_equal,
            self.n_explained_post,
            self.n_unknown,
            self.n_open,
            self.hint
        ]


def _optimal_substemma (ms_id, explain_matrix, combinations, mode):
    """Do an exhaustive search for the combination among a given set of ancestors
    that best explains a given manuscript.

    """

    ms_id = ms_id - 1  # numpy indices start at 0
    val = current_app.config.val

    b_defined = val.def_matrix[ms_id]
    # remove variants where the inspected ms is undefined
    b_common = np.logical_and (val.def_matrix, b_defined)

    explain_equal_matrix = val.mask_matrix[ms_id]

    # The mss x passages boolean matrix that is TRUE whenever the inspected ms.
    # agrees with the potential source ms.
    b_equal = np.bitwise_and (val.mask_matrix, explain_equal_matrix) > 0
    b_equal = np.logical_and (b_equal, b_common)

    # The mss x passages boolean matrix that is TRUE whenever the inspected ms.
    # agrees with the potential source ms. or is posterior to it.
    b_post = np.bitwise_and (val.mask_matrix, explain_matrix) > 0
    b_post = np.logical_and (b_post, b_common)

    for comb in combinations:
        # how many passages does this combination explain?
        # pylint: disable=no-member
        b_explained_equal = np.logical_or.reduce (b_equal[comb.vec])
        b_explained_post  = np.logical_or.reduce (b_post[comb.vec])
        b_explained_post  = np.logical_and (b_explained_post, np.logical_not (b_explained_equal))
        b_explained       = np.logical_or (b_explained_equal, b_explained_post)

        comb.n_explained_equal = np.count_nonzero (b_explained_equal)
        comb.n_explained_post  = np.count_nonzero (b_explained_post)

        unexplained_matrix = np.copy (explain_matrix)
        unexplained_matrix[np.logical_not (b_defined)] = 0
        unexplained_matrix[b_explained] = 0
        b_unknown = np.bitwise_and (unexplained_matrix, 0x1) > 0
        unexplained_matrix[b_unknown] = 0
        b_open = unexplained_matrix > 0

        comb.n_unknown = np.count_nonzero (b_unknown)
        comb.n_open = np.count_nonzero (b_open)

        if mode == 'detail':
            comb.open_indices    = tuple (int (n + 1) for n in np.nonzero (b_open)[0])
            comb.unknown_indices = tuple (int (n + 1) for n in np.nonzero (b_unknown)[0])

    if mode == 'search':
        # add the 'hint' column
        def key_len (c):
            return c.len

        def key_explained (c):
            return -c.explained ()

        for _k, g in itertools.groupby (sorted (combinations, key = key_len), key = key_len):
            sorted (g, key = key_explained)[0].hint = True


@bp.route ('/optimal-substemma.json')
def optimal_substemma_json ():
    """Normalize parameters and add some general info.
    """

    if current_app.config.val is None:
        current_app.config.val = init (current_app.config.dba)
    val = current_app.config.val

    with current_app.config.dba.engine.begin () as conn:
        # the manuscript to explain
        ms = Manuscript (conn, request.args.get ('ms'))

        # get the selected set of ancestors and build all combinations of that set
        selected = [ Manuscript (conn, anc_id)
                     for anc_id in (request.args.get ('selection') or '').split () ]
        response = {
            'ms'  : ms.to_json (),
            'mss' : [s.to_json () for s in selected],
        }
        n_defined = np.count_nonzero (val.def_matrix[ms.ms_id - 1])
        response['ms']['open'] = n_defined

        return make_json_response (response)


_OptimalSubstemmaRow = collections.namedtuple (
    'OptimalSubstemmaRow',
    'mss count equal post unknown open hint'
)

@bp.route ('/optimal-substemma.csv')
def optimal_substemma_csv ():
    """Do an exhaustive search for the combination among a given set of ancestors
    that best explains a given manuscript.

    """

    if current_app.config.val is None:
        current_app.config.val = init (current_app.config.dba)
    val = current_app.config.val

    with current_app.config.dba.engine.begin () as conn:
        # the manuscript to explain
        ms = Manuscript (conn, request.args.get ('ms'))

        # get the selected set of ancestors and build all combinations of that set
        selected = [ Manuscript (conn, anc_id)
                     for anc_id in (request.args.get ('selection') or '').split () ]
        combinations = []
        i = 0
        for l in range (len (selected)):
            for c in itertools.combinations (selected, l + 1):
                combinations.append (Combination (c, i))
                i += 1

        explain_matrix = build_explain_matrix (conn, val, ms.ms_id)
        _optimal_substemma (ms.ms_id, explain_matrix, combinations, mode = 'search')

        res = [c.to_csv () for c in combinations]

        return csvify (_OptimalSubstemmaRow._fields,
                       list (map (_OptimalSubstemmaRow._make, res)))


_OptimalSubstemmaDetailRow = collections.namedtuple (
    'OptimalSubstemmaDetailRow',
    'type pass_id begadr endadr labez_clique lesart'
)

class _OptimalSubstemmaDetailRowCalcFields (_OptimalSubstemmaDetailRow):
    __slots__ = ()

    _fields = _OptimalSubstemmaDetailRow._fields + ('pass_hr', )

    @property
    def pass_hr (self):
        """ Add a field with a human-readable passage id. """
        return Passage.static_to_hr (self.begadr, self.endadr)

    def _asdict (self):
        return collections.OrderedDict (zip (self._fields, self + (self.pass_hr, )))


@bp.route ('/optimal-substemma-detail.csv')
def optimal_substemma_detail_csv ():
    """Report details about one combination of ancestors.
    """

    if current_app.config.val is None:
        current_app.config.val = init (current_app.config.dba)
    val = current_app.config.val

    with current_app.config.dba.engine.begin () as conn:
        # the manuscript to explain
        ms = Manuscript (conn, request.args.get ('ms'))

        # get the selected set of ancestors
        selected = [ Manuscript (conn, anc_id)
                     for anc_id in (request.args.get ('selection') or '').split () ]

        combinations   = [Combination (selected, 0)]
        explain_matrix = build_explain_matrix (conn, val, ms.ms_id)
        _optimal_substemma (ms.ms_id, explain_matrix, combinations, mode = 'detail')

        res = execute (conn, """
        SELECT 'unknown' as type, p.pass_id, p.begadr, p.endadr, v.labez_clique, v.lesart
        FROM passages p
          JOIN apparatus_cliques_view v USING (pass_id)
        WHERE v.ms_id = :ms_id AND pass_id IN :unknown_pass_ids
        UNION
        SELECT 'open' as type, p.pass_id, p.begadr, p.endadr, v.labez_clique, v.lesart
        FROM passages p
          JOIN apparatus_cliques_view v USING (pass_id)
        WHERE v.ms_id = :ms_id AND pass_id IN :open_pass_ids
        """, dict (
            ms_id = ms.ms_id,
            unknown_pass_ids = combinations[0].unknown_indices or (-1, ),
            open_pass_ids    = combinations[0].open_indices    or (-1, )
        ))

        return csvify (_OptimalSubstemmaDetailRowCalcFields._fields,
                       list (map (_OptimalSubstemmaDetailRowCalcFields._make, res)))
