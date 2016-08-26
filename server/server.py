#!/usr/bin/python3
# -*- encoding: utf-8 -*-

"""An application server for CBGM."""

import argparse
import collections
import datetime
import itertools
import math
import re
import sys
import os.path

import flask
from flask import request
import flask_babel
from flask_babel import gettext as _, ngettext as n_

from sqlalchemy import create_engine, MetaData, Table
from sqlalchemy.sql import text
import networkx as nx
import networkx.readwrite.json_graph

# for server-side DAG layout via GraphViz
import pygraphviz as pgv

sys.path.append (os.path.dirname (os.path.abspath (__file__)) + "/..")

from ntg_common import db
from ntg_common.db import execute
from ntg_common.config import args
from ntg_common import tools

LANGUAGES = {
    'en': 'English',
    'de': 'Deutsch'
}

LABEZ_I18N = {
    'lac':     _('Lac'),
    'all':     _('All'),
    'all+lac': _('All+Lac'),
}

app = flask.Flask ("server")
babel = flask_babel.Babel (app)

@babel.localeselector
def get_locale ():
    return flask.request.accept_languages.best_match (LANGUAGES.keys ())

class Bag (object):
    """ Class to stick values in. """
    pass


class Passage (object):
    """ Represent one passage. """

    def __init__ (self, conn, passage_or_id):
        """ Initialize passage struct from passage or passage id. """

        start, end =  self.fix (passage_or_id)

        if int (start) > 10000000:
            self.start, self.end = start, end
            self.hr_pass = self.format (start, end)
            res = execute (conn, """
            SELECT id
            FROM {pass}
            WHERE anfadr = :anfadr AND endadr = :endadr
            """, dict (parameters, anfadr = start, endadr = end))
            self.pass_id = res.scalar ()
        else:
            self.pass_id = start
            res = execute (conn, """
            SELECT anfadr, endadr
            FROM {pass}
            WHERE id = :pass_id
            """, dict (parameters, pass_id = start))
            self.start, self.end = res.first ()
            self.hr_pass = self.format (self.start, self.end)

    @staticmethod
    def fix (passage):
        if '-' in passage:
            start, end = passage.split ('-')
        else:
            start, end = passage, passage

        start = str (int (start))
        end   = str (int (end))
        cut   = len (start) - len (end)
        return start, start[:cut] + end


    @staticmethod
    def format (start, end):
        def scan (p):
            p = str (int (p))
            m = re.match (r'^(\d)(\d\d)(\d\d)(\d\d\d)$', p)
            if (m):
                b = Bag ()
                b.book    = int (m.group (1))
                b.chapter = int (m.group (2))
                b.verse   = int (m.group (3))
                b.word    = int (m.group (4))
                return b
            return None

        s = scan (start)
        res = "%s %d:%d/%d" % (tools.BOOKS[s.book - 1][1], s.chapter, s.verse, s.word)

        if (end is not None):
            e = scan (end)

            if (e.book != s.book):
                return res + " - %s %d:%d/%d" % (tools.BOOKS[e.book - 1], e.chapter, e.verse, e.word)
            if (e.chapter != s.chapter):
                return res + " - %d:%d/%d" % (e.chapter, e.verse, e.word)
            if (e.verse != s.verse):
                return res + " - %d/%d" % (e.verse, e.word)
            if (e.word != s.word):
                return res + "-%d" % e.word

        return res


def ord_labez (labez):
    if labez == 'lac':
        return 0
    return (ord (labez[0]) - 96)


def char_labez (labez):
    if labez == 0:
        return 'lac'
    return chr (labez + 96)


@app.route ("/")
def index ():
    return flask.render_template ('index.html')


@app.route('/ms_attesting/<int:pass_id>/<labez>')
def ms_attesting (pass_id, labez):
    """ Get all mss. attesting labez at passage. """

    with dba.engine.begin () as conn:

        res = execute (conn, """
        SELECT anfadr, endadr
        FROM {pass}
        WHERE id = :pass_id
        """, dict (parameters, pass_id = pass_id))

        row = res.fetchone ()
        passage = format_passage (row[0], row[1])

        res = execute (conn, """
        SELECT hsnr
        FROM {att}
        WHERE anfadr = :anfadr AND endadr = :endadr AND labez = :labez
        ORDER BY hsnr
        """, dict (parameters, anfadr = row [0], endadr = row[1], labez = labez ))

        Attesting = collections.namedtuple ('Attesting', 'hsnr')
        attesting = list (map (Attesting._make, res))

        # convert tuples to lists
        return flask.render_template ("ms_attesting.html",
                                      pass_id = pass_id, passage = passage, labez = labez, rows = attesting)


