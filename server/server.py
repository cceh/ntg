#!/usr/bin/python3
# -*- encoding: utf-8 -*-

"""An application server for CBGM."""

import argparse
import collections
import csv
import datetime
import glob
import io
import itertools
import math
import operator
import re
import sys
import os
import os.path

import flask
from flask import request, current_app
import flask_babel
from flask_babel import gettext as _, ngettext as n_, lazy_gettext as l_
import networkx as nx

sys.path.append (os.path.abspath (os.path.dirname (__file__) + '/..'))

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

    RE_HSNR = re.compile (r'^\d{6}$')             # 123456
    RE_MSID = re.compile (r'^\d+$')               # 123
    RE_HS   = re.compile (r'^[PL]?[s\d]+[.]?$|^A$|^MT$')   # 01.

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


    def to_json (self):
        return flask.json.jsonify ({
            'id'   : self.ms_id,
            'hs'   : self.hs,
            'hsnr' : self.hsnr,
        })


class Word (object):
    """ Represents one word address. """

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
        if m:
            self.book    = 5 # FIXME parse m.group (1)
            self.chapter = int (m.group (2) or '0')
            self.verse   = int (m.group (3) or '0')
            self.word    = int (m.group (4) or '0')
        return self


    def format (self, start = None):
        # Format a word to the format: "Acts 1:2/3-4"
        if start is None:
            return "%s %d:%d/%d" % (tools.BOOKS[self.book - 1][1], self.chapter, self.verse, self.word)

        if start.book != self.book:
            return " - %s %d:%d/%d" % (tools.BOOKS[self.book - 1], self.chapter, self.verse, self.word)
        if start.chapter != self.chapter:
            return " - %d:%d/%d" % (self.chapter, self.verse, self.word)
        if start.verse != self.verse:
            return " - %d/%d" % (self.verse, self.word)
        if start.word != self.word:
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


    @staticmethod
    def _to_hr (start, end):
        # return passage in human-readable format
        s = Word (start)
        if start == end:
            return s.format ()
        e = Word (end)
        return s.format () + e.format (s)


    def to_hr (self):
        # return passage in human-readable format
        return Passage._to_hr (self.start, self.end)


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


DOT_SKELETON = """
strict digraph G {{
        graph [nodesep=0.1,
               ordering=out,
               rankdir=BT,
               ranksep={ranksep},
               size={size:.2f},
               fontname="LiberationSans-Regular", // like Arial
               fontsize={fontsize},
               remincross=true
        ];
        node [shape=ellipse,
              height=0.3,
              width=0.3,
              margin=0.005
        ];
        edge [arrowhead=none,
              arrowtail=none,
              headclip=true,
              tailclip=true,
              labelangle=0.0,
              labeldistance=1.5,
        ];
"""

def dot_skeleton (width = 960.0, fontsize = 10.0, ranksep = 0.4):
    # We have to convert the values the browser sends (96 dpi) into
    # values that GraphViz accepts (72 dpi).

    # Why dpi = 96 ? See: https://www.w3.org/TR/css3-values/#reference-pixel

    # All input to GraphViz assumes 72pt = 1 inch and 72 dpi regardless of the
    # value of dpi. dpi is used only for bitmap and svg output.

    return [DOT_SKELETON.format (
        ranksep = ranksep,
        size = width / 96,               # convert px => inch
        fontsize = (fontsize / 96) * 72  # convert px => pt (72 pt = 1 inch)
    )]


def nx_to_dot (nxg, width = 960.0, fontsize = 10.0):
    """Convert an nx graph into a dot file.

    We'd like to sort the nodes in the graph, but nx internally uses
    dictionaries "all the way down".  Thus the only chance to sort nodes and
    edges is while writing the file.  This function is a lightweight
    re-implementation of nx.nx_pydot.to_pydot ().

    """

    dot = dot_skeleton (width = width, fontsize = fontsize);

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


