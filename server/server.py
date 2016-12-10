#!/usr/bin/python3
# -*- encoding: utf-8 -*-

"""An application server for CBGM."""

import argparse
import collections
import datetime
import glob
import itertools
import math
import re
import sys
import os
import os.path

import flask
from flask import request, current_app
import flask_babel
from flask_babel import gettext as _, ngettext as n_, lazy_gettext as l_
import six
import networkx as nx

sys.path.append (os.path.abspath (os.path.dirname (__file__) + '/..'))

instance_path = os.path.abspath (os.path.dirname (__file__) + '/instance')

from ntg_common import db
from ntg_common.db import execute
from ntg_common.config import args
from ntg_common import tools

LANGUAGES = {
    'en': 'English',
    'de': 'Deutsch'
}

LABEZ_I18N = {
    'z':       l_('Lac'),
    'zu':      l_('Overlap'),
    'zv':      l_('Lac'),
    'zw':      l_('Dub'),
    'zz':      l_('Lac'),
    'lac':     l_('Lac'),
    'all':     l_('All'),
    'all+lac': l_('All+Lac'),
}

app = flask.Blueprint ('the_app', __name__)
static_app = flask.Flask (__name__)


def get_locale ():
    return flask.request.accept_languages.best_match (LANGUAGES.keys ())


class Bag (object):
    """ Class to stick values in. """
    pass


class Manuscript (object):
    """ Represent one manuscript. """

    RE_HSNR = re.compile (r'^\d{6}$')
    RE_MSID = re.compile (r'^\d+$')
    RE_HS   = re.compile (r'^[PL]?[s\d]+[.]?$')

    def __init__ (self, conn, manuscript_id_or_hs_or_hsnr):
        """ Initialize passage struct from manuscript id or hs or hsnr. """

        self.ms_id = self.hs = self.hsnr = None
        param = manuscript_id_or_hs_or_hsnr

        if Manuscript.RE_HSNR.search (param):
            where = 'hsnr = :param'
            param = int (param)
        elif Manuscript.RE_MSID.search (param):
            where = 'id = :param'
            param = int (param) + 1
        elif Manuscript.RE_HS.search (param):
            where = 'hs = :param'
            param = param.strip ('.')
        else:
            return

        res = execute (conn, """
        SELECT id - 1 as id, hs, hsnr
        FROM {ms}
        WHERE {where}
        """, dict (parameters, where = where, param = param))

        self.ms_id, self.hs, self.hsnr = res.first ()


class Word (object):
    """ Represents on word address. """

    RE_HR_WORD = re.compile (r'^(?:(\w+)\s)?(?:(\d+):)?(?:(\d+)/)?(\d+)$')

    def __init__ (self, w = 0):
        w = int (w)
        self.word    = w % 1000
        w //= 1000
        self.verse   = w % 100
        w //= 100
        self.chapter = w % 100
        w //= 100
        self.book    = w


    def __str__ (self):
        return str (10000000 * self.book + 100000 * self.chapter + 1000 * self.verse + self.word)


    def parse (self, s):
        # Parse an address from the format: "Acts 1:2/3-4"
        m = Word.RE_HR_WORD.match (s)
        if (m):
            self.book    = 5 # FIXME parse m.group (1)
            self.chapter = int (m.group (2) or '0')
            self.verse   = int (m.group (3) or '0')
            self.word    = int (m.group (4) or '0')
        return self


    def format (self, start = None):
        # Format a word to the format: "Acts 1:2/3-4"
        if start is None:
            return "%s %d:%d/%d" % (tools.BOOKS[self.book - 1][1], self.chapter, self.verse, self.word)

        if (start.book != self.book):
            return " - %s %d:%d/%d" % (tools.BOOKS[self.book - 1], self.chapter, self.verse, self.word)
        if (start.chapter != self.chapter):
            return " - %d:%d/%d" % (self.chapter, self.verse, self.word)
        if (start.verse != self.verse):
            return " - %d/%d" % (self.verse, self.word)
        if (start.word != self.word):
            return "-%d" % self.word
        return ""