@app.route('/relatives/<int:pass_id>/<int:hsnr>')
@app.route('/ancestors/<int:pass_id>/<int:hsnr>')
@app.route('/descendants/<int:pass_id>/<int:hsnr>')
def relatives (hsnr, pass_id):
    """Output a table of the nearest relatives of a manuscript.

    Output a table of the nearest relatives/ancestors/descendants of a
    manuscript and what they attest.

    """

    chapter = request.args.get ('chapter') or 0
    limit   = int (request.args.get ('limit') or 10)
    labez   = request.args.get ('labez') or 'all'

    caption = _('Relatives for')
    where = ''
    if 'ancestors' in request.url_rule.rule:
        where =  ' AND older < newer'
        caption = _('Ancestors for')
    if 'descendants' in request.url_rule.rule:
        where =  ' AND older >= newer'
        caption = _('Descendants for')
    if labez == 'all':
        where += ' AND labez > 0'
    elif labez == 'all+lac':
        pass
    else:
        where += ' AND labez = %d' % ord_labez (labez)

    with dba.engine.begin () as conn:

        # Get the manuscript name
        ms = Bag ()
        res = execute (conn, """
        SELECT id - 1 as id, hs, hsnr FROM {ms} WHERE hsnr = :hsnr
        """, dict (parameters, hsnr = hsnr))
        ms.id_, ms.hs, ms.hsnr = res.fetchone ()

        # Get the attestation (labez) of the manuscript
        res = execute (conn, """
        SELECT char_labez (labez) as labez, labezsuf
        FROM {labez}
        WHERE ms_id = :ms_id AND pass_id = :pass_id
        """, dict (parameters, ms_id = ms.id_ + 1, pass_id = pass_id))
        ms.labez, ms.labezsuf = res.fetchone ()

        # Get the passage
        res = execute (conn, """
        SELECT kapanf FROM {pass} WHERE id = :pass_id
        """, dict (parameters, pass_id = pass_id))
        pass_chapter, = res.fetchone ()

        # Get the affinity of the manuscript to MT
        mt = Bag ()
        res = execute (conn, """
        SELECT affinity FROM {aff} WHERE id1 = :id1 AND id2 = 2 AND chapter = :chapter
        """, dict (parameters, id1 = ms.id_ + 1, chapter = chapter))
        mt.aff = res.scalar ()

        # Get the attestation (labez) of MT
        res = execute (conn, """
        SELECT char_labez (labez) as labez, labezsuf
        FROM {labez}
        WHERE ms_id = 2 AND pass_id = :pass_id
        """, dict (parameters, pass_id = pass_id))
        mt.labez, mt.labezsuf = res.fetchone ()

        # Get all variants for this passage
        res = execute (conn, """
        SELECT DISTINCT char_labez (labez) as clabez
        FROM {labez}
        WHERE pass_id = :pass_id
        ORDER BY clabez
        """, dict (parameters, pass_id = pass_id))
        res = [('all', )] + list (res) + [('all+lac', )]
        Variants = collections.namedtuple ('Variants', 'labez labez_i18n')
        variants = list (map (Variants._make, ((r[0], LABEZ_I18N.get (r[0], r[0])) for r in res)))

        # Get chapter length
        # To make the following huge query a bit smaller
        res = execute (conn, """
        SELECT length
        FROM {chap}
        WHERE ms_id = :ms_id1 AND chapter = :chapter
        """, dict (parameters, ms_id1 = ms.id_ + 1, chapter = chapter))
        chapter_length, = res.fetchone ()

        # Get the X most similar manuscripts and their attestations
        res = execute (conn, """
        SELECT aff.rank,
               ms2.id - 1 as ms_id,
               ms2.hs,
               ms2.hsnr,
               aff.common,
               aff.equal,
               aff.older,
               aff.newer,
               aff.unclear,
               aff.common - aff.equal - aff.older - aff.newer - aff.unclear as norel,
               if (aff.newer < aff.older, '', if (aff.newer = aff.older, '=', '>')) as direction,
               aff.affinity,
               char_labez (labez.labez) as labez,
               labez.labezsuf
        FROM
          {aff} aff
        JOIN {ms} ms2
          ON aff.id2 = ms2.id
        JOIN {labez} labez
          ON aff.id2 = labez.ms_id
        JOIN {chap} ch
          ON aff.id2 = ch.ms_id AND ch.chapter = :chapter
        WHERE id1 = :ms_id1 AND aff.chapter = :chapter AND aff.common > 0
              AND ch.length > :threshold AND labez.pass_id = :pass_id {where}
        ORDER BY affinity DESC, rank, newer DESC, older DESC
        LIMIT :limit
        """, dict (parameters, where = where, ms_id1 = ms.id_ + 1, hsnr = hsnr,
                   pass_id = pass_id, chapter = chapter, limit = limit,
                   threshold = max (1, chapter_length // 2)))

        Relatives = collections.namedtuple (
            'Relatives',
            'rank ms_id hs hsnr common equal older newer unclear norel direction affinity labez labezsuf'
        )
        relatives = list (map (Relatives._make, res))

        # convert tuples to lists
        return flask.render_template ("relatives.html",
                                      pass_id = pass_id, pass_chapter = pass_chapter, caption = caption,
                                      ms = ms, mt = mt, variants = variants, rows = relatives)


@app.route('/coherence.json/<passage_or_id>/attestation/<labez>')
def coherence_attestation_json (passage_or_id, labez):

    max_rank = 10

    with dba.engine.begin () as conn:
        passage = Passage (conn, passage_or_id)

        G = pgv.AGraph (directed = True, ordering = "out", dpi = 100,
                        ranksep = 0.2, nodesep = 0.2, rankdir = 'BT')
        G.node_attr.update (width = 0.6, fixedsize = "shape", shape ="circle")
        G.edge_attr.update (headclip = "false", tailclip = "false",
                            # headclip, tailclip: important! otherwise the pos
                            # will contain endpoint positions which will offset
                            # our parsing in the js
                            arrowhead = "none", arrowtail = "none")

        res = execute (conn, """
        SELECT ms_id, hs
        FROM {labez} labez
        JOIN {ms} ms
          ON ms.id = labez.ms_id AND labez.pass_id = :pass_id AND labez.labez = :labez_ord
        ORDER BY ms_id
        """, dict (parameters, pass_id = passage.pass_id, labez_ord = ord_labez (labez)))

        Mss = collections.namedtuple ('Mss', 'ms_id hs')
        mss = list (map (Mss._make, res))
        for ms in mss:
            G.add_node (ms.ms_id, label = ms.hs, labez = labez)

        res = execute (conn, """
        SELECT aff.id1, aff.id2, aff.rank
        FROM {aff} aff
        JOIN {labez} labez1
          ON aff.id1 = labez1.ms_id AND labez1.pass_id = :pass_id AND labez1.labez = :labez_ord
        JOIN {labez} labez2
          ON aff.id2 = labez2.ms_id AND labez2.pass_id = :pass_id AND labez2.labez = :labez_ord
        WHERE aff.chapter = 0 AND aff.rank > 0 AND aff.rank <= :rank
        ORDER BY rank, id1, id2
        """, dict (parameters, pass_id = passage.pass_id, labez_ord = ord_labez (labez), rank = max_rank))

        Ranks = collections.namedtuple ('Ranks', 'ms_id1 ms_id2 rank')
        ranks = list (map (Ranks._make, res))

        has_parent = set ()
        for r in ranks:
            if not r.ms_id1 in has_parent:
                if r.rank > 1:
                    G.add_edge (r.ms_id2, r.ms_id1, rank = r.rank)
                else:
                    G.add_edge (r.ms_id2, r.ms_id1)
                has_parent.add (r.ms_id1)

        # nx.set_node_attributes (G, 'pos', nx.nx_pydot.pydot_layout (G, prog='dot'))
        G.layout (prog = 'dot')

    # return flask.json.jsonify (nx.readwrite.json_graph.node_link_data (G))
    return graph_to_d3json (G)


@app.route('/coherence/<passage_or_id>/attestation/<labez>')
def coherence_attestation (passage_or_id, labez):

    with dba.engine.begin () as conn:
        passage = Passage (conn, passage_or_id)

        return flask.render_template ('coherence_attestation.html', passage = passage, labez = labez)


@app.route('/coherence/<passage>')
def coherence (passage):

    values = Bag ()

    with dba.engine.begin () as conn:
        passage = Passage (conn, passage)

        # list of labez
        res = execute (conn, """
        SELECT DISTINCT labez, labezsuf, ord_labez (labez) as ord_labez, lesart
        FROM {att}
        WHERE anfadr = :anfadr AND endadr = :endadr AND NOT labez REGEXP '^z'
        ORDER BY labez, labezsuf
        """, dict (parameters, anfadr = passage.start, endadr = passage.end))

        Readings = collections.namedtuple ('Readings', 'labez labezsuf ord_labez lesart')
        readings = list (map (Readings._make, res))

        values.readings = []
        for r in readings:
            res = execute (conn, """
            SELECT ms.id - 1 as id, ms.hs
            FROM {att} att
            JOIN {ms} ms
            ON att.hsnr = ms.hsnr
            WHERE anfadr = :anfadr AND endadr = :endadr AND labez = :labez AND labezsuf = :labezsuf
            ORDER BY ms.hsnr
            """, dict (parameters, anfadr = passage.start, endadr = passage.end,
                       labez = r.labez, labezsuf = r.labezsuf))

            b = Bag ()
            b.labez = r.labez
            b.labezsuf = r.labezsuf
            b.ord_labez = r.ord_labez
            b.lesart = r.lesart
            b.manuscripts = res.fetchall ()
            values.readings.append (b)

        # manuscript -> labez
        res = execute (conn, """
        SELECT ms_id - 1 AS ms_id, labez, labezsuf
        FROM {labez}
        WHERE pass_id = :pass_id
        """, dict (parameters, pass_id = passage.pass_id))

        Attestation = collections.namedtuple ('Attestation', 'id labez labezsuf')
        values.attestation = list (map (Attestation._make, res))

        return flask.render_template ('coherence.html', passage = passage, values = values)

    return 'Error'


@app.route('/coherence.json/<int:pass_id>')
def coherence_json (pass_id):

    with dba.engine.begin () as conn:

        res = execute (conn, """
        SELECT ms_id, labez
        FROM {labez}
        WHERE pass_id = :pass_id
        ORDER BY ms_id
        """, dict (parameters, pass_id = pass_id))

        attestations = {}
        for row in res:
            ms_id, labez = row
            attestations[str(ms_id - 1)] = labez

        return flask.json.jsonify ({
            'attestations': attestations
        })


def get_stemma (pass_id):
    with dba.engine.begin () as conn:

        res = execute (conn, """
        SELECT varid, varnew, s1, s2
        FROM {locstemed} s
        JOIN {pass} p
        ON s.begadr = p.anfadr AND s.endadr = p.endadr
        WHERE s.varnew NOT REGEXP '^z' AND p.id = :pass_id
        ORDER BY varnew
        """, dict (parameters, pass_id = pass_id))

        Variant = collections.namedtuple ('stemma_json_variant', 'varid, varnew, s1, s2')

        rows = list (map (Variant._make, res))
        return rows


def graph_to_d3json (g):
    """ Convert a graph into a json-formatted string suitable for D3. """

    # bb = g.graph_attr['bb']
    nxg = nx.DiGraph ()

    for id_ in g.iternodes ():
        n = g.get_node (id_)
        x, y = n.attr["pos"].split (",")

        params = {}
        params['x'] = float (x)
        params['y'] = float (y)
        for name in ('label', 'labez', 'href'):
            if name in n.attr:
                params[name] = n.attr[name]

        nxg.add_node (id_, **params)

    for e in g.iteredges ():
        params = {}
        for name in ('pos', 'rank'):
            if name in e.attr:
                params[name] = e.attr[name]

        nxg.add_edge (e[0], e[1], **params)

    return flask.json.jsonify (nx.readwrite.json_graph.node_link_data (nxg))


@app.route('/stemma.json/<int:pass_id>')
def stemma_json (pass_id):
    """Return a local stemma in json format.

    Return a local stemma in a json format suitable for D3.  A local stemma is a
    DAG (directed acyclic graph).  The layout is precomputed on the server side
    using GraphViz.  Node positions and link paths are added to the graph as
    attributes.

    I considered client-side layout of DAGs but found only 2 libraries:

    - dagre.  Javascript clone of GraphViz.  Unmaintained.  Buggy.  Does not
      work well with require.js.

    - viz.js.  GraphViz cross-compiled to Javascript with Emscripten.  Huge.
      Promising but still early days.

    Both libraries have their drawbacks so the easiest way out was to precompute
    the layout on the server.

    """
    rows = get_stemma (pass_id)

    # G = nx.DiGraph (rankdir = "BT", ordering = "out")
    G = pgv.AGraph (directed = True, ordering = "out", dpi = 100,
                    ranksep = 0.2, nodesep = 0.2, rankdir = 'BT')
    G.node_attr.update (width = 0.6, fixedsize = "shape", shape ="circle")
    G.edge_attr.update (headclip = "false", tailclip = "false",
                        # important! otherwise the pos will contain endpoint
                        # positions which will offset our parsing in the js
                        arrowhead = "none", arrowtail = "none")

    for row in rows:
        G.add_node (row.varnew, label = row.varnew, labez = row.varid,
                    href = "/coherence/%s/attestation/%s" % (pass_id, row.varid))
        if row.s1 != '*':
            G.add_edge (row.s1, row.varnew)
        if row.s2 and row.s2 != '*':
            G.add_edge (row.s2, row.varnew)

    # nx.set_node_attributes (G, 'pos', nx.nx_pydot.pydot_layout (G, prog='dot'))
    G.layout (prog = 'dot')

    # return flask.json.jsonify (nx.readwrite.json_graph.node_link_data (G))
    return graph_to_d3json (G)


@app.route('/affinity.json')
def affinity_json ():
    """ Return manuscript affinities for D3.

    Returns manuscript affinities in a json format suitable for D3.js.

    """
    with dba.engine.begin () as conn:

        res = execute (conn, """
        SELECT id, hs, hsnr, length
        FROM Manuscripts
        ORDER BY id
        """, {})

        nodes = []
        edges = []

        # Every ms gets to be a node.
        for row in res:
            id_, hs, hsnr, length = row
            nodes.append ( {
                'id'     : id_ - 1,
                'hs'     : hs,
                'hsnr'   : hsnr,
                'group'  : hsnr // 100000,
                'radius' : 5 + math.log (length)
            } )

            # Build edges table.  Needs brains.  Creating an edge between every
            # two mss will not give a very meaningful graph.  We have to keep only
            # the most significant edges.  But what is significant?
            #
            # Currently we `edge´: for each manuscript the X most similar
            # manuscripts that are at least half as long.

            limit = 20

            res2 = execute (conn, """
            SELECT id1, id2, common, equal
            FROM {aff} aff
              JOIN {ms} ms1
              JOIN {ms} ms2
              ON aff.id1 = ms1.id AND aff.id2 = ms2.id
                AND common >= ms1.length / 2
            WHERE chapter = 0 AND id1 = :id1
            ORDER BY affinity DESC
            LIMIT :limit
            """, dict (parameters, id1 = id_, limit = limit))

            for i, row in enumerate (res2):
                id1, id2, common, equal = row

                edges.append ( {
                    'source' : id1 - 1,
                    'target' : id2 - 1,
                    'common' : common,
                    'equal'  : equal,
                    'rank'   : i + 1
                } )

        return flask.json.jsonify ({
            'nodes': nodes,
            'links': edges
        })


if __name__ == "__main__":
    parser = argparse.ArgumentParser (description='An application server for CBGM')

    parser.add_argument ('-v', '--verbose', dest='verbose', action='count',
                         help='increase output verbosity', default=0)
    parser.add_argument ('-p', '--profile', dest='profile', default='ntg-local',
                         metavar='PROFILE', help="the database profile (default='ntg-local')")

    parser.parse_args (namespace = args)
    args.source_db = 'ECM_Acts_Ph3'
    args.target_db = 'ECM_Acts_UpdatePh3'
    args.src_vg_db = 'VarGenAtt_ActPh3'
    args.chapter = 0
    args.start_time = datetime.datetime.now ()

    dba = db.DBA (args.profile)

    parameters = tools.init_parameters (tools.DEFAULTS)

    app.run ()