def nx_to_dot_subgraphs (nxg, field, width = 960.0, fontsize = 10.0):
    """Convert an nx graph into a dot file.

    We'd like to sort the nodes in the graph, but nx internally uses
    dictionaries "all the way down".  Thus the only chance to sort nodes and
    edges is while writing the file.  This function is a lightweight
    re-implementation of nx.nx_pydot.to_pydot ().

    """

    dot = dot_skeleton (width = width, fontsize = fontsize, ranksep = 1.2);

    # Copy nodes and sort them.  (Sorting nodes is important too.)
    sorted_nodes = sorted (nxg, key = lambda n: (nxg.node[n][field], nxg.node[n]['hsnr']))
    for key, nodes_for_key in itertools.groupby (sorted_nodes, key = lambda n: nxg.node[n][field]):
        dot.append ("subgraph cluster_%s {" % key)
        dot.append ("labeljust=l")
        dot.append ("labelloc=c")
        dot.append ("rank=%s" % ('source' if key in ('a', 'a1') else 'same'))
        dot.append ("label=%s" % key)
        for n in nodes_for_key:
            attr = nxg.node[n]
            dot.append ("\"%s\" [%s];" %
                        (n, ','.join (["\"%s\"=\"%s\"" % (k, v) for k, v in attr.items ()])))
        dot.append ("}")

    # Copy edges and sort them.
    for u, v, edgedata in sorted (nxg.edges_iter (data = True)):
        dot.append ("\"%s\" -> \"%s\" [%s];" %
                    (u, v, ','.join (["\"%s\"=\"%s\"" % (k, v) for k, v in edgedata.items ()])))

    dot.append ('}\n')

    return '\n'.join (dot)


@static_app.endpoint ('index')
def index ():
    return flask.render_template ('index.html')


@app.endpoint ('links')
def links ():
    return flask.render_template ('links.html')


@app.endpoint ('passage.json')
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


@app.endpoint ('chapters.json')
def chapters_json ():

    with current_app.config.dba.engine.begin () as conn:
        res = execute (conn, """
        SELECT DISTINCT chapter, chapter
        FROM {chap}
        WHERE chapter > 0
        ORDER BY chapter
        """, parameters)

        Chapters = collections.namedtuple ('Chapters', 'chapter i18n')
        chapters = list (map (Chapters._make, res))
        # chapters = [ Chapters._make (r)._asdict () for r in res ]

        return flask.json.jsonify ({
            'chapters' : chapters,
        })


@app.endpoint ('manuscript.json')
def manuscript_json (hs_hsnr_id):

    hs_hsnr_id = request.args.get ('ms_id') or hs_hsnr_id

    with current_app.config.dba.engine.begin () as conn:
        ms = Manuscript (conn, hs_hsnr_id)
        return ms.to_json ()


@app.endpoint ('ms_attesting')
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


@app.endpoint ('relatives')
def relatives (hs_hsnr_id, passage_or_id):
    """The relatives popup skeleton.

    A convenience method that serves an empty skeleton for the relatives popup.

    """

    chapter = request.args.get ('chapter') or 0
    caption = _('Relatives for')

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

    # convert tuples to lists
    return flask.render_template ('relatives-skeleton.html', caption = caption, ms = ms, mt = mt)


@app.endpoint ('relatives.json')
def relatives_json (hs_hsnr_id, passage_or_id):
    """Output a table of the nearest relatives of a manuscript.

    Output a table of the nearest relatives/ancestors/descendants of a
    manuscript and what they attest.

    """

    type_     = request.args.get ('type') or 'rel'
    chapter   = request.args.get ('chapter') or 0
    limit     = int (request.args.get ('limit') or 10)
    labez     = request.args.get ('labez') or 'all'
    mode      = request.args.get ('mode') or 'rec'
    include   = request.args.getlist ('include[]') or []
    fragments = request.args.getlist ('fragments[]') or []

    caption = _('Relatives for')
    where = ''
    if type_ == 'anc':
        where =  ' AND older <= newer'
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

        return flask.render_template ('relatives.html', mt = mt, rows = relatives)


def remove_z_leaves (G, group_field):
    """ Removes leaves (recursively) if they read z. """

    for n in nx.topological_sort (G, reverse = True):
        atts = G.node[n]
        if G.out_degree (n) == 0 and group_field in atts and atts[group_field][0] == 'z':
            G.remove_node (n)