class Passage (object):
    """ Represents one passage. """

    def __init__ (self, conn, passage_or_id):
        """ Initialize passage struct from passage or passage id. """

        self.conn = conn
        start, end =  self.fix (str (passage_or_id))

        if int (start) > 10000000:
            res = execute (conn, """
            SELECT id, anfadr, endadr, kapanf
            FROM {pass}
            WHERE anfadr = :anfadr AND endadr = :endadr
            """, dict (parameters, anfadr = start, endadr = end))
        else:
            res = execute (conn, """
            SELECT id, anfadr, endadr, kapanf
            FROM {pass}
            WHERE id = :pass_id
            """, dict (parameters, pass_id = start))

        self.pass_id, self.start, self.end, self.chapter = res.first ()


    def to_hr (self):
        # return passage in human-readable format
        s = Word (self.start).format ()

        if self.start == self.end:
            return s
        return s + Word (self.end).format (Word (self.start))


    def to_json (self):
        return flask.json.jsonify ({
            'id'       : self.pass_id,
            'hr'       : self.to_hr (),
            'start'    : str (self.start),
            'end'      : str (self.end),
            'passage'  : self.to_passage (),
            'chapter'  : str (self.chapter),
            'variants' : self.variants (),
        })


    @staticmethod
    def parse (hr):
        if '-' in hr:
            s, e = hr.split ('-')
            s = Word ().parse (s.strip ())
            e = Word ().parse (e.strip ())
            e.book    = e.book    or s.book
            e.chapter = e.chapter or s.chapter
            e.verse   = e.verse   or s.verse
            e.word    = e.word    or s.word
            return "%s-%s" % (str (s), str (e))
        return str (Word ().parse (hr))


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


    def to_passage (self):
        # get a passage id in the form "start-end"
        if self.start == self.end:
            return str (self.start)
        common = len (os.path.commonprefix ((str (self.start), str (self.end))))
        return str (self.start) + '-' + str (self.end)[common:]


    def variants (self, prefix = [], suffix = [], delete = []):
        # Get a list of all variants for this passage

        res = execute (self.conn, """
        SELECT DISTINCT SUBSTR (labez, 1, 1) AS labez
        FROM {var}
        WHERE pass_id = :pass_id
        ORDER BY labez
        """, dict (parameters, pass_id = self.pass_id))

        d = collections.OrderedDict ()
        for p in prefix:
            d[p] = p
        for row in res:
            d[row[0]] = row[0]
        for s in suffix:
            d[s] = s
        for dd in delete:
            if dd in d:
                del d[dd]
        for k in d.keys ():
            d[k] = LABEZ_I18N.get (d[k], d[k])

        Variants = collections.namedtuple ('Variants', 'labez labez_i18n')
        return list (map (Variants._make, ((k, v) for k, v in d.items ())))


@static_app.route ("/")
def index ():
    return flask.render_template ('index.html')


@app.route ("/")
def index ():
    return flask.render_template ('links.html')


@app.route('/passage.json/<passage_or_id>')
def passage_json (passage_or_id):

    passage_or_id = request.args.get ('pass_id') or passage_or_id
    dest   = request.args.get ('dest')
    button = request.args.get ('button')

    with current_app.config.dba.engine.begin () as conn:
        if dest and button == 'Go':
            passage = Passage (conn, Passage.parse (dest))
            return passage.to_json ()

        if button in ('-1', '1'):
            passage = Passage (conn, passage_or_id)
            passage = Passage (conn, int (passage.pass_id) + int (button))
            return passage.to_json ()

        passage = Passage (conn, passage_or_id)
        return passage.to_json ()


@app.route('/ms_attesting/<passage_or_id>/<labez>')
def ms_attesting (passage_or_id, labez):
    """ Serve all relatives of all mss. attesting labez at passage. """

    with current_app.config.dba.engine.begin () as conn:
        passage = Passage (conn, passage_or_id)

        res = execute (conn, """
        SELECT hsnr
        FROM {var}_view
        WHERE pass_id = :pass_id AND labez = :labez
        ORDER BY hsnr
        """, dict (parameters, pass_id = passage.pass_id, labez = labez))

        Attesting = collections.namedtuple ('Attesting', 'hsnr')
        attesting = list (map (Attesting._make, res))

        # convert tuples to lists
        return flask.render_template ("ms_attesting.html",
                                      passage = passage, labez = labez, rows = attesting)


