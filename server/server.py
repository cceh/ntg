#!/usr/bin/python3
# -*- encoding: utf-8 -*-

"""API server for CBGM."""

import argparse
import collections
import glob
import re
import os
import os.path
import urllib.parse

import flask
from flask import request, current_app
import flask_sqlalchemy
import flask_user
import flask_login
import flask_mail
import networkx as nx

from ntg_common.db_tools import execute, to_csv
from ntg_common.config import init_cmdline
from ntg_common.tools import log
from ntg_common import tools
from ntg_common import db_tools

from . import helpers
from .helpers import parameters, Passage, Manuscript, make_json_response
from . import security
from . import editor

app = flask.Blueprint ('the_app', __name__)
static_app = flask.Flask (__name__)
dba = flask_sqlalchemy.SQLAlchemy ()
security.declare_user_model (dba)
db_adapter = flask_user.SQLAlchemyAdapter (dba, security.User)
login_manager = flask_login.LoginManager ()
login_manager.anonymous_user = security.AnonymousUserMixin
user_manager = flask_user.UserManager (db_adapter)
mail = flask_mail.Mail ()

SHAPES = {
    'a' : 'ellipse',
    'b' : 'box',
    'c' : 'pentagon',
    'd' : 'hexagon',
    'e' : 'septagon',
    'f' : 'octagon',
    'g' : 'diamond',
    'h' : 'trapezium',
    'i' : 'parallelogram',
    'j' : 'house',
    'k' : 'invtrapezium',
    'l' : 'invparallelogram',
    'm' : 'invhouse',
}

def _f_map_word (t):
    """Helper function for the :func:`suggest_json` function.

    Formats the entry of the last field of the navigation gadget.
    """

    if t.kapanf != t.kapend:
        t2 = "%s-%s:%s/%s" % (t.wortanf, t.kapend, t.versend, t.wortend)
    elif t.versanf != t.versend:
        t2 = "%s-%s/%s" % (t.wortanf, t.versend, t.wortend)
    elif t.wortanf != t.wortend:
        t2 = "%s-%s" % (t.wortanf, t.wortend)
    else:
        t2 = "%s" % t.wortanf
    return [t2, t2, t.lemma]


EXCLUDE_REGEX_MAP = {
    'A'  : 'A',
    'MT' : 'MT',
    'F'  : 'F[1-9Π][0-9]*'
}
""" Regexes for the include/exclude toolbar buttons. """


def csvify (fields, rows):
    """ Send a HTTP response in CSV format. """
    return flask.Response (to_csv (fields, rows), mimetype = 'text/csv')


def get_excluded_ms_ids (conn, include):
    exclude = set (EXCLUDE_REGEX_MAP.keys ()) - set (include)
    if not exclude:
        return tuple ([-1]) # a non-existing id to avoid an SQL syntax error
    exclude = [ EXCLUDE_REGEX_MAP[x] for x in exclude]

    # get ids of nodes to exclude
    res = execute (conn, """
    SELECT ms_id
    FROM manuscripts
    WHERE hs ~ '^({exclude})$'
    ORDER BY ms_id
    """, dict (parameters, exclude = '|'.join (exclude)))

    return tuple ([ row[0] for row in res ] or [ -1 ])


@app.endpoint ('application.json')
def application_json ():
    """Endpoint.  Serve information about the application."""

    conf = current_app.config

    return make_json_response ({
        'name'  : conf['APPLICATION_NAME'],
        'root'  : conf['APPLICATION_ROOT'],
        'start' : conf['server_start_time'],
    })


@app.endpoint ('messages.json')
def messages_json ():
    """Endpoint.  Serve the flashed messages."""

    return make_json_response (flask.get_flashed_messages (with_categories = True) or [])


@app.endpoint ('user.json')
def user_json ():
    """Endpoint.  Serve information about the current user."""

    user = flask_login.current_user
    logged_in = user.is_authenticated

    return make_json_response ({
        'is_logged_in' : logged_in,
        'is_editor' :    logged_in and user.has_role ('editor'),
        'username' :     user.username if logged_in else 'anonymous',
    })


@app.endpoint ('passage.json')
def passage_json (passage_or_id = None):
    """Endpoint.  Serve information about a passage.

    Return information about a passage or navigate to it.

    :param string passage_or_id: The passage id.
    :param string siglum:        The siglum of the book to navigate to.
    :param string chapter:       The chapter to navigate to.
    :param string verse:         The verse to navigate to.
    :param string word:          The word (range) to navigate to.
    :param string button:        The button pressed.

    """

    passage_or_id = request.args.get ('pass_id') or passage_or_id or '0'

    siglum  = request.args.get ('siglum')
    chapter = request.args.get ('chapter')
    verse   = request.args.get ('verse')
    word    = request.args.get ('word')
    button  = request.args.get ('button')

    with current_app.config.dba.engine.begin () as conn:
        if siglum and chapter and verse and word and button == 'Go':
            parsed_passage = Passage.parse ("%s %s:%s/%s" % (siglum, chapter, verse, word))
            # log (logging.INFO, parsed_passage)
            passage = Passage (conn, parsed_passage)
            return make_json_response (passage.to_json ())

        if button in ('-1', '1'):
            passage = Passage (conn, passage_or_id)
            passage = Passage (conn, int (passage.pass_id) + int (button))
            return make_json_response (passage.to_json ())

        passage = Passage (conn, passage_or_id)
        return make_json_response (passage.to_json ())