@app.endpoint ('textflow.dot')
def textflow_dot (passage_or_id):
    """ Output a stemma of manuscripts. """

    varnew       = request.args.get ('labez') or ''
    hyp_a        = request.args.get ('hyp_a')  or 'A'
    chapter      = request.args.get ('chapter') or 0
    connectivity = int (request.args.get ('connectivity') or 10)
    width        = float (request.args.get ('width') or 0.0)
    fontsize     = float (request.args.get ('fontsize') or 10.0)
    mode         = request.args.get ('mode') or 'rec'

    include      = set (request.args.getlist ('include[]') or ['NONE'])
    fragments    = request.args.getlist ('fragments[]') or []
    var_only     = request.args.getlist ('var_only[]')  or []
    splits       = request.args.getlist ('splits[]')    or []

    fragments = 'fragments' in fragments
    var_only  = 'var_only'  in var_only
    splits    = 'splits'    in splits
    show_z    = 'Z'         in include

    prefix = '' if mode == 'rec' else 'p_'
    if connectivity == 21:
        connectivity = 9999

    if fragments:
        f_where = ''
    else:
        f_where = 'AND a.common > c.length / 2'

    varnew_where = ''
    if varnew != '':
        varnew_where = 'AND v.varnew ~ :varnew'
        if hyp_a != 'A':
            varnew_where = 'AND (v.varnew ~ :varnew OR (v.ms_id = 1 AND :hyp_a ~ :varnew))'

    group_field = 'varnew' if splits else 'varid'

    with current_app.config.dba.engine.begin () as conn:
        passage = Passage (conn, passage_or_id)

        G = nx.DiGraph ()

        Nodes = collections.namedtuple ('Nodes', 'ms_id')

        # get ids of nodes to exclude
        res = execute (conn, """
        SELECT id
        FROM {ms}
        WHERE (hs IN ('A', 'MT')) AND (hs NOT IN :include)
        ORDER BY id
        """, dict (parameters, include = tuple (include)))

        exclude = set ([str (n.ms_id) for n in map (Nodes._make, res)])
        exclude.add (-1) # a non-existing id to avoid SQL syntax error if empty

        # get all nodes or all nodes (hypothetically) attesting varnew
        res = execute (conn, """
        SELECT ms_id
        FROM {var} v
        WHERE pass_id = :pass_id {varnew_where} AND ms_id NOT IN :exclude
        """, dict (parameters, exclude = tuple (exclude),
                   pass_id = passage.pass_id, varnew = '^' + varnew,
                   hyp_a = hyp_a, varnew_where = varnew_where))

        nodes = list (map (Nodes._make, res))

        for n in nodes:
            G.add_node (n.ms_id)

        order = 'affinity DESC, common, older, newer DESC, id2' # id2 is a tiebreaker

        # query to get the closest ancestors for every node with rank <= connectivity
        query = """
        SELECT id1, id2, rank
        FROM (
          SELECT id1, id2, rank () OVER (PARTITION BY id1 ORDER BY {order}) AS rank
          FROM {aff} a
          JOIN {chap} c
            ON c.ms_id = a.id1 AND c.chapter = a.chapter
          WHERE id1 IN :nodes AND a.chapter = :chapter AND id2 NOT IN :exclude
            AND {prefix}newer > {prefix}older AND a.common > c.length / 2
        ) AS r
        WHERE rank <= :connectivity
        ORDER BY rank
        """

        global_textflow = not ((varnew != '') or var_only)
        if global_textflow:
            connectivity = 1

        res = execute (conn, query,
                       dict (parameters, nodes = tuple (G.nodes ()), exclude = tuple (exclude),
                             chapter = chapter, pass_id = passage.pass_id, prefix = prefix,
                             varnew = '^' + varnew, connectivity = connectivity, order = order,
                             f_where = f_where, hyp_a = hyp_a, varnew_where = varnew_where))

        Ranks = collections.namedtuple ('Ranks', 'ms_id1 ms_id2 rank')
        ranks = list (map (Ranks._make, res))

        # Initially build a graph with all nodes.  We will remove unused nodes
        # later.
        dest_nodes = set ([r.ms_id1 for r in ranks])
        src_nodes  = set ([r.ms_id2 for r in ranks])

        res = execute (conn, """
        SELECT ms.id, ms.hs, ms.hsnr, v.varid, v.varnew
        FROM {ms} ms
        JOIN {var} v
          ON ms.id = v.ms_id AND v.pass_id = :pass_id
        WHERE ms.id IN :ms_ids
        """, dict (parameters, ms_ids = tuple (src_nodes | dest_nodes), pass_id = passage.pass_id))

        Mss = collections.namedtuple ('Mss', 'ms_id hs hsnr varid varnew')
        mss = list (map (Mss._make, res))
        for ms in mss:
            attrs = {}
            attrs['hs']     = ms.hs
            attrs['hsnr']   = ms.hsnr
            attrs['varid']  = ms.varid
            attrs['varnew'] = ms.varnew
            attrs['labez']  = ms.varnew[0]
            attrs['ms_id']  = ms.ms_id - 1
            attrs['label']  = ms.hs
            if ms.ms_id == 1 and hyp_a != 'A':
                attrs['varid']  = hyp_a[0]
                attrs['varnew'] = hyp_a
                attrs['labez']  = hyp_a[0]
            G.add_node (ms.ms_id, attrs)

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

        G.remove_nodes_from (nx.isolates (G))

        if var_only:
            # Remove non-variant links
            #
            # remove nodes attesting z and link the children up
            for n in G:
                if G.node[n][group_field][0] == 'z':
                    pred = G.predecessors (n)
                    if pred:
                        G.remove_edge (pred[0], n)
                    for succ in G.successors (n):
                        G.remove_edge (n, succ)
                        if pred:
                            G.add_edge (pred[0], succ)

            # remove a node's other edges if one edge is within attestation
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
            for u, v in G.edges ():
                if G.node[u][group_field] == G.node[v][group_field]:
                    G.remove_edge (u, v)

            # remove now isolated nodes
            G.remove_nodes_from (nx.isolates (G))

            # unconstrain backward edges
            for u, v in G.edges ():
                if G.node[u][group_field] > G.node[v][group_field]:
                    G.edge[u][v]['constraint'] = 'false'

        else:
            for n in G:
                # Use a different label if the parent's varnew differs from this
                # node's varnew.
                pred = G.predecessors (n)
                attrs = G.node[n]
                if not pred:
                    attrs['label'] = "%s: %s" % (attrs['varnew'], attrs['hs'])
                for p in pred:
                    if attrs['varnew'] != G.node[p]['varnew']:
                        attrs['label'] = "%s: %s" % (attrs['varnew'], attrs['hs'])
                        G.edge[p][n]['broken'] = 'true'

    if var_only:
        dot = nx_to_dot_subgraphs (G, group_field, width, fontsize)
    else:
        dot = nx_to_dot (G, width, fontsize)
    dot = tools.graphviz_layout (dot)
    return flask.Response (dot, mimetype = 'text/vnd.graphviz')