@app.route('/relatives/<passage_or_id>/<hs_hsnr_id>')
@app.route('/ancestors/<passage_or_id>/<hs_hsnr_id>')
@app.route('/descendants/<passage_or_id>/<hs_hsnr_id>')
def relatives (hs_hsnr_id, passage_or_id):
    """Output a table of the nearest relatives of a manuscript.

    Output a table of the nearest relatives/ancestors/descendants of a
    manuscript and what they attest.

    """

    chapter   = request.args.get ('chapter') or 0
    limit     = int (request.args.get ('limit') or 10)
    labez     = request.args.get ('labez') or 'all'
    mode      = request.args.get ('mode') or 'rec'
    include   = request.args.getlist ('include[]') or []
    fragments = request.args.getlist ('fragments[]') or []

    caption = _('Relatives for')
    where = ''
    if 'ancestors' in request.url_rule.rule:
        where =  ' AND older <= newer'
        caption = _('Ancestors for')
    if 'descendants' in request.url_rule.rule:
        where =  ' AND older >= newer'
        caption = _('Descendants for')

    if labez == 'all':
        where += " AND labez !~ '^z'"
    elif labez == 'all+lac':
        pass
    else:
        where += " AND labez = '%s'" % labez

    prefix = '' if mode == 'rec' else 'p_'

    if '1' in fragments:
        f_where = ''
    else:
        f_where = 'AND aff.common > ch.length / 2'

    limit = '' if limit == 0 else ' LIMIT %d' % limit

    with current_app.config.dba.engine.begin () as conn:

        passage = Passage (conn, passage_or_id)
        ms      = Manuscript (conn, hs_hsnr_id)

        # Get the attestation (labez) of the manuscript
        res = execute (conn, """
        SELECT labez, labezsuf, varid, varnew
        FROM {var}
        WHERE ms_id = :ms_id AND pass_id = :pass_id
        """, dict (parameters, ms_id = ms.ms_id + 1, pass_id = passage.pass_id))
        ms.labez, ms.labezsuf, ms.varid, ms.varnew = res.fetchone ()

        # Get the passage
        res = execute (conn, """
        SELECT kapanf FROM {pass} WHERE id = :pass_id
        """, dict (parameters, pass_id = passage.pass_id))
        pass_chapter, = res.fetchone ()

        # Get the affinity of the manuscript to MT
        #
        # For the reason we don't simply use affinity.affinity, see the comment
        # in: ActsMsListValPh3.pl
        mt = Bag ()
        res = execute (conn, """
        SELECT a.equal::float / c.length as affinity
        FROM {aff} a
        JOIN {chap} c
          ON (a.id1, a.chapter) = (c.ms_id, c.chapter)
        WHERE a.id1 = :id1 AND a.id2 = 2 AND a.chapter = :chapter
        """, dict (parameters, id1 = ms.ms_id + 1, chapter = chapter))
        mt.aff = res.scalar ()

        # Get the attestation (labez) of MT
        res = execute (conn, """
        SELECT labez, labezsuf, varid, varnew
        FROM {var}
        WHERE ms_id = 2 AND pass_id = :pass_id
        """, dict (parameters, pass_id = passage.pass_id))
        mt.labez, mt.labezsuf, mt.varid, mt.varnew = res.fetchone ()

        Nodes = collections.namedtuple ('Nodes', 'ms_id')

        if include:
            # get ids of nodes to include
            res = execute (conn, """
            SELECT id
            FROM {ms}
            WHERE (hs IN :include)
            ORDER BY id
            """, dict (parameters, include = tuple (include)))

            include = [str (n.ms_id) for n in map (Nodes._make, res)]

        exclude = set (include) ^ set (['1', '2'])
        exclude.add (-1) # a non-existing id to avoid SQL error

        # Get the X most similar manuscripts and their attestations
        res = execute (conn, """
        /* get the LIMIT closest ancestors for this node */
        WITH ranks AS (
          SELECT id1, id2, rank () OVER (ORDER BY affinity DESC) AS rank, affinity
          FROM {aff} aff
          JOIN {chap} ch
            ON ch.ms_id = aff.id1 AND ch.chapter = aff.chapter
          WHERE id1 = :ms_id1 AND aff.chapter = :chapter AND id2 NOT IN :exclude
            AND {prefix}newer > {prefix}older AND aff.common > ch.length / 2
          ORDER BY affinity DESC
        )

        SELECT r.rank,
               ms2.id - 1 as ms_id,
               ms2.hs,
               ms2.hsnr,
               aff.common,
               aff.equal,
               aff.{prefix}older,
               aff.{prefix}newer,
               aff.unclear,
               aff.common - aff.equal - aff.{prefix}older - aff.{prefix}newer - aff.unclear as norel,
               CASE WHEN aff.{prefix}newer < aff.{prefix}older THEN ''
                    WHEN aff.{prefix}newer = aff.{prefix}older THEN '-'
                    ELSE '>'
               END as direction,
               aff.affinity,
               v.labez,
               v.labezsuf,
               v.varid,
               v.varnew
        FROM
          {aff} aff
        JOIN {ms} ms2
          ON aff.id2 = ms2.id AND aff.id2 NOT IN :exclude
        JOIN {var} v
          ON aff.id2 = v.ms_id
        JOIN {chap} ch
          ON ch.ms_id = aff.id1 AND ch.chapter = aff.chapter
        LEFT JOIN ranks r
          ON r.id2 = aff.id2
        WHERE aff.id1 = :ms_id1 AND aff.chapter = :chapter AND aff.common > 0
              AND v.pass_id = :pass_id {where} {f_where}
        ORDER BY affinity DESC, r.rank, {prefix}newer DESC, {prefix}older DESC, hsnr
        {limit}
        """, dict (parameters, where = where, f_where = f_where, ms_id1 = ms.ms_id + 1, hsnr = ms.hsnr,
                   pass_id = passage.pass_id, chapter = chapter, limit = limit,
                   prefix = prefix, exclude = tuple (exclude)))

        Relatives = collections.namedtuple (
            'Relatives',
            'rank ms_id hs hsnr common equal older newer unclear norel direction affinity labez labezsuf varid varnew'
        )
        relatives = list (map (Relatives._make, res))

        variants = passage.variants (prefix = ('all', ), suffix = ('all+lac', ))

        # convert tuples to lists
        return flask.render_template ("relatives.html", passage = passage, caption = caption,
                                      ms = ms, mt = mt, variants = variants, rows = relatives)


