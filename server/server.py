#!/usr/bin/python3
# -*- encoding: utf-8 -*-

"""An application server for CBGM. Main module."""

import argparse
import collections
import csv
import datetime
import functools
import glob
import io
import itertools
import math
import operator
import re
import sys
import os
import os.path
import urllib.parse

import flask
import sqlalchemy
import flask_sqlalchemy
from flask import request, current_app
import flask_babel
from flask_babel import gettext as _, ngettext as n_, lazy_gettext as l_
import flask_user
from flask_user import login_required, roles_required
import flask_login
import flask_mail
import networkx as nx

from . import helpers
from .helpers import parameters, Bag, Passage, Manuscript, LANGUAGES, LABEZ_I18N, make_json_response
from . import security
from . import editor

from ntg_common import db
from ntg_common.db_tools import execute
from ntg_common.config import args
from ntg_common import tools
from ntg_common import db_tools

app = flask.Blueprint ('the_app', __name__)
static_app = flask.Flask (__name__)
dba = flask_sqlalchemy.SQLAlchemy ()
user_model = security.declare_user_model (dba)
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


@static_app.endpoint ('index')
def index ():
    """ Endpoint.  The root of the application. """

    return flask.redirect ('/ph4/', code = 302)


@app.endpoint ('acts-phase4')
def acts_phase4 ():
    """ Endpoint.  The current main page. """

    return flask.render_template ('acts-phase4.html')


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
            # tools.log (logging.INFO, parsed_passage)
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
        return make_json_response (passage.cliques ());


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

    Words = collections.namedtuple ('Words', 'kapanf, versanf, wortanf, kapend, versend, wortend, lemma')

    res = []
    with current_app.config.dba.engine.begin () as conn:

        if field == 'siglum':
            res = execute (conn, """
            SELECT siglum, siglum, book
            FROM books b
            WHERE siglum ~ :term OR book ~ :term
            ORDER BY bk_id
            """, dict (parameters, term = term))
            return flask.json.jsonify ([ { 'value' : r[0], 'label' : r[1], 'description' : r[2] } for r in res ])

        elif field == 'chapter':
            res = execute (conn, """
            SELECT range, range
            FROM ranges_view
            WHERE siglum = :siglum AND range ~ '[1-9][0-9]*' AND range ~ :term
            ORDER BY range::integer
            """, dict (parameters, siglum = siglum, term = term))
            return flask.json.jsonify ([ { 'value' : r[0], 'label' : r[1] } for r in res ])

        elif field == 'verse':
            res = execute (conn, """
            SELECT DISTINCT verse, verse
            FROM passages_view
            WHERE siglum = :siglum AND chapter = :chapter AND verse::varchar ~ :term
            ORDER BY verse
            """, dict (parameters, siglum = siglum, chapter = chapter, term = term))
            return flask.json.jsonify ([ { 'value' : r[0], 'label' : r[1] } for r in res ])

        elif field == 'word':
            res = execute (conn, """
            SELECT DISTINCT chapter, verse, word,
                            adr2chapter (endadr), adr2verse (endadr), adr2word (endadr),
                            lemma
            FROM passages_view
            WHERE siglum = :siglum AND chapter = :chapter AND verse = :verse AND word::varchar ~ :term
            ORDER BY word, adr2verse (endadr), adr2word (endadr)
            """, dict (parameters, siglum = siglum, chapter = chapter, verse = verse, term = term))
            res = map (Words._make, res)
            res = map (_f_map_word, res)
            return flask.json.jsonify ([ { 'value' : r[0], 'label' : r[1], 'description' : r[2] } for r in res ])

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
        SELECT DISTINCT range, range, lower (ch.irange) as anfadr, upper (ch.irange) as endadr
        FROM ranges ch
        WHERE bk_id = :bk_id
        ORDER BY anfadr, endadr DESC
        """, dict (parameters, bk_id = bk_id))

        Ranges = collections.namedtuple ('Ranges', 'range, value, anfadr, endadr')
        # ranges = list (map (Ranges._make, res))
        ranges = [ Ranges._make (r)._asdict () for r in res ]

        return make_json_response ({
            'ranges' : ranges,
        })


@app.endpoint ('manuscript.json')
def manuscript_json (hs_hsnr_id):
    """Endpoint.  Serve information about a manuscript.

    :param string hs_hsnr_id: The hs, hsnr or id of the manuscript.

    """

    hs_hsnr_id = request.args.get ('ms_id') or hs_hsnr_id

    with current_app.config.dba.engine.begin () as conn:
        ms = Manuscript (conn, hs_hsnr_id)
        return make_json_response (ms.to_json ())


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


@app.endpoint ('relatives-skeleton')
def relatives_skeleton (hs_hsnr_id, passage_or_id):
    """Endpoint. Serve a skeleton for the relatives popup.

    An endpoint that serves an empty skeleton for the relatives popup.

    """

    chapter = request.args.get ('range') or 'All'

    with current_app.config.dba.engine.begin () as conn:

        passage = Passage (conn, passage_or_id)
        ms      = Manuscript (conn, hs_hsnr_id)

    # convert tuples to lists
    return flask.render_template ('relatives-skeleton.html', ms = ms)


@app.endpoint ('relatives.html')
def relatives_html (hs_hsnr_id, passage_or_id):
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

    caption = _('Relatives for')
    where = ''
    if type_ == 'anc':
        where =  ' AND older < newer'
        caption = _('Ancestors for')
    if type_ == 'des':
        where =  ' AND older >= newer'
        caption = _('Descendants for')

    if labez == 'all':
        where += " AND labez !~ '^z'"
    elif labez == 'all+lac':
        pass
    else:
        where += " AND labez = '%s'" % labez

    if 'fragments' in fragments:
        f_where = ''
    else:
        f_where = 'AND aff.common > aff.ms1_length / 2'

    limit = '' if limit == 0 else ' LIMIT %d' % limit

    with current_app.config.dba.engine.begin () as conn:

        passage   = Passage (conn, passage_or_id)
        ms        = Manuscript (conn, hs_hsnr_id)
        ms.length = ms.get_length (passage, chapter)
        rg_id     = passage.range_id (chapter)

        # Get the attestation(s) of the manuscript
        res = execute (conn, """
        SELECT labez
        FROM apparatus_view_agg
        WHERE ms_id = :ms_id AND pass_id = :pass_id
        """, dict (parameters, ms_id = ms.ms_id, pass_id = passage.pass_id))
        ms.labez,  = res.fetchone ()

        # Get the affinity of the manuscript to all manuscripts
        res = execute (conn, """
        SELECT avg (a.affinity) as aa,
               percentile_cont(0.5) WITHIN GROUP (ORDER BY a.affinity) as ma
        FROM affinity a
        WHERE a.ms_id1 = :ms_id1 AND a.rg_id = :rg_id
        """, dict (parameters, ms_id1 = ms.ms_id, rg_id = rg_id))
        ms.aa, ms.ma = res.fetchone ()

        mt = Bag ()

        # Get the reading of MT
        res = execute (conn, """
        SELECT labez, clique, labez_clique
        FROM apparatus_view
        WHERE ms_id = 2 AND pass_id = :pass_id
        """, dict (parameters, pass_id = passage.pass_id))
        mt.labez, mt.clique, mt.labez_clique = res.fetchone ()

        # Get the affinity of the manuscript to MT
        #
        # For a description of mt and mtp see the comment in
        # ActsMsListValPh3.pl and
        # http://intf.uni-muenster.de/cbgm/actsPh3/guide_en.html#Ancestors

        mt.mt, mt.mtp = 0.0, 0.0
        res = execute (conn, """
        SELECT a.affinity as mt, a.equal::float / c.length as mtp
        FROM affinity a
        JOIN ms_ranges c
          ON (a.ms_id1, a.rg_id) = (c.ms_id, c.rg_id)
        WHERE a.ms_id1 = :ms_id1 AND a.ms_id2 = 2 AND a.rg_id = :rg_id
        """, dict (parameters, ms_id1 = ms.ms_id, rg_id = rg_id))
        if res.rowcount > 0:
            mt.mt, mt.mtp = res.fetchone ()

        Nodes = collections.namedtuple ('Nodes', 'ms_id')

        if include:
            # get ids of nodes to include
            res = execute (conn, """
            SELECT ms_id
            FROM manuscripts
            WHERE (hs IN :include)
            ORDER BY ms_id
            """, dict (parameters, include = tuple (include)))

            include = [str (n.ms_id) for n in map (Nodes._make, res)]

        exclude = set (include) ^ set (['1', '2'])
        exclude.add (-1) # a non-existing id to avoid SQL error

        # Get the X most similar manuscripts and their attestations
        res = execute (conn, """
        /* get the LIMIT closest ancestors for this node */
        WITH ranks AS (
          SELECT ms_id1, ms_id2, rank () OVER (ORDER BY affinity DESC) AS rank, affinity
          FROM {view} aff
          JOIN ms_ranges ch
            ON ch.ms_id = aff.ms_id1 AND ch.rg_id = aff.rg_id
          WHERE ms_id1 = :ms_id1 AND aff.rg_id = :rg_id AND ms_id2 NOT IN :exclude
            AND newer > older AND aff.common > ch.length / 2
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
              AND a.pass_id = :pass_id {where} {f_where}
        ORDER BY affinity DESC, r.rank, newer DESC, older DESC, hsnr
        {limit}
        """, dict (parameters, where = where, f_where = f_where, ms_id1 = ms.ms_id, hsnr = ms.hsnr,
                   pass_id = passage.pass_id, rg_id = rg_id, limit = limit,
                   view = view, exclude = tuple (exclude)))

        Relatives = collections.namedtuple (
            'Relatives',
            'rank ms_id hs hsnr length common equal older newer unclear norel direction affinity labez'
        )
        relatives = list (map (Relatives._make, res))

        return flask.render_template ('relatives.html', caption = caption, ms = ms, mt = mt, rows = relatives)


def remove_z_leaves (G, group_field):
    """ Removes leaves (recursively) if they read z. """

    # We cannot use DFS because we don't know the root.
    for n in reversed (list (nx.topological_sort (G))):
        atts = G.node[n]
        if G.out_degree (n) == 0 and group_field in atts and atts[group_field][0] == 'z':
            G.remove_node (n)


def textflow (passage_or_id):
    """ Output a stemma of manuscripts. """

    labez        = request.args.get ('labez') or ''
    hyp_a        = request.args.get ('hyp_a') or 'A'
    chapter      = request.args.get ('range') or 'All'
    connectivity = int (request.args.get ('connectivity') or 10)
    width        = float (request.args.get ('width') or 0.0)
    fontsize     = float (request.args.get ('fontsize') or 10.0)
    mode         = request.args.get ('mode') or 'sim'

    include      = set (request.args.getlist ('include[]') or ['NONE'])
    fragments    = request.args.getlist ('fragments[]') or []
    var_only     = request.args.getlist ('var_only[]')  or []
    cliques      = request.args.getlist ('cliques[]')   or []

    fragments = 'fragments' in fragments
    var_only  = 'var_only'  in var_only
    cliques   = 'cliques'   in cliques
    show_z    = 'Z'         in include

    prefix = '' if mode == 'rec' else 'p_'
    if connectivity == 21:
        connectivity = 9999

    if fragments:
        f_where = ''
    else:
        f_where = 'AND a.common > c.length / 2'

    labez_where = ''
    if labez != '':
        labez_where = 'AND a.cbgm AND a.labez = :labez'
        if hyp_a != 'A':
            labez_where = 'AND a.cbgm AND (a.labez = :labez OR (a.ms_id = 1 AND :hyp_a = :labez))'

    group_field = 'labez' if cliques else 'labez_clique'

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

        G = nx.DiGraph ()

        Nodes = collections.namedtuple ('Nodes', 'ms_id')

        # get ids of nodes to exclude
        res = execute (conn, """
        SELECT ms_id
        FROM manuscripts
        WHERE (hs IN ('A', 'MT')) AND (hs NOT IN :include)
        ORDER BY ms_id
        """, dict (parameters, include = tuple (include)))

        exclude = set ([str (n.ms_id) for n in map (Nodes._make, res)])
        exclude.add (-1) # a non-existing id to avoid SQL syntax error if empty

        # get all nodes or all nodes (hypothetically) attesting labez
        res = execute (conn, """
        SELECT ms_id
        FROM apparatus a
        WHERE pass_id = :pass_id {labez_where} AND ms_id NOT IN :exclude
        """, dict (parameters, exclude = tuple (exclude),
                   pass_id = passage.pass_id, labez = labez,
                   hyp_a = hyp_a, labez_where = labez_where))

        nodes = list (map (Nodes._make, res))

        for n in nodes:
            G.add_node (n.ms_id)

        order = 'affinity DESC, common, older, newer DESC, ms_id2' # id2 is a tiebreaker

        # query to get the closest ancestors for every node with rank <= connectivity
        query = """
        SELECT ms_id1, ms_id2, rank
        FROM (
          SELECT ms_id1, ms_id2, rank () OVER (PARTITION BY ms_id1 ORDER BY {order}) AS rank
          FROM affinity a
          JOIN ms_ranges c
            ON c.ms_id = a.ms_id1 AND c.rg_id = a.rg_id
          WHERE ms_id1 IN :nodes AND a.rg_id = :rg_id AND ms_id2 NOT IN :exclude
            AND {prefix}newer > {prefix}older {f_where}
        ) AS r
        WHERE rank <= :connectivity
        ORDER BY rank
        """

        global_textflow = not ((labez != '') or var_only)
        if global_textflow:
            connectivity = 1

        res = execute (conn, query,
                       dict (parameters, nodes = tuple (G.nodes ()), exclude = tuple (exclude),
                             rg_id = rg_id, pass_id = passage.pass_id, prefix = prefix,
                             labez = labez, connectivity = connectivity, order = order,
                             f_where = f_where, hyp_a = hyp_a, labez_where = labez_where))

        Ranks = collections.namedtuple ('Ranks', 'ms_id1 ms_id2 rank')
        ranks = list (map (Ranks._make, res))

        # Initially build a graph with all nodes.  We will remove unused nodes
        # later.
        dest_nodes = set ([r.ms_id1 for r in ranks])
        src_nodes  = set ([r.ms_id2 for r in ranks])

        res = execute (conn, """
        SELECT ms.ms_id, ms.hs, ms.hsnr, av.labez, av.clique, av.labez_clique
        FROM manuscripts ms
        JOIN (
          SELECT ms_id,
                 labez_agg (labez order by labez) as labez,
                 labez_agg (clique order by clique) as clique,
                 labez_agg (labez_clique order by labez_clique) as labez_clique
          FROM apparatus_view
          WHERE pass_id = :pass_id
          GROUP BY ms_id
        ) AS av
        USING (ms_id)
        WHERE ms.ms_id IN :ms_ids
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
            G.add_node (ms.ms_id, **attrs)

        # Step 1: A node that has ancestors within the same attestation keeps
        # only the top-ranked one as parent.
        #
        # Step 2: A node without ancestors within the same attestation keeps one
        # top-ranked parent for every other attestation.
        #
        # Assumption: ranks are sorted top-ranked first

        tags = set ()
        for step in (1, 2):
            for r in ranks:
                a1 = G.node[r.ms_id1];
                a2 = G.node[r.ms_id2];
                if not (global_textflow) and (a1[group_field][0] == 'z' or a2[group_field][0] == 'z'):
                    # disregard lacunae
                    continue
                if step == 1 and a1[group_field] != a2[group_field]:
                    # differing attestations are handled in step 2
                    continue
                if r.ms_id1 in tags:
                    # the node's ancestor within the same attestation was
                    # already seen.  we need not look into other attestations
                    continue
                if str (r.ms_id1) + a2[group_field] in tags:
                    # the node's ancestor within this attestation was already
                    # seen.  we need not look into further nodes
                    continue;
                if r.rank > 1:
                    G.add_edge (r.ms_id2, r.ms_id1, rank = r.rank, headlabel = r.rank)
                else:
                    G.add_edge (r.ms_id2, r.ms_id1)
                if a1[group_field] == a2[group_field]:
                    tags.add (r.ms_id1)
                else:
                    tags.add (str (r.ms_id1) + a2[group_field])

        if not show_z:
            remove_z_leaves (G, group_field);

        G.remove_nodes_from (list (nx.isolates (G)))

        if var_only:
            # Remove non-variant links
            #
            # remove nodes attesting zz/zw and link the children up
            for n in G:
                gf = G.node[n][group_field]
                if gf == 'zz' or '/' in gf:
                    pred = list (G.predecessors (n))
                    if pred:
                        G.remove_edge (pred[0], n)
                    for succ in G.successors (n):
                        G.remove_edge (n, succ)
                        if pred:
                            G.add_edge (pred[0], succ)

            # if one predecessor is within the same attestation then remove all
            # other predecessors that are not within the same attestation
            for n in G:
                within = False
                attestation_n = G.node[n][group_field]
                for p in G.predecessors (n):
                    if G.node[p][group_field] == attestation_n:
                        within = True
                        break
                if within:
                    for p in G.predecessors (n):
                        if G.node[p][group_field] != attestation_n:
                            G.remove_edge (p, n)

            # remove edges between nodes within the same attestation
            for u, v in list (G.edges ()):
                if G.node[u][group_field] == G.node[v][group_field]:
                    G.remove_edge (u, v)

            # remove now isolated nodes
            G.remove_nodes_from (list (nx.isolates (G)))

            # unconstrain backward edges
            for u, v in G.edges ():
                if G.node[u][group_field] > G.node[v][group_field]:
                    G.adj[u][v]['constraint'] = 'false'

        else:
            for n in G:
                # Use a different label if the parent's labez_clique differs from this
                # node's labez_clique.
                pred = list (G.predecessors (n))
                attrs = G.node[n]
                if not pred:
                    attrs['label'] = "%s: %s" % (attrs['labez_clique'], attrs['hs'])
                for p in pred:
                    if attrs['labez_clique'] != G.node[p]['labez_clique']:
                        attrs['label'] = "%s: %s" % (attrs['labez_clique'], attrs['hs'])
                        G.adj[p][n]['style'] = 'dashed'

    if var_only:
        dot = helpers.nx_to_dot_subgraphs (G, group_field, width, fontsize)
    else:
        dot = helpers.nx_to_dot (G, width, fontsize)
    return dot


@app.endpoint ('textflow.dot')
def textflow_dot (passage_or_id):
    dot = textflow (passage_or_id)
    dot = tools.graphviz_layout (dot)
    return flask.Response (dot, mimetype = 'text/vnd.graphviz')


@app.endpoint ('textflow.png')
def textflow_png (passage_or_id):
    dot = textflow (passage_or_id)
    png = tools.graphviz_layout (dot, format = 'png')
    return flask.Response (png, mimetype = 'image/png')


def csvify (fields, rows):
    fp = io.StringIO ()
    writer = csv.DictWriter (fp, fields, restval='', extrasaction='raise', dialect='excel')
    writer.writeheader ()
    for r in rows:
        writer.writerow (r._asdict ())
    return flask.Response (fp.getvalue (), mimetype = 'text/csv')


@app.endpoint ('coherence-skeleton')
def coherence_skeleton ():
    """Endpoint. Serve a skeleton of the Coherence page.

    The Coherence page is the main page of the application.  This endpoint only
    serves a skeleton.  All relevant content is then loaded by AJAX.

    """

    return flask.render_template ('coherence-skeleton.html')


@app.endpoint ('comparison-skeleton')
def comparison_skeleton ():
    """Endpoint. Serve a skeleton of the Comparison page.

    The comparison page contains a table detailing the differences between 2
    manuscripts.  This endpoint only serves a skeleton.  The table rows will be
    loaded with AJAX.

    """

    with current_app.config.dba.engine.begin () as conn:
        ms1 = Manuscript (conn, request.args.get ('ms1') or 'A')
        ms2 = Manuscript (conn, request.args.get ('ms2') or 'A')

        return flask.render_template ('comparison-skeleton.html', ms1 = ms1, ms2 = ms2)


_ComparisonRow = collections.namedtuple (
    'ComparisonRow', 'rg_id, range, common, equal, older, newer, unclear, affinity, rank, length1, length2')


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

        SELECT a.rg_id, ch.range, a.common, a.equal,
               a.{prefix}older, a.{prefix}newer, a.{prefix}unclear, a.affinity, r.rank, c1.length, c2.length
        FROM affinity a
        JOIN ranks r     USING (rg_id, ms_id1, ms_id2)
        JOIN ranges ch USING (rg_id)
        JOIN ms_ranges c1 ON a.ms_id1 = c1.ms_id AND a.rg_id = c1.rg_id
        JOIN ms_ranges c2 ON a.ms_id2 = c2.ms_id AND a.rg_id = c2.rg_id
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

        SELECT a.rg_id, ch.range, a.common, a.equal,
               a.{prefix}older, a.{prefix}newer, a.{prefix}unclear, a.affinity, r.rank, c1.length, c2.length
        FROM affinity a
        JOIN ranks2 r    USING (rg_id, ms_id1, ms_id2)
        JOIN ranges ch USING (rg_id)
        JOIN ms_ranges c1 ON a.ms_id1 = c1.ms_id AND a.rg_id = c1.rg_id
        JOIN ms_ranges c2 ON a.ms_id2 = c2.ms_id AND a.rg_id = c2.rg_id
        WHERE a.ms_id1 = :ms_id1 AND a.ms_id2 = :ms_id2
        )

        UNION

        SELECT a.rg_id, ch.range, a.common, a.equal,
               a.{prefix}older, a.{prefix}newer, a.{prefix}unclear, a.affinity, NULL, c1.length, c2.length
        FROM affinity a
        JOIN ranges ch USING (rg_id)
        JOIN ms_ranges c1 ON a.ms_id1 = c1.ms_id AND a.rg_id = c1.rg_id
        JOIN ms_ranges c2 ON a.ms_id2 = c2.ms_id AND a.rg_id = c2.rg_id
        WHERE a.ms_id1 = :ms_id1 AND a.ms_id2 = :ms_id2 AND a.{prefix}newer = a.{prefix}older

        ORDER BY rg_id
        """, dict (parameters, ms_id1 = ms1.ms_id, ms_id2 = ms2.ms_id, prefix = ''))

        return list (map (_ComparisonRowCalcFields._make, res))


_ComparisonDetailRow = collections.namedtuple (
    'ComparisonDetailRow',
    'pass_id anfadr endadr labez_clique1 lesart1 labez_clique2 lesart2 older newer unclear'
)

class _ComparisonDetailRowCalcFields (_ComparisonDetailRow):
    __slots__ = ()

    _fields = _ComparisonDetailRow._fields + ('pass_hr', 'norel')

    @property
    def pass_hr (self):
        return Passage._to_hr (self.anfadr, self.endadr)

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
        SELECT p.pass_id, p.anfadr, p.endadr, v1.labez_clique, v1.lesart,
                                              v2.labez_clique, v2.lesart,
          is_older (p.pass_id, v1.labez, v1.clique, v2.labez, v2.clique) AS older,
          is_older (p.pass_id, v2.labez, v2.clique, v1.labez, v1.clique) AS newer,
          is_unclear (p.pass_id, v1.labez, v1.clique) OR
          is_unclear (p.pass_id, v2.labez, v2.clique) AS unclear
        FROM (SELECT * FROM ranges WHERE range = :range_) r
          JOIN passages p ON (r.irange @> p.irange )
          JOIN apparatus_view v1 USING (pass_id)
          JOIN apparatus_view v2 USING (pass_id)
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
        SELECT labez, lesart
        FROM readings
        WHERE pass_id = :pass_id
        ORDER BY labez
        """, dict (parameters, pass_id = passage.pass_id))

        Readings = collections.namedtuple ('Readings', 'labez lesart')
        readings = [ Readings._make (r)._asdict () for r in res ]

        # list of labez_clique => manuscripts
        res = execute (conn, """
        SELECT labez, clique, labez_clique, ms_id, hs, hsnr, certainty
        FROM apparatus_view
        WHERE pass_id = :pass_id
        ORDER BY labez, clique, hsnr
        """, dict (parameters, pass_id = passage.pass_id))

        Manuscripts = collections.namedtuple ('Manuscripts', 'labez clique labez_clique ms_id hs hsnr certainty')
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
        nx = db_tools.local_stemma_to_nx (
            conn, passage.pass_id, flask_login.current_user.has_role ('editor')
        )
        dot = helpers.nx_to_dot (nx, width, fontsize, nodesep = 0.2)
        return dot