def csvify (fields, rows):
    fp = io.StringIO ()
    writer = csv.DictWriter (fp, fields, restval='', extrasaction='raise', dialect='excel')
    writer.writeheader ()
    for r in rows:
        writer.writerow (r._asdict ())
    return flask.Response (fp.getvalue (), mimetype = 'text/csv')


@app.endpoint ('coherence')
def coherence ():
    """The main page of the user interface.

    This page gets a hashtag parameter for the passage id.  All
    relevant content is loaded by ajax.

    """

    return flask.render_template ('coherence.html')


@app.endpoint ('comparison')
def comparison ():
    """ Comparison of 2 witnesses. """

    with current_app.config.dba.engine.begin () as conn:
        ms1 = Manuscript (conn, request.args.get ('ms1') or 'A')
        ms2 = Manuscript (conn, request.args.get ('ms2') or 'A')

        return flask.render_template ('comparison.html', ms1 = ms1, ms2 = ms2)


ComparisonRow = collections.namedtuple (
    'Comparison', 'chapter, common, equal, older, newer, unclear, affinity, rank')


ComparisonDetailRow = collections.namedtuple (
    'ComparisonDetailRow',
    'pass_id anfadr endadr var1 mask1 anc1 par1 lesart1 var2 mask2 anc2 par2 lesart2'
)

class ComparisonDetailRowCalcFields (ComparisonDetailRow):
    __slots__ = ()

    _fields = ComparisonDetailRow._fields + ('pass_hr', )

    @property
    def pass_hr (self):
        return Passage._to_hr (self.anfadr, self.endadr)

    def _asdict (self):
        return collections.OrderedDict (zip (self._fields, self + (self.pass_hr, )))