@app.route('/textflow.dot/<passage_or_id>/attestation/<varnew>')
def textflow_dot (passage_or_id, varnew):

    chapter      = request.args.get ('chapter') or 0
    connectivity = int (request.args.get ('connectivity') or 10)
    mode         = request.args.get ('mode') or 'rec'
    include      = request.args.getlist ('include[]') or []
    fragments    = request.args.getlist ('fragments[]') or []

    prefix = '' if mode == 'rec' else 'p_'

    if '1' in fragments:
        f_where = ''
    else:
        f_where = 'AND a.common > c.length / 2'

    with current_app.config.dba.engine.begin () as conn:
        passage = Passage (conn, passage_or_id)

        G = nx.DiGraph ()

        Nodes = collections.namedtuple ('Nodes', 'ms_id')

        if include:
            # get ids of nodes to include
            res = execute (conn, """
            SELECT id
            FROM {ms}
            WHERE (hs IN :include)
            ORDER BY id
            """, dict (parameters, include = tuple (include)))

            include = [str (n.ms_id) for n in map (Nodes._make, res)]

        exclude = set (include) ^ set (['1', '2'])
        exclude.add (-1) # a non-existing id to avoid SQL error

        # get nodes attesting varnew
        res = execute (conn, """
        SELECT ms_id
        FROM {var}
        WHERE pass_id = :pass_id AND varnew ~ :varnew AND ms_id NOT IN :exclude
        """, dict (parameters, exclude = tuple (exclude),
                   pass_id = passage.pass_id, varnew = '^' + varnew))

        nodes = list (map (Nodes._make, res))

        for n in nodes:
            G.add_node (n.ms_id)

        # FIXME: why do we get a different result if we remove the inner ORDER BY clauses?
        # FIXME: change this query to give a sorted graph. How?

        res = execute (conn, """
        /* get the :connectivity closest ancestors for every node */
        WITH ranks AS (
          SELECT id1, id2, rank () OVER (PARTITION BY id1 ORDER BY affinity DESC) AS rank, affinity
          FROM {aff} a
          JOIN {chap} c
            ON c.ms_id = a.id1 AND c.chapter = a.chapter
          WHERE id1 IN :nodes AND a.chapter = :chapter AND id2 NOT IN :exclude
            AND {prefix}newer > {prefix}older AND a.common > c.length / 2
        )

        /* get the closest ancestor attesting varnew */

        (SELECT DISTINCT ON (id1) 1 as u, id1, id2, rank, affinity
        FROM ranks r
        JOIN {var} v
          ON v.ms_id = id2 AND v.pass_id = :pass_id AND v.varnew ~ :varnew
        WHERE r.rank <= :connectivity AND r.id2 NOT IN :exclude
        ORDER BY id1, affinity DESC)

        UNION

        /* get the closest ancestor attesting anything (as fallback if the query
           above fails to get a result) */

        (SELECT DISTINCT ON (id1) 2 as u, id1, id2, rank, affinity
        FROM ranks r
        JOIN {var} v
          ON v.ms_id = r.id2 AND v.pass_id = :pass_id AND v.varnew !~ '^z'
        WHERE r.id2 NOT IN :exclude
        ORDER BY id1, affinity DESC)

        ORDER BY u, id1, affinity DESC, id2
        """, dict (parameters, nodes = tuple (G.nodes ()), exclude = tuple (exclude),
                   chapter = chapter, pass_id = passage.pass_id, prefix = prefix,
                   varnew = '^' + varnew, connectivity = connectivity, f_where = f_where))

        Ranks = collections.namedtuple ('Ranks', 'u ms_id1 ms_id2 rank affinity')
        ranks = list (map (Ranks._make, res))

        # Add nodes to the graph.  Add each node only once.
        nodes_seen = set ()
        for r in ranks:
            if not r.ms_id1 in nodes_seen:
                if r.rank > 1:
                    G.add_edge (r.ms_id2, r.ms_id1, rank = r.rank)
                else:
                    G.add_edge (r.ms_id2, r.ms_id1)
                nodes_seen.add (r.ms_id1)

        # Set the node labels.
        res = execute (conn, """
        SELECT ms.id, ms.hs, ms.hsnr, v.varid, v.varnew
        FROM {ms} ms
        JOIN {var} v
          ON ms.id = v.ms_id AND v.pass_id = :pass_id
        WHERE ms.id IN :ms_ids
        """, dict (parameters, ms_ids = tuple (G.nodes ()), pass_id = passage.pass_id))

        Mss = collections.namedtuple ('Mss', 'ms_id hs hsnr varid varnew')
        mss = list (map (Mss._make, res))
        for ms in mss:
            attrs = G.node[ms.ms_id]
            attrs['hs']     = ms.hs
            attrs['hsnr']   = ms.hsnr
            attrs['varid']  = ms.varid
            attrs['varnew'] = ms.varnew
            attrs['labez']  = ms.varnew[0]
            attrs['ms_id']  = ms.ms_id - 1
            attrs['label']  = ms.hs

        for n in G:
            # Use a different label if the parent's varnew differs from this
            # node's varnew.
            pred = G.predecessors (n)
            attrs = G.node[n]
            if not pred or attrs['varnew'] != G.node[pred[0]]['varnew']:
                attrs['label'] = "%s: %s" % (attrs['varnew'], attrs['hs'])
                if pred:
                    G.edge[pred[0]][n]['broken'] = True

    dot = nx_to_dot (G)
    dot = tools.graphviz_layout (dot)
    return flask.Response (dot, mimetype = 'text/vnd.graphviz')