@app.endpoint ('cliques.json')
def cliques_json (passage_or_id):
    """ Endpoint.  Serve all cliques found in a passage.

    :param string passage_or_id: The passage id.

    """

    with current_app.config.dba.engine.begin () as conn:
        passage = Passage (conn, passage_or_id)
        return make_json_response (passage.cliques ())


@app.endpoint ('leitzeile.json')
def leitzeile_json (passage_or_id = None):
    """Endpoint.  Serve the leitzeile for the verse containing passage_or_id. """

    with current_app.config.dba.engine.begin () as conn:
        passage = Passage (conn, passage_or_id)
        verse_start = (passage.start // 1000) * 1000
        verse_end = verse_start + 999

        res = execute (conn, """
        SELECT l.begadr, l.endadr, l.lemma, p.pass_id, p.spanned,
          EXISTS (SELECT labez from readings r
          WHERE r.pass_id = p.pass_id AND r.labez ~ '^[b-y]' AND r.lesart != '') AS replaced
        FROM nestle l
          LEFT JOIN passages p ON (p.passage @> l.passage)
        WHERE int4range (:start, :end + 1) @> l.passage

        UNION -- get the insertions

        SELECT p.begadr, p.endadr, p.lemma, p.pass_id, p.spanned,
          EXISTS (SELECT labez from readings r
          WHERE r.pass_id = p.pass_id AND r.labez ~ '^[b-y]' AND r.lesart != '') AS replaced
        FROM passages_view_lemma p
        WHERE int4range (:start, :end + 1) @> p.passage AND (begadr % 2) = 1

        ORDER BY begadr, endadr DESC
        """, dict (parameters, start = verse_start, end = verse_end))

        Leitzeile = collections.namedtuple (
            'Leitzeile', 'begadr, endadr, lemma, pass_id, spanned, replaced')
        leitzeile = [ Leitzeile._make (r)._asdict () for r in res ]

        return make_json_response (leitzeile)


@app.endpoint ('suggest.json')
def suggest_json ():
    """Endpoint.  The suggestion drop-downs in the navigator.

    Serves a list of books, chapters, verses, or words that the user can enter
    in the navigation gadget.  It suggests only entities that are actually in
    the database.

    """

    # the name of the current field
    field   = request.args.get ('currentfield')

    # the term the user entered in the current field
    term    = request.args.get ('term') or ''
    term    = '^' + re.escape (term.split ('-')[0])

    # terms entered in previous fields
    siglum  = request.args.get ('siglum')  or 'Act'
    chapter = request.args.get ('chapter') or 'All'
    verse   = request.args.get ('verse')   or '1'

    Words = collections.namedtuple (
        'Words', 'kapanf, versanf, wortanf, kapend, versend, wortend, lemma')

    res = []
    with current_app.config.dba.engine.begin () as conn:

        if field == 'siglum':
            # only show those books that actually are in the database
            res = execute (conn, """
            SELECT DISTINCT siglum, siglum, book, bk_id
            FROM passages_view b
            WHERE siglum ~ :term OR book ~ :term
            ORDER BY bk_id
            """, dict (parameters, term = term))
            return flask.json.jsonify (
                [ { 'value' : r[0], 'label' : r[1], 'description' : r[2] } for r in res ])

        if field == 'chapter':
            res = execute (conn, """
            SELECT range, range
            FROM ranges_view
            WHERE siglum = :siglum AND range ~ '[1-9][0-9]*' AND range ~ :term
            ORDER BY range::integer
            """, dict (parameters, siglum = siglum, term = term))
            return flask.json.jsonify ([ { 'value' : r[0], 'label' : r[1] } for r in res ])

        if field == 'verse':
            res = execute (conn, """
            SELECT DISTINCT verse, verse
            FROM passages_view
            WHERE variant AND siglum = :siglum AND chapter = :chapter AND verse::varchar ~ :term
            ORDER BY verse
            """, dict (parameters, siglum = siglum, chapter = chapter, term = term))
            return flask.json.jsonify ([ { 'value' : r[0], 'label' : r[1] } for r in res ])

        if field == 'word':
            res = execute (conn, """
            SELECT chapter, verse, word,
                            adr2chapter (p.endadr), adr2verse (p.endadr), adr2word (p.endadr),
                            COALESCE (string_agg (n.lemma, ' ' ORDER BY n.begadr), '') as lemma
            FROM passages_view p
            LEFT JOIN nestle n
              ON (p.passage @> n.passage)
            WHERE variant AND siglum = :siglum AND chapter = :chapter AND verse = :verse AND word::varchar ~ :term
            GROUP BY chapter, verse, word, p.endadr
            ORDER BY word, adr2verse (p.endadr), adr2word (p.endadr)
            """, dict (parameters, siglum = siglum, chapter = chapter, verse = verse, term = term))
            res = map (Words._make, res)
            res = map (_f_map_word, res)
            return flask.json.jsonify (
                [ { 'value' : r[0], 'label' : r[1], 'description' : r[2] } for r in res ])

    return flask.json.jsonify ([])


@app.endpoint ('ranges.json')
def ranges_json (passage_or_id):
    """Endpoint.  Serve a list of ranges.

    Serves a list of the configured ranges that are contained inside a book in
    the NT.

    :param string passage_or_id: The passage id.
    :param integer bk_id:        The id of the book.

    """

    passage_or_id = request.args.get ('pass_id') or passage_or_id or '0'

    with current_app.config.dba.engine.begin () as conn:
        passage = Passage (conn, passage_or_id)
        bk_id   = request.args.get ('bk_id') or passage.bk_id

        res = execute (conn, """
        SELECT DISTINCT range, range, lower (ch.passage) as begadr, upper (ch.passage) as endadr
        FROM ranges ch
        WHERE bk_id = :bk_id
        ORDER BY begadr, endadr DESC
        """, dict (parameters, bk_id = bk_id))

        Ranges = collections.namedtuple ('Ranges', 'range, value, begadr, endadr')
        # ranges = list (map (Ranges._make, res))
        ranges = [ Ranges._make (r)._asdict () for r in res ]

        return make_json_response (ranges)


@app.endpoint ('manuscript.json')
def manuscript_json (hs_hsnr_id):
    """Endpoint.  Serve information about a manuscript.

    :param string hs_hsnr_id: The hs, hsnr or id of the manuscript.

    """

    hs_hsnr_id = request.args.get ('ms_id') or hs_hsnr_id

    with current_app.config.dba.engine.begin () as conn:
        ms = Manuscript (conn, hs_hsnr_id)
        return make_json_response (ms.to_json ())


@app.endpoint ('manuscript-full.json')
def manuscript_full_json (hs_hsnr_id, passage_or_id):
    """Endpoint.  Serve information about a manuscript.

    :param string hs_hsnr_id: The hs, hsnr or id of the manuscript.

    """

    hs_hsnr_id = request.args.get ('ms_id') or hs_hsnr_id
    chapter    = request.args.get ('range') or 'All'

    with current_app.config.dba.engine.begin () as conn:
        passage   = Passage (conn, passage_or_id)
        ms        = Manuscript (conn, hs_hsnr_id)
        rg_id     = passage.range_id (chapter)

        json = ms.to_json ()
        json['length'] = ms.get_length (passage, chapter)

        # Get the attestation(s) of the manuscript (may be uncertain eg. a/b/c)
        res = execute (conn, """
        SELECT labez, clique, labez_clique
        FROM apparatus_view_agg
        WHERE ms_id = :ms_id AND pass_id = :pass_id
        """, dict (parameters, ms_id = ms.ms_id, pass_id = passage.pass_id))
        json['labez'], json['clique'], json['labez_clique'] = res.fetchone ()

        # Get the affinity of the manuscript to all manuscripts
        res = execute (conn, """
        SELECT avg (a.affinity) as aa,
        percentile_cont(0.5) WITHIN GROUP (ORDER BY a.affinity) as ma
        FROM affinity a
        WHERE a.ms_id1 = :ms_id1 AND a.rg_id = :rg_id
        """, dict (parameters, ms_id1 = ms.ms_id, rg_id = rg_id))
        json['aa'], json['ma'] = res.fetchone ()

        # Get the affinity of the manuscript to MT
        #
        # For a description of mt and mtp see the comment in
        # ActsMsListValPh3.pl and
        # http://intf.uni-muenster.de/cbgm/actsPh3/guide_en.html#Ancestors

        json['mt'], json['mtp'] = 0.0, 0.0
        res = execute (conn, """
        SELECT a.affinity as mt, a.equal::float / c.length as mtp
        FROM affinity a
        JOIN ms_ranges c
          ON (a.ms_id1, a.rg_id) = (c.ms_id, c.rg_id)
        WHERE a.ms_id1 = :ms_id1 AND a.ms_id2 = 2 AND a.rg_id = :rg_id
        """, dict (parameters, ms_id1 = ms.ms_id, rg_id = rg_id))
        if res.rowcount > 0:
            json['mt'], json['mtp'] = res.fetchone ()

        return make_json_response (json)


@app.endpoint ('relatives.csv')
def relatives_csv (hs_hsnr_id, passage_or_id):
    """Output a table of the nearest relatives of a manuscript.

    Output a table of the nearest relatives/ancestors/descendants of a
    manuscript and what they attest.

    """

    type_     = request.args.get ('type') or 'rel'
    chapter   = request.args.get ('range') or 'All'
    limit     = int (request.args.get ('limit') or 10)
    labez     = request.args.get ('labez') or 'all'
    mode      = request.args.get ('mode') or 'sim'
    include   = request.args.getlist ('include[]') or []
    fragments = request.args.getlist ('fragments[]') or []

    view = 'affinity_view' if mode == 'rec' else 'affinity_p_view'

    where = ''
    if type_ == 'anc':
        where =  ' AND older < newer'
    if type_ == 'des':
        where =  ' AND older >= newer'

    if labez == 'all':
        where += " AND labez !~ '^z'"
    elif labez == 'all+lac':
        pass
    else:
        where += " AND labez = '%s'" % labez

    if 'fragments' in fragments:
        frag_where = ''
    else:
        frag_where = 'AND aff.common > aff.ms1_length / 2'

    limit = '' if limit == 0 else ' LIMIT %d' % limit

    with current_app.config.dba.engine.begin () as conn:

        passage   = Passage (conn, passage_or_id)
        ms        = Manuscript (conn, hs_hsnr_id)
        rg_id     = passage.range_id (chapter)

        exclude = get_excluded_ms_ids (conn, include)

        # Get the X most similar manuscripts and their attestations
        res = execute (conn, """
        /* get the LIMIT closest ancestors for this node */
        WITH ranks AS (
          SELECT ms_id1, ms_id2,
            rank () OVER (ORDER BY affinity DESC, common, older, newer DESC, ms_id2) AS rank,
            affinity
          FROM {view} aff
          WHERE ms_id1 = :ms_id1 AND aff.rg_id = :rg_id AND ms_id2 NOT IN :exclude
            AND newer > older {frag_where}
          ORDER BY affinity DESC
        )

        SELECT r.rank,
               aff.ms_id2 as ms_id,
               ms.hs,
               ms.hsnr,
               aff.ms2_length,
               aff.common,
               aff.equal,
               aff.older,
               aff.newer,
               aff.unclear,
               aff.common - aff.equal - aff.older - aff.newer - aff.unclear as norel,
               CASE WHEN aff.newer < aff.older THEN ''
                    WHEN aff.newer = aff.older THEN '-'
                    ELSE '>'
               END as direction,
               aff.affinity,
               a.labez
        FROM
          {view} aff
        JOIN apparatus_view_agg a
          ON aff.ms_id2 = a.ms_id
        JOIN manuscripts ms
          ON aff.ms_id2 = ms.ms_id
        LEFT JOIN ranks r
          ON r.ms_id2 = aff.ms_id2
        WHERE aff.ms_id2 NOT IN :exclude AND aff.ms_id1 = :ms_id1
              AND aff.rg_id = :rg_id AND aff.common > 0
              AND a.pass_id = :pass_id {where} {frag_where}
        ORDER BY affinity DESC, r.rank, newer DESC, older DESC, hsnr
        {limit}
        """, dict (parameters, where = where, frag_where = frag_where,
                   ms_id1 = ms.ms_id, hsnr = ms.hsnr,
                   pass_id = passage.pass_id, rg_id = rg_id, limit = limit,
                   view = view, exclude = exclude))

        Relatives = collections.namedtuple (
            'Relatives',
            'rank ms_id hs hsnr length common equal older newer unclear norel direction affinity labez'
        )
        return csvify (Relatives._fields, list (map (Relatives._make, res)))


@app.endpoint ('ms_attesting')
def ms_attesting (passage_or_id, labez):
    """ Serve all relatives of all mss. attesting labez at passage. """

    with current_app.config.dba.engine.begin () as conn:
        passage = Passage (conn, passage_or_id)

        res = execute (conn, """
        SELECT hsnr
        FROM apparatus_view
        WHERE pass_id = :pass_id AND labez = :labez
        ORDER BY hsnr
        """, dict (parameters, pass_id = passage.pass_id, labez = labez))

        Attesting = collections.namedtuple ('Attesting', 'hsnr')
        attesting = list (map (Attesting._make, res))

        # convert tuples to lists
        return flask.render_template ("ms_attesting.html",
                                      passage = passage, labez = labez, rows = attesting)


def remove_z_leaves (graph):
    """ Removes leaves (recursively) if they read z. """

    # We cannot use DFS because we don't know the root.
    for n in reversed (list (nx.topological_sort (graph))):
        atts = graph.node[n]
        if graph.out_degree (n) == 0 and 'labez' in atts and atts['labez'][0] == 'z':
            graph.remove_node (n)


def textflow (passage_or_id):
    """ Output a stemma of manuscripts. """

    labez        = request.args.get ('labez') or ''
    hyp_a        = request.args.get ('hyp_a') or 'A'
    chapter      = request.args.get ('range') or 'All'
    connectivity = int (request.args.get ('connectivity') or 10)
    width        = float (request.args.get ('width') or 0.0)
    fontsize     = float (request.args.get ('fontsize') or 10.0)
    mode         = request.args.get ('mode') or 'sim'

    include      = request.args.getlist ('include[]')   or []
    fragments    = request.args.getlist ('fragments[]') or []
    var_only     = request.args.getlist ('var_only[]')  or []
    cliques      = request.args.getlist ('cliques[]')   or []

    fragments = 'fragments' in fragments
    var_only  = 'var_only'  in var_only
    cliques   = 'cliques'   in cliques
    leaf_z    = 'Z'         in include    # show leaf z nodes in global textflow?

    view = 'affinity_view' if mode == 'rec' else 'affinity_p_view'

    global_textflow = not ((labez != '') or var_only)
    rank_z = False  # include z nodes in ranking?

    if global_textflow:
        connectivity = 1
        rank_z = True
    if connectivity == 21:
        connectivity = 9999

    labez_where = ''
    frag_where = ''
    z_where = ''

    if labez != '':
        labez_where = 'AND app.cbgm AND app.labez = :labez'
        if hyp_a != 'A':
            labez_where = 'AND app.cbgm AND (app.labez = :labez OR (app.ms_id = 1 AND :hyp_a = :labez))'

    if not fragments:
        frag_where = 'AND a.common > a.ms1_length / 2'

    if not rank_z:
        z_where = "AND app.labez !~ '^z' AND app.certainty = 1.0"

    group_field = 'labez_clique' if cliques else 'labez'

    with current_app.config.dba.engine.begin () as conn:
        passage = Passage (conn, passage_or_id)

        if chapter == 'This':
            chapter = passage.chapter

        # get rg_id
        res = execute (conn, """
        SELECT rg_id
        FROM ranges
        WHERE range = :range_ AND bk_id = :bk_id
        """, dict (parameters, bk_id = passage.bk_id, range_ = chapter))
        rg_id, = res.fetchone ()

        exclude = get_excluded_ms_ids (conn, include)

        # nodes query
        #
        # get all nodes or all nodes (hypothetically) attesting labez

        res = execute (conn, """
        SELECT ms_id
        FROM apparatus app
        WHERE pass_id = :pass_id AND ms_id NOT IN :exclude {labez_where} {z_where}
        """, dict (parameters, exclude = exclude,
                   pass_id = passage.pass_id, labez = labez,
                   hyp_a = hyp_a, labez_where = labez_where, z_where = z_where))

        nodes = tuple ([ row[0] for row in res ] or [ -1 ]) # avoid SQL syntax error

        # rank query
        #
        # query to get the closest ancestors for every node with rank <= connectivity

        query = """
        SELECT ms_id1, ms_id2, rank
        FROM (
          SELECT ms_id1, ms_id2, rank () OVER (PARTITION BY ms_id1
             ORDER BY affinity DESC, common, older, newer DESC, ms_id2) AS rank
          FROM {view} a
          WHERE ms_id1 IN :nodes AND a.rg_id = :rg_id AND ms_id2 NOT IN :exclude
            AND newer > older {frag_where}
        ) AS r
        WHERE rank <= :connectivity
        ORDER BY rank
        """

        res = execute (conn, query,
                       dict (parameters, nodes = tuple (nodes), exclude = exclude,
                             rg_id = rg_id, pass_id = passage.pass_id, view = view,
                             labez = labez, connectivity = connectivity,
                             frag_where = frag_where, hyp_a = hyp_a))

        Ranks = collections.namedtuple ('Ranks', 'ms_id1 ms_id2 rank')
        ranks = list (map (Ranks._make, res))

        # Initially build an unconnected graph with one node for each
        # manuscript.  We will connect the nodes later.  Finally we will remove
        # unconnected nodes.

        graph = nx.DiGraph ()

        dest_nodes = { r.ms_id1 for r in ranks }
        src_nodes  = { r.ms_id2 for r in ranks }

        res = execute (conn, """
        SELECT ms.ms_id, ms.hs, ms.hsnr, a.labez, a.clique, a.labez_clique
        FROM apparatus_view_agg a
        JOIN manuscripts ms USING (ms_id)
        WHERE pass_id = :pass_id AND ms_id IN :ms_ids
        """, dict (parameters, ms_ids = tuple (src_nodes | dest_nodes), pass_id = passage.pass_id))

        Mss = collections.namedtuple ('Mss', 'ms_id hs hsnr labez clique labez_clique')
        mss = list (map (Mss._make, res))

        for ms in mss:
            attrs = {}
            attrs['hs']           = ms.hs
            attrs['hsnr']         = ms.hsnr
            attrs['labez']        = ms.labez
            attrs['clique']       = ms.clique
            attrs['labez_clique'] = ms.labez_clique
            attrs['ms_id']        = ms.ms_id
            attrs['label']        = ms.hs
            attrs['clickable']    = '1'
            if ms.ms_id == 1 and hyp_a != 'A':
                attrs['labez']        = hyp_a[0]
                attrs['clique']       = ''
                attrs['labez_clique'] = hyp_a[0]
            # FIXME: attrs['shape'] = SHAPES.get (attrs['labez'], SHAPES['a'])
            graph.add_node (ms.ms_id, **attrs)

        # Connect the nodes
        #
        # Step 1: A node that has ancestors within the same attestation keeps
        # the top-ranked one of those as the only parent.
        #
        # Step 2: A node without ancestors from step 1 keeps as parents the
        # top-ranked parent for each other attestation.
        #
        # Assumption: ranks are sorted top-ranked first

        def is_z_node (n):
            labez = n['labez']
            return (labez[0] == 'z') or ('/' in labez)

        tags = set ()
        for step in (1, 2):
            for r in ranks:
                a1 = graph.node[r.ms_id1]
                a2 = graph.node[r.ms_id2]
                if not (global_textflow) and is_z_node (a2):
                    # disregard lacunae
                    continue
                if step == 1 and a1[group_field] != a2[group_field]:
                    # differing attestations are handled in step 2
                    continue
                if r.ms_id1 in tags:
                    # an ancestor of this node that lays within the node's
                    # attestation was already seen.  we need not look into other
                    # attestations
                    continue
                if str (r.ms_id1) + a2[group_field] in tags:
                    # an ancestor of this node that lays within this attestation
                    # was already seen.  we need not look into further nodes
                    continue
                # add a new parent
                if r.rank > 1:
                    graph.add_edge (r.ms_id2, r.ms_id1, rank = r.rank, headlabel = r.rank)
                else:
                    graph.add_edge (r.ms_id2, r.ms_id1)

                if a1[group_field] == a2[group_field]:
                    # tag: has ancestor node within the same attestation
                    tags.add (r.ms_id1)
                else:
                    # tag: has ancestor node with this other attestation
                    tags.add (str (r.ms_id1) + a2[group_field])

        if not leaf_z:
            remove_z_leaves (graph)

        graph.remove_nodes_from (list (nx.isolates (graph)))

        if var_only:
            # if one predecessor is within the same attestation then remove all
            # other predecessors that are not within the same attestation
            for n in graph:
                within = False
                attestation_n = graph.node[n][group_field]
                for p in graph.predecessors (n):
                    if graph.node[p][group_field] == attestation_n:
                        within = True
                        break
                if within:
                    for p in graph.predecessors (n):
                        if graph.node[p][group_field] != attestation_n:
                            graph.remove_edge (p, n)

            # remove edges between nodes within the same attestation
            for u, v in list (graph.edges ()):
                if graph.node[u][group_field] == graph.node[v][group_field]:
                    graph.remove_edge (u, v)

            # remove now isolated nodes
            graph.remove_nodes_from (list (nx.isolates (graph)))

            # unconstrain backward edges
            for u, v in graph.edges ():
                if graph.node[u][group_field] > graph.node[v][group_field]:
                    graph.adj[u][v]['constraint'] = 'false'

        else:
            for n in graph:
                # Use a different label if the parent's labez_clique differs from this
                # node's labez_clique.
                pred = list (graph.predecessors (n))
                attrs = graph.node[n]
                if not pred:
                    attrs['label'] = "%s: %s" % (attrs['labez_clique'], attrs['hs'])
                for p in pred:
                    if attrs['labez_clique'] != graph.node[p]['labez_clique']:
                        attrs['label'] = "%s: %s" % (attrs['labez_clique'], attrs['hs'])
                        graph.adj[p][n]['style'] = 'dashed'

    if var_only:
        dot = helpers.nx_to_dot_subgraphs (graph, group_field, width, fontsize)
    else:
        dot = helpers.nx_to_dot (graph, width, fontsize)
    return dot


@app.endpoint ('textflow.dot')
def textflow_dot (passage_or_id):
    """ Return a textflow diagram in .dot format. """

    dot = textflow (passage_or_id)
    dot = tools.graphviz_layout (dot)
    return flask.Response (dot, mimetype = 'text/vnd.graphviz')


@app.endpoint ('textflow.png')
def textflow_png (passage_or_id):
    """ Return a textflow diagram in .png format. """

    dot = textflow (passage_or_id)
    png = tools.graphviz_layout (dot, format = 'png')
    return flask.Response (png, mimetype = 'image/png')


_ComparisonRow = collections.namedtuple (
    'ComparisonRow',
    'rg_id, range, common, equal, older, newer, unclear, affinity, rank, length1, length2'
)


class _ComparisonRowCalcFields (_ComparisonRow):
    __slots__ = ()

    _fields = _ComparisonRow._fields + ('norel', )

    @property
    def norel (self):
        return self.common - self.equal - self.older - self.newer - self.unclear

    def _asdict (self):
        return collections.OrderedDict (zip (self._fields, self + (self.norel, )))


def comparison_summary ():
    """Output comparison of 2 witnesses, chapter summary.

    Outputs a summary of the differences between 2 manuscripts, one summary row
    per chapters.

    """

    with current_app.config.dba.engine.begin () as conn:
        ms1 = Manuscript (conn, request.args.get ('ms1') or 'A')
        ms2 = Manuscript (conn, request.args.get ('ms2') or 'A')

        res = execute (conn, """
        (WITH ranks AS (
          SELECT ms_id1, ms_id2, rg_id, rank () OVER (PARTITION BY rg_id ORDER BY affinity DESC) AS rank, affinity
          FROM affinity aff
          WHERE ms_id1 = :ms_id1
            AND {prefix}newer > {prefix}older
          ORDER BY affinity DESC
        )

        SELECT a.rg_id, a.range, a.common, a.equal,
               a.older, a.newer, a.unclear, a.affinity, r.rank, ms1_length, ms2_length
        FROM {view} a
        JOIN ranks r     USING (rg_id, ms_id1, ms_id2)
        WHERE a.ms_id1 = :ms_id1 AND a.ms_id2 = :ms_id2
        )

        UNION

        (WITH ranks2 AS (
          SELECT ms_id1, ms_id2, rg_id, rank () OVER (PARTITION BY rg_id ORDER BY affinity DESC) AS rank, affinity
          FROM affinity aff
          WHERE ms_id2 = :ms_id2
            AND {prefix}newer < {prefix}older
          ORDER BY affinity DESC
        )

        SELECT a.rg_id, a.range, a.common, a.equal,
               a.older, a.newer, a.unclear, a.affinity, r.rank, ms1_length, ms2_length
        FROM {view} a
        JOIN ranks2 r USING (rg_id, ms_id1, ms_id2)
        WHERE a.ms_id1 = :ms_id1 AND a.ms_id2 = :ms_id2
        )

        UNION

        SELECT a.rg_id, a.range, a.common, a.equal,
               a.older, a.newer, a.unclear, a.affinity, NULL, ms1_length, ms2_length
        FROM {view} a
        WHERE a.ms_id1 = :ms_id1 AND a.ms_id2 = :ms_id2 AND a.newer = a.older

        ORDER BY rg_id
        """, dict (parameters, ms_id1 = ms1.ms_id, ms_id2 = ms2.ms_id,
                   view = 'affinity_p_view', prefix = 'p_'))

        return list (map (_ComparisonRowCalcFields._make, res))


_ComparisonDetailRow = collections.namedtuple (
    'ComparisonDetailRow',
    'pass_id begadr endadr labez_clique1 lesart1 labez_clique2 lesart2 older newer unclear'
)

class _ComparisonDetailRowCalcFields (_ComparisonDetailRow):
    __slots__ = ()

    _fields = _ComparisonDetailRow._fields + ('pass_hr', 'norel')

    @property
    def pass_hr (self):
        return Passage.static_to_hr (self.begadr, self.endadr)

    @property
    def norel (self):
        return not (self.older or self.newer or self.unclear)

    def _asdict (self):
        return collections.OrderedDict (zip (self._fields, self + (self.pass_hr, self.norel)))


def comparison_detail ():
    """Output comparison of 2 witnesses, chapter detail.

    Outputs a detail of the differences between 2 manuscripts in one chapter.
    """

    with current_app.config.dba.engine.begin () as conn:
        ms1 = Manuscript (conn, request.args.get ('ms1') or 'A')
        ms2 = Manuscript (conn, request.args.get ('ms2') or 'A')
        range_ = request.args.get ('range') or 'All'

        res = execute (conn, """
        SELECT p.pass_id, p.begadr, p.endadr, v1.labez_clique, v1.lesart,
                                              v2.labez_clique, v2.lesart,
          is_p_older (p.pass_id, v1.labez, v1.clique, v2.labez, v2.clique) AS older,
          is_p_older (p.pass_id, v2.labez, v2.clique, v1.labez, v1.clique) AS newer,
          is_p_unclear (p.pass_id, v1.labez, v1.clique) OR
          is_p_unclear (p.pass_id, v2.labez, v2.clique) AS unclear
        FROM (SELECT * FROM ranges WHERE range = :range_) r
          JOIN passages p ON (r.passage @> p.passage )
          JOIN apparatus_cliques_view v1 USING (pass_id)
          JOIN apparatus_cliques_view v2 USING (pass_id)
        WHERE v1.ms_id = :ms1 AND v2.ms_id = :ms2
          AND v1.labez != v2.labez AND v1.labez !~ '^z' AND v2.labez !~ '^z'
          AND v1.cbgm AND v2.cbgm
        ORDER BY p.pass_id
        """, dict (parameters, ms1 = ms1.ms_id, ms2 = ms2.ms_id, range_ = range_))

        return list (map (_ComparisonDetailRowCalcFields._make, res))


@app.endpoint ('comparison-summary.csv')
def comparison_summary_csv ():
    """Endpoint. Serve a CSV table. (see also :func:`comparison_summary`)"""

    return csvify (_ComparisonRowCalcFields._fields, comparison_summary ())


@app.endpoint ('comparison-detail.csv')
def comparison_detail_csv ():
    """Endpoint. Serve a CSV table. (see also :func:`comparison_detail`)"""

    return csvify (_ComparisonDetailRowCalcFields._fields, comparison_detail ())


@app.endpoint ('apparatus.json')
def apparatus_json (passage_or_id):
    """ The contents of the apparatus table. """

    with current_app.config.dba.engine.begin () as conn:
        passage = Passage (conn, passage_or_id)

        # list of labez => lesart
        res = execute (conn, """
        SELECT labez, reading (labez, lesart)
        FROM readings
        WHERE pass_id = :pass_id
        ORDER BY labez
        """, dict (parameters, pass_id = passage.pass_id))

        Readings = collections.namedtuple ('Readings', 'labez lesart')
        readings = [ Readings._make (r)._asdict () for r in res ]

        # list of labez_clique => manuscripts
        res = execute (conn, """
        SELECT labez, clique, labez_clique, labezsuf, reading (labez, lesart), ms_id, hs, hsnr, certainty
        FROM apparatus_cliques_view
        WHERE pass_id = :pass_id
        ORDER BY hsnr, labez, clique
        """, dict (parameters, pass_id = passage.pass_id))

        Manuscripts = collections.namedtuple (
            'Manuscripts',
            'labez clique labez_clique labezsuf lesart ms_id hs hsnr certainty'
        )
        manuscripts = [ Manuscripts._make (r)._asdict () for r in res ]

        return make_json_response ({
            'readings'    : readings,
            'manuscripts' : manuscripts,
        })

    return 'Error'


@app.endpoint ('attestation.json')
def attestation_json (passage_or_id):

    with current_app.config.dba.engine.begin () as conn:
        passage = Passage (conn, passage_or_id)

        res = execute (conn, """
        SELECT ms_id, labez
        FROM apparatus
        WHERE pass_id = :pass_id
        ORDER BY ms_id
        """, dict (parameters, pass_id = passage.pass_id))

        attestations = {}
        for row in res:
            ms_id, labez = row
            attestations[str (ms_id)] = labez

        return make_json_response ({
            'attestations': attestations
        })


def stemma (passage_or_id):
    """Serve a local stemma in dot format.

    A local stemma is a DAG (directed acyclic graph).  The layout of the DAG is
    precomputed on the server using GraphViz.  GraphViz adds a precomputed
    position to each node and a precomputed bezier path to each edge.

    N.B. I also considered client-side layout of DAGs, but found only 2 viable
    libraries:

    - dagre.  Javascript clone of GraphViz.  Unmaintained.  Buggy.  Does not
      work well with require.js.

    - viz.js.  GraphViz cross-compiled to Javascript with Emscripten.  Huge.
      Promising but still early days.

    Both libraries have their drawbacks so the easiest way out was to precompute
    the layout on the server.

    """

    width    = float (request.args.get ('width') or 0.0)
    fontsize = float (request.args.get ('fontsize') or 10.0)

    with current_app.config.dba.engine.begin () as conn:
        passage = Passage (conn, passage_or_id)
        graph = db_tools.local_stemma_to_nx (
            conn, passage.pass_id, flask_login.current_user.has_role ('editor')
        )
        dot = helpers.nx_to_dot (graph, width, fontsize, nodesep = 0.2)
        return dot


@app.endpoint ('stemma.dot')
def stemma_dot (passage_or_id):
    """ Return a local stemma diagram in .dot format. """

    dot = stemma (passage_or_id)
    dot = tools.graphviz_layout (dot)
    return flask.Response (dot, mimetype = 'text/vnd.graphviz')


@app.endpoint ('stemma.png')
def stemma_png (passage_or_id):
    """ Return a local stemma diagram in .png format. """

    dot = stemma (passage_or_id)
    png = tools.graphviz_layout (dot, format = 'png')
    return flask.Response (png, mimetype = 'image/png')


def make_safe_url (url):
    """Turns an usafe absolute URL into a safe relative URL
    by removing the scheme and the hostname

    Example: make_safe_url('http://hostname/path1/path2?q1=v1&q2=v2#fragment')
             returns: '/path1/path2?q1=v1&q2=v2#fragment

    Copied from flask_user/views.py because it was defective.
    """
    parts = urllib.parse.urlsplit (url)
    return urllib.parse.urlunsplit ( ('', '', parts[2], parts[3], parts[4]) )


def build_parser ():
    """ Build the commandlien parser. """

    parser = argparse.ArgumentParser (description = __doc__)
    config_path = os.path.abspath (os.path.dirname (__file__) + '/instance')

    parser.add_argument (
        '-v', '--verbose', dest='verbose', action='count',
        help='increase output verbosity', default=0
    )
    parser.add_argument (
        '-c', '--config-path', dest='config_path',
        default=config_path, metavar='CONFIG_PATH',
        help="the directory where the config files reside (default='./instance/')"
    )
    return parser


if __name__ == "__main__":
    from werkzeug.routing import Map, Rule
    from werkzeug.wsgi import DispatcherMiddleware
    from werkzeug.serving import run_simple
    import logging

    args, dummy = init_cmdline (build_parser ())

    instances = collections.OrderedDict ()

    static_app.config.from_pyfile (args.config_path.rstrip ('/') + '/_global.conf')
    static_app.config['server_start_time'] = str (int (args.start_time.timestamp ()))
    static_app.url_map.add (Rule ('/', endpoint = 'index'))

    static_app.config.dba = db_tools.PostgreSQLEngine (**static_app.config)
    static_app.config['SQLALCHEMY_DATABASE_URI'] = static_app.config.dba.url
    static_app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    dba.init_app (static_app)
    mail.init_app (static_app)
    user_manager.init_app (static_app, login_manager = login_manager,
                           make_safe_url_function = make_safe_url)

    for fn in glob.glob (args.config_path.rstrip ('/') + '/*.conf'):
        if fn.endswith ('/_global.conf'):
            continue
        sub_app = flask.Flask (__name__)
        sub_app.logger.setLevel (args.log_level)
        sub_app.config.from_pyfile (args.config_path.rstrip ('/') + '/_global.conf')
        sub_app.config.from_pyfile (fn)
        sub_app.config['server_start_time'] = str (int (args.start_time.timestamp ()))

        sub_app.register_blueprint (app)
        sub_app.register_blueprint (editor.app)

        sub_app.url_map = Map ([
            Rule ('/comparison-summary.csv',                      endpoint = 'comparison-summary.csv'),
            Rule ('/comparison-detail.csv',                       endpoint = 'comparison-detail.csv'),
            Rule ('/suggest.json',                                endpoint = 'suggest.json'),
            Rule ('/application.json',                            endpoint = 'application.json'),
            Rule ('/user.json',                                   endpoint = 'user.json'),
            Rule ('/messages.json',                               endpoint = 'messages.json'),
            Rule ('/leitzeile.json/<passage_or_id>',              endpoint = 'leitzeile.json'),
            Rule ('/manuscript.json/<hs_hsnr_id>',                endpoint = 'manuscript.json'),
            Rule ('/manuscript-full.json/<passage_or_id>/<hs_hsnr_id>', endpoint = 'manuscript-full.json'),
            Rule ('/relatives.csv/<passage_or_id>/<hs_hsnr_id>',  endpoint = 'relatives.csv'),
            Rule ('/passage.json/',                               endpoint = 'passage.json'),
            Rule ('/passage.json/<passage_or_id>',                endpoint = 'passage.json'),
            Rule ('/cliques.json/<passage_or_id>',                endpoint = 'cliques.json'),
            Rule ('/ranges.json/<passage_or_id>',                 endpoint = 'ranges.json'),
            Rule ('/ms_attesting/<passage_or_id>/<labez>',        endpoint = 'ms_attesting'),
            Rule ('/apparatus.json/<passage_or_id>',              endpoint = 'apparatus.json'),
            Rule ('/attestation.json/<passage_or_id>',            endpoint = 'attestation.json'),
            Rule ('/stemma.dot/<passage_or_id>',                  endpoint = 'stemma.dot'),
            Rule ('/stemma.png/<passage_or_id>',                  endpoint = 'stemma.png'),
            Rule ('/textflow.dot/<passage_or_id>',                endpoint = 'textflow.dot'),
            Rule ('/textflow.png/<passage_or_id>',                endpoint = 'textflow.png'),
            Rule ('/notes.txt/<passage_or_id>',                   endpoint = 'notes.txt', methods = ['GET', 'PUT']),
            Rule ('/stemma-edit/<passage_or_id>',                 endpoint = 'stemma-edit', methods = ['POST']),
        ])

        log (logging.INFO, "{name} at {path} from conf {conf}".format (
            name = sub_app.config['APPLICATION_NAME'],
            path = sub_app.config['APPLICATION_ROOT'],
            conf = fn))

        sub_app.config.dba = db_tools.PostgreSQLEngine (**sub_app.config)
        sub_app.config['SQLALCHEMY_DATABASE_URI'] = static_app.config.dba.url
        sub_app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        dba.init_app (sub_app)
        mail.init_app (sub_app)
        user_manager.init_app (sub_app, login_manager = login_manager, make_safe_url_function = make_safe_url)

        instances[sub_app.config['APPLICATION_ROOT']] = sub_app

    dispatcher = DispatcherMiddleware (static_app, instances)
    run_simple ('localhost', 5000, dispatcher)