def _comparison ():
    """ Comparison of 2 witnesses. Returns CSV. """

    with current_app.config.dba.engine.begin () as conn:
        ms1 = Manuscript (conn, request.args.get ('ms1') or 'A')
        ms2 = Manuscript (conn, request.args.get ('ms2') or 'A')

        res = execute (conn, """
        (WITH ranks AS (
          SELECT id1, id2, aff.chapter, rank () OVER (PARTITION BY aff.chapter ORDER BY affinity DESC) AS rank, affinity
          FROM {aff} aff
          JOIN {chap} ch
            ON ch.ms_id = aff.id1 AND ch.chapter = aff.chapter
          WHERE id1 = :ms_id1
            AND {prefix}newer > {prefix}older AND aff.common > ch.length / 2
          ORDER BY affinity DESC
        )

        SELECT a.chapter, a.common, a.equal,
               a.{prefix}older, a.{prefix}newer, a.{prefix}unclear, a.affinity, r.rank
        FROM {aff} a
        JOIN ranks r
          ON r.id1 = a.id1 AND r.id2 = a.id2 AND r.chapter = a.chapter
        WHERE a.id1 = :ms_id1 AND a.id2 = :ms_id2
        )

        UNION

        (WITH ranks2 AS (
          SELECT id1, id2, aff.chapter, rank () OVER (PARTITION BY aff.chapter ORDER BY affinity DESC) AS rank, affinity
          FROM {aff} aff
          JOIN {chap} ch
            ON ch.ms_id = aff.id2 AND ch.chapter = aff.chapter
          WHERE id2 = :ms_id2
            AND {prefix}newer < {prefix}older AND aff.common > ch.length / 2
          ORDER BY affinity DESC
        )

        SELECT a.chapter, a.common, a.equal,
               a.{prefix}older, a.{prefix}newer, a.{prefix}unclear, a.affinity, r.rank
        FROM {aff} a
        JOIN ranks2 r
          ON r.id1 = a.id1 AND r.id2 = a.id2 AND r.chapter = a.chapter
        WHERE a.id1 = :ms_id1 AND a.id2 = :ms_id2
        )

        UNION

        SELECT a.chapter, a.common, a.equal,
               a.{prefix}older, a.{prefix}newer, a.{prefix}unclear, a.affinity, NULL
        FROM {aff} a
        WHERE a.id1 = :ms_id1 AND a.id2 = :ms_id2 AND a.{prefix}newer = a.{prefix}older

        ORDER BY chapter
        """, dict (parameters, ms_id1 = ms1.ms_id + 1, ms_id2 = ms2.ms_id + 1, prefix = 'p_'))

        return list (map (ComparisonRow._make, res))


def _comparison_detail ():
    """Comparison of 2 witnesses, chapter detail"""

    with current_app.config.dba.engine.begin () as conn:
        ms1 = Manuscript (conn, request.args.get ('ms1') or 'A')
        ms2 = Manuscript (conn, request.args.get ('ms2') or 'A')
        chapter = request.args.get ('chapter') or 0

        res = execute (conn, """
        SELECT p.id, p.anfadr, p.endadr,
          v1.varnew, l1.varnewmask, l1.ancestors, l1.parents, r1.lesart,
          v2.varnew, l2.varnewmask, l2.ancestors, l2.parents, r2.lesart
        FROM (SELECT * FROM {pass} WHERE kapanf = :chapter) p
          JOIN {var} v1 ON v1.pass_id = p.id AND v1.ms_id = :ms1
          JOIN {var} v2 ON v2.pass_id = p.id AND v2.ms_id = :ms2
          JOIN {locstemed} l1 ON l1.pass_id = p.id AND l1.varnew = v1.varnew
          JOIN {locstemed} l2 ON l2.pass_id = p.id AND l2.varnew = v2.varnew
          JOIN {read} r1 ON r1.pass_id = p.id AND r1.labez = v1.labez AND r1.labezsuf = v1.labezsuf
          JOIN {read} r2 ON r2.pass_id = p.id AND r2.labez = v2.labez AND r2.labezsuf = v2.labezsuf
        WHERE v1.varnew != v2.varnew AND v1.varnew !~ '^z' AND v2.varnew !~ '^z'
        ORDER BY p.id
        """, dict (parameters, ms1 = ms1.ms_id + 1, ms2 = ms2.ms_id + 1, chapter = chapter))

        return list (map (ComparisonDetailRowCalcFields._make, res))


@app.endpoint ('comparison.csv')
def comparison_csv ():
    return csvify (ComparisonRow._fields, _comparison ())


@app.endpoint ('comparison-detail.csv')
def comparison_detail_csv ():
    # tools.log (logging.INFO, ComparisonDetailRow._source)
    return csvify (ComparisonDetailRowCalcFields._fields, _comparison_detail ())