@app.route('/coherence')
def coherence ():
    """The main page of the user interface.

    This page gets a hashtag parameter for the passage id.  All
    relevant content is loaded by ajax.

    """

    return flask.render_template ('coherence.html')


@app.route('/apparatus.json/<passage_or_id>')
def apparatus_json (passage_or_id):
    """ The contents of the apparatus table. """

    with current_app.config.dba.engine.begin () as conn:
        passage = Passage (conn, passage_or_id)

        # list of labez => lesart
        res = execute (conn, """
        SELECT labez, MODE () WITHIN GROUP (ORDER BY lesart) AS lesart
        FROM {att} a
        JOIN {pass} p
          ON (a.anfadr, a.endadr) = (p.anfadr, p.endadr)
        WHERE p.id = :pass_id
        GROUP BY p.id, labez
        """, dict (parameters, pass_id = passage.pass_id))

        # dict of labez: lesart
        readings = { row[0]: row[1] for row in res }
        for k in readings.keys ():
            if k in LABEZ_I18N:
                readings[k] = LABEZ_I18N[k]
        readings['zz'] = LABEZ_I18N['zz']

        # list of varnew => manuscripts
        res = execute (conn, """
        SELECT varid, varnew, ms_id - 1 as ms_id, hs, hsnr
        FROM {var}_view
        WHERE pass_id = :pass_id
        ORDER BY varnew, hsnr
        """, dict (parameters, pass_id = passage.pass_id))

        Manuscripts = collections.namedtuple ('Manuscripts', 'varid varnew ms_id hs hsnr')
        manuscripts = [ Manuscripts._make (r)._asdict () for r in res ]

        return flask.json.jsonify ({
            'readings'    : readings,
            'manuscripts' : manuscripts,
        })

    return 'Error'