@app.endpoint ('stemma.dot')
def stemma_dot (passage_or_id):
    dot = stemma (passage_or_id)
    dot = tools.graphviz_layout (dot)
    return flask.Response (dot, mimetype = 'text/vnd.graphviz')


@app.endpoint ('stemma.png')
def stemma_png (passage_or_id):
    dot = stemma (passage_or_id)
    png = tools.graphviz_layout (dot, format = 'png')
    return flask.Response (png, mimetype = 'image/png')


# Turns an usafe absolute URL into a safe relative URL by removing the scheme and the hostname
# Example: make_safe_url('http://hostname/path1/path2?q1=v1&q2=v2#fragment')
#          returns: '/path1/path2?q1=v1&q2=v2#fragment
# Copied from flask_user/views.py because it was defective.

def make_safe_url (url):
    parts = urllib.parse.urlsplit (url)
    return urllib.parse.urlunsplit ( ('', '', parts[2], parts[3], parts[4]) )


if __name__ == "__main__":
    from werkzeug.routing import Map, Rule
    from werkzeug.wsgi import DispatcherMiddleware
    from werkzeug.serving import run_simple
    import logging

    instance_path = os.path.abspath (os.path.dirname (__file__) + '/instance')

    parser = argparse.ArgumentParser (description='An application server for CBGM')

    parser.add_argument ('-v', '--verbose', dest='verbose', action='count',
                         help='increase output verbosity', default=0)
    parser.add_argument ('-c', '--config-path', dest='config_path',
                         default=instance_path, metavar='CONFIG_PATH',
                         help="the directory where the config files reside (default='%s')" % instance_path)

    args = parser.parse_args (namespace = args)
    args.start_time = datetime.datetime.now ()
    LOG_LEVELS = { 0: logging.CRITICAL, 1: logging.ERROR, 2: logging.WARN, 3: logging.INFO, 4: logging.DEBUG }
    args.log_level = LOG_LEVELS.get (args.verbose + 1, logging.CRITICAL)

    babel = flask_babel.Babel ()
    babel.localeselector (helpers.get_locale)

    logging.basicConfig (format = '%(asctime)s - %(levelname)s - %(message)s')
    logging.getLogger ('sqlalchemy.engine').setLevel (args.log_level)
    logging.getLogger ('server').setLevel (args.log_level)

    instances = collections.OrderedDict ()

    static_app.config.from_pyfile (args.config_path.rstrip ('/') + '/_global.conf')
    static_app.config['server_start_time'] = str (int (args.start_time.timestamp ()))
    static_app.url_map.add (Rule ('/', endpoint = 'index'))

    static_app.config.dba = db_tools.PostgreSQLEngine (**static_app.config)
    static_app.config['SQLALCHEMY_DATABASE_URI'] = static_app.config.dba.url
    static_app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    dba.init_app (static_app)
    mail.init_app (static_app)
    user_manager.init_app (static_app, login_manager = login_manager, make_safe_url_function = make_safe_url)
    babel.init_app (static_app)

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
            Rule ('/',                                            endpoint = 'acts-phase4'),
            Rule ('/coherence',                                   endpoint = 'coherence-skeleton'),
            Rule ('/comparison',                                  endpoint = 'comparison-skeleton'),
            Rule ('/comparison-summary.csv',                      endpoint = 'comparison-summary.csv'),
            Rule ('/comparison-detail.csv',                       endpoint = 'comparison-detail.csv'),
            Rule ('/suggest.json',                                endpoint = 'suggest.json'),
            Rule ('/manuscript.json/<hs_hsnr_id>',                endpoint = 'manuscript.json'),
            Rule ('/passage.json/',                               endpoint = 'passage.json'),
            Rule ('/passage.json/<passage_or_id>',                endpoint = 'passage.json'),
            Rule ('/cliques.json/<passage_or_id>',                endpoint = 'cliques.json'),
            Rule ('/ranges.json/<passage_or_id>',                 endpoint = 'ranges.json'),
            Rule ('/ms_attesting/<passage_or_id>/<labez>',        endpoint = 'ms_attesting'),
            Rule ('/relatives/<passage_or_id>/<hs_hsnr_id>',      endpoint = 'relatives-skeleton'),
            Rule ('/relatives.html/<passage_or_id>/<hs_hsnr_id>', endpoint = 'relatives.html'),
            Rule ('/apparatus.json/<passage_or_id>',              endpoint = 'apparatus.json'),
            Rule ('/attestation.json/<passage_or_id>',            endpoint = 'attestation.json'),
            Rule ('/stemma.dot/<passage_or_id>',                  endpoint = 'stemma.dot'),
            Rule ('/stemma.png/<passage_or_id>',                  endpoint = 'stemma.png'),
            Rule ('/textflow.dot/<passage_or_id>',                endpoint = 'textflow.dot'),
            Rule ('/textflow.png/<passage_or_id>',                endpoint = 'textflow.png'),
            Rule ('/stemma-edit/<passage_or_id>',                 endpoint = 'stemma-edit'),
        ])

        tools.log (logging.INFO, "{name} at {path} from conf {conf}".format (
            name = sub_app.config['APPLICATION_NAME'],
            path = sub_app.config['APPLICATION_ROOT'],
            conf = fn))

        sub_app.config.dba = db_tools.PostgreSQLEngine (**sub_app.config)
        sub_app.config['SQLALCHEMY_DATABASE_URI'] = static_app.config.dba.url
        sub_app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        dba.init_app (sub_app)
        mail.init_app (sub_app)
        user_manager.init_app (sub_app, login_manager = login_manager, make_safe_url_function = make_safe_url)
        babel.init_app (sub_app)

        instances[sub_app.config['APPLICATION_ROOT']] = sub_app

    tools.log (logging.INFO, "Found translations for: {translations}".format (
        translations = ', '.join ([l.get_display_name () for l in babel.list_translations ()])))

    dispatcher = DispatcherMiddleware (static_app, instances)
    run_simple ('localhost', 5000, dispatcher)