@app.endpoint ('apparatus.json')
def apparatus_json (passage_or_id):
    """ The contents of the apparatus table. """

    with current_app.config.dba.engine.begin () as conn:
        passage = Passage (conn, passage_or_id)

        Readings    = collections.namedtuple ('Readings',    'labez labezsuf lesart')
        Manuscripts = collections.namedtuple ('Manuscripts', 'varid varnew labez labezsuf ms_id hs hsnr')

        # list of labez, labezsuf => lesart
        res = execute (conn, """
        SELECT labez, labezsuf, lesart
        FROM {read}
        WHERE pass_id = :pass_id
        ORDER BY labez, labezsuf
        """, dict (parameters, pass_id = passage.pass_id))

        def i18n (d):
            if d['labez'] in LABEZ_I18N:
                d['lesart'] = LABEZ_I18N[d['labez']]
            return d

        readings = [ i18n (Readings._make (r)._asdict ()) for r in res ]

        for k in LABEZ_I18N:
            readings.append ({ 'labez': k, 'labezsuf': '', 'lesart': LABEZ_I18N[k] });


        # list of varnew => manuscripts
        res = execute (conn, """
        SELECT varid, varnew, labez, labezsuf, ms_id - 1 as ms_id, hs, hsnr
        FROM {var}_view
        WHERE pass_id = :pass_id
        ORDER BY varnew, labezsuf, hsnr
        """, dict (parameters, pass_id = passage.pass_id))

        manuscripts = [ Manuscripts._make (r)._asdict () for r in res ]

        return flask.json.jsonify ({
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


@app.endpoint ('stemma.dot')
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

    width    = float (request.args.get ('width') or 0.0)
    fontsize = float (request.args.get ('fontsize') or 10.0)

    dot = nx_to_dot (local_stemma (passage_or_id), width, fontsize)
    dot = tools.graphviz_layout (dot)
    return flask.Response (dot, mimetype = 'text/vnd.graphviz')


@app.endpoint ('affinity.json')
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
    parameters = tools.init_parameters (tools.DEFAULTS)

    babel = flask_babel.Babel ()
    babel.localeselector (get_locale)

    logging.basicConfig (format = '%(asctime)s - %(levelname)s - %(message)s')
    logging.getLogger ('sqlalchemy.engine').setLevel (args.log_level)
    logging.getLogger ('server').setLevel (args.log_level)

    instances = collections.OrderedDict ()

    static_app.url_map.add (Rule ('/', endpoint = 'index'))

    for fn in glob.glob (args.config_path.rstrip ('/') + '/*.conf'):
        sub_app = flask.Flask (__name__)
        sub_app.logger.setLevel (args.log_level)
        sub_app.config.from_pyfile (fn)
        sub_app.config['server_start_time'] = str (int (args.start_time.timestamp ()))
        sub_app.register_blueprint (app)

        sub_app.url_map = Map ([
            Rule ('/',                                         endpoint = 'links'),
            Rule ('/coherence',                                endpoint = 'coherence'),
            Rule ('/comparison',                               endpoint = 'comparison'),
            Rule ('/comparison.csv',                           endpoint = 'comparison.csv'),
            Rule ('/comparison-detail.csv',                    endpoint = 'comparison-detail.csv'),
            Rule ('/affinity.json',                            endpoint = 'affinity.json'),
            Rule ('/chapters.json',                            endpoint = 'chapters.json'),
            Rule ('/manuscript.json/<hs_hsnr_id>',             endpoint = 'manuscript.json'),
            Rule ('/passage.json/<passage_or_id>',             endpoint = 'passage.json'),
            Rule ('/ms_attesting/<passage_or_id>/<labez>',     endpoint = 'ms_attesting'),
            Rule ('/relatives/<passage_or_id>/<hs_hsnr_id>',   endpoint = 'relatives'),
            Rule ('/relatives.json/<passage_or_id>/<hs_hsnr_id>', endpoint = 'relatives.json'),
            Rule ('/apparatus.json/<passage_or_id>',           endpoint = 'apparatus.json'),
            Rule ('/attestation.json/<passage_or_id>',         endpoint = 'attestation.json'),
            Rule ('/stemma.dot/<passage_or_id>',               endpoint = 'stemma.dot'),
            Rule ('/textflow.dot/<passage_or_id>',             endpoint = 'textflow.dot'),
        ])

        tools.log (logging.INFO, "{name} at {path} from conf {conf}".format (
            name = sub_app.config['APPLICATION_NAME'],
            path = sub_app.config['APPLICATION_ROOT'],
            conf = fn))

        sub_app.config.dba = db.PostgreSQLEngine (**sub_app.config)

        # tools.log (logging.DEBUG, "URL Map {urlmap}".format (urlmap = sub_app.url_map))

        babel.init_app (sub_app)
        instances[sub_app.config['APPLICATION_ROOT']] = sub_app

    tools.log (logging.INFO, "Found translations for: {translations}".format (
        translations = ', '.join ([l.get_display_name () for l in babel.list_translations ()])))

    dispatcher = DispatcherMiddleware (static_app, instances)
    run_simple ('localhost', 5000, dispatcher)