@app.route('/attestation.json/<passage_or_id>')
def attestation_json (passage_or_id):

    with current_app.config.dba.engine.begin () as conn:
        passage = Passage (conn, passage_or_id)

        res = execute (conn, """
        SELECT ms_id, labez
        FROM {var}
        WHERE pass_id = :pass_id
        ORDER BY ms_id
        """, dict (parameters, pass_id = passage.pass_id))

        attestations = {}
        for row in res:
            ms_id, labez = row
            attestations[str(ms_id - 1)] = labez

        return flask.json.jsonify ({
            'attestations': attestations
        })


def local_stemma (passage_or_id):
    """Return a local stemma as nx graph."""

    with current_app.config.dba.engine.begin () as conn:
        passage = Passage (conn, passage_or_id)

        res = execute (conn, """
        SELECT varid, varnew, s1, s2
        FROM {locstemed} s
        WHERE s.varnew !~ '^z' AND pass_id = :pass_id
        ORDER BY varnew
        """, dict (parameters, pass_id = passage.pass_id))

        Variant = collections.namedtuple ('stemma_json_variant', 'varid, varnew, s1, s2')

        rows = list (map (Variant._make, res))

        G = nx.DiGraph ()

        for row in rows:
            G.add_node (row.varnew, label = row.varnew, labez = row.varid)
            if row.s1 != '*':
                G.add_edge (row.s1, row.varnew)
            if row.s2 and row.s2 != '*':
                G.add_edge (row.s2, row.varnew)

        # Add a '?' node because there is none in the database
        if [r for r in rows if r.s1 == '?' or r.s2 == '?']:
            G.add_node ('?', label = '?')

        return G


def nx_to_dot (nxg):
    """Convert an nx graph into a dot file.

    We'd like to sort the nodes in the graph, but nx internally uses
    dictionaries "all the way down".  Thus the only chance to sort nodes and
    edges is while writing the file.  This function is a lightweight
    re-implementation of nx.nx_pydot.to_pydot ().

    """

    dot = ["""strict digraph G {
        graph [dpi=100,
               nodesep=0.2,
               ordering=out,
               rankdir=BT,
               ranksep=0.4,
               size=10.0,
               ratio=compress
        ];
        node [fixedsize=shape,
              shape=circle,
              width=0.6
        ];
        edge [arrowhead=none,
              arrowtail=none,
              headclip=false,
              tailclip=false
        ];"""]

    # Copy nodes and sort them.  (Sorting nodes is important too.)
    for n, nodedata in sorted (nxg.nodes (data = True)):
        dot.append ("\"%s\" [%s];" %
                    (n, ','.join (["\"%s\"=\"%s\"" % (k, v) for k, v in nodedata.items ()])))

    # Copy edges and sort them.
    for u, v, edgedata in sorted (nxg.edges_iter (data = True)):
        dot.append ("\"%s\" -> \"%s\" [%s];" %
                    (u, v, ','.join (["\"%s\"=\"%s\"" % (k, v) for k, v in edgedata.items ()])))

    dot.append ('}\n')

    return '\n'.join (dot)


@app.route('/stemma.dot/<passage_or_id>')
def stemma_dot (passage_or_id):
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

    dot = nx_to_dot (local_stemma (passage_or_id))
    dot = tools.graphviz_layout (dot)
    return flask.Response (dot, mimetype = 'text/vnd.graphviz')


@app.route('/affinity.json')
def affinity_json ():
    """ Return manuscript affinities for D3.

    Returns manuscript affinities in a json format suitable for D3.js.

    """
    chapter = request.args.get ('chapter') or 0
    limit   = int (request.args.get ('limit') or 10)

    nodes = []
    edges = []

    with current_app.config.dba.engine.begin () as conn:

        res = execute (conn, """
        SELECT id, hs, hsnr, length
        FROM Manuscripts
        ORDER BY id
        """, {})

        # Every ms gets to be a node.
        for row in res:
            id_, hs, hsnr, length = row
            nodes.append ( {
                'ms_id'  : id_ - 1,
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

        res = execute (conn, """
        /* get the :limit closest relatives for every node */
        SELECT id1, id2, common, equal, rank
        FROM (
          SELECT id1, id2, common, equal, rank () OVER (PARTITION BY id1 ORDER BY affinity DESC) AS rank, affinity
          FROM {aff} a
          JOIN {chap} c
            ON a.id1 = c.ms_id AND a.chapter = c.chapter
          WHERE a.chapter = :chapter AND a.common >= c.length / 2 AND a.newer >= a.older
        ) AS r
        WHERE r.rank <= :limit
        ORDER BY id1, id2
        """, dict (parameters, limit = limit, chapter = chapter))

        for row in res:
            id1, id2, common, equal, rank = row

            edges.append ( {
                'source' : id1 - 1,
                'target' : id2 - 1,
                'common' : common,
                'equal'  : equal,
                'rank'   : rank
            } )

        return flask.json.jsonify ({
            'nodes': nodes,
            'links': edges
        })


if __name__ == "__main__":
    from werkzeug.wsgi import DispatcherMiddleware
    from werkzeug.serving import run_simple

    parser = argparse.ArgumentParser (description='An application server for CBGM')

    parser.add_argument ('-v', '--verbose', dest='verbose', action='count',
                         help='increase output verbosity', default=0)
    parser.add_argument ('-c', '--config-path', dest='config_path',
                         default=instance_path, metavar='CONFIG_PATH',
                         help="the directory where the config files reside (default='%s')" % instance_path)

    args = parser.parse_args (namespace = args)
    args.start_time = datetime.datetime.now ()
    parameters = tools.init_parameters (tools.DEFAULTS)

    babel = flask_babel.Babel ()
    babel.localeselector (get_locale)

    instances = collections.OrderedDict ()

    for fn in glob.glob (args.config_path.rstrip ('/') + '/*.conf'):
        sub_app = flask.Flask (__name__)
        sub_app.config.from_pyfile (fn)
        sub_app.register_blueprint (app) # , url_prefix = sub_app.config['APPLICATION_ROOT'])

        tools.message (3, "{name} at {path} from conf {conf}".format (
            name = sub_app.config['APPLICATION_NAME'],
            path = sub_app.config['APPLICATION_ROOT'],
            conf = fn), True)

        sub_app.config.dba = db.PostgreSQLEngine (
            host     = sub_app.config['PGHOST'],
            port     = sub_app.config['PGPORT'],
            database = sub_app.config['PGDATABASE'],
            user     = sub_app.config['PGUSER']
        )

        # tools.message (3, "URL Map {urlmap}".format (urlmap = sub_app.url_map))

        babel.init_app (sub_app)
        instances[sub_app.config['APPLICATION_ROOT']] = sub_app

    tools.message (3, "Found translations for: {translations}".format (
        translations = ', '.join ([l.get_display_name () for l in babel.list_translations ()])), True)

    dispatcher = DispatcherMiddleware (static_app, instances)
    run_simple ('127.0.0.1', 5000, dispatcher)
