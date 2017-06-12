#!/usr/bin/python3
# -*- encoding: utf-8 -*-

""" An application server for CBGM.  Helper classes. """

import collections
import csv
import datetime
import functools
import itertools
import math
import operator
import re
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
from flask_user import login_required
import flask_mail
import networkx as nx

from ntg_common.db import execute
from ntg_common import tools


parameters = dict ()


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
        return {
            'id'   : self.ms_id,
            'hs'   : self.hs,
            'hsnr' : self.hsnr,
        }


class Word (object):
    """ Represents one word address. """

    RE_HR_WORD = re.compile (r'^(?:(\w+)\s+)?(?:(\d+):)?(?:(\d+)/)?(\d+)$')

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
        s = Word (self.start)
        hr = self.to_hr ()
        return {
            'id'       : self.pass_id,
            'hr'       : hr,
            'start'    : str (self.start),
            'end'      : str (self.end),
            'passage'  : self.to_passage (),
            'chapter'  : str (self.chapter),
            'verse'    : s.verse,
            'word'     : hr.split ('/', 1)[1],
            'variants' : self.variants (),
            'splits'   : self.splits (),
        }


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


    def splits (self, prefix = [], suffix = [], delete = []):
        # Get a list of all split-variants for this passage

        res = execute (self.conn, """
        SELECT DISTINCT varnew
        FROM {locstemed}
        WHERE pass_id = :pass_id
        ORDER BY varnew
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
            d[k] = LABEZ_I18N.get (d[k][0], d[k])

        Variants = collections.namedtuple ('Splits', 'split split_i18n')
        return list (map (Variants._make, ((k, v) for k, v in d.items ())))


def get_locale ():
    return flask.request.accept_languages.best_match ('en')
    # return flask.request.accept_languages.best_match (LANGUAGES.keys ())


def make_json_response (json = None, status = 200, message = None):
    d = dict (status = status)
    if json:
        d['data'] = json
    if message:
        d['message'] = message
    return flask.make_response (flask.json.jsonify (d), status)


DOT_SKELETON = """
strict digraph G {{
        graph [nodesep={nodesep},
               ordering=out,
               rankdir=TB,
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
        edge [arrowhead=normal,
              arrowtail=none,
              labelangle=-15.0,
              labeldistance=2.0,
        ];
"""

def clip (lo, x, hi):
    return max (lo, min (hi, x))


def dot_skeleton (width = 960.0, fontsize = 10.0, ranksep = 0.4, nodesep = 0.1):
    # We have to convert the values the browser sends (96 dpi) into
    # values that GraphViz accepts (72 dpi).

    # Why dpi = 96 ? See: https://www.w3.org/TR/css3-values/#reference-pixel

    # All input to GraphViz assumes 72pt = 1 inch and 72 dpi regardless of the
    # value of dpi. dpi is used only for bitmap and svg output.

    # sanitize input
    width    = clip (10.0, width,   1600.0)
    fontsize = clip ( 6.0, fontsize,  72.0)
    ranksep  = clip ( 0.0, ranksep,   10.0)
    nodesep  = clip ( 0.0, nodesep,   10.0)

    return [DOT_SKELETON.format (
        ranksep = ranksep,
        nodesep = nodesep,
        size = width / 96,               # convert px => inch
        fontsize = (fontsize / 96) * 72  # convert px => pt (72 pt = 1 inch)
    )]


def nx_to_dot (nxg, width = 960.0, fontsize = 10.0, nodesep = 0.1):
    """Convert an nx graph into a dot file.

    We'd like to sort the nodes in the graph, but nx internally uses
    dictionaries "all the way down".  Thus the only chance to sort nodes and
    edges is while writing the file.  This function is a lightweight
    re-implementation of nx.nx_pydot.to_pydot ().

    """

    dot = dot_skeleton (width = width, fontsize = fontsize, nodesep = nodesep);

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
        dot.append ("style=rounded")
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


def local_stemma_to_nx (conn, passage):
    """ Load a passage fron the database into an nx Graph. """

    res = execute (conn, """
    SELECT varid, varnew, s1, s2
    FROM {locstemed} s
    WHERE s.varnew !~ '^z' AND pass_id = :pass_id
    ORDER BY varnew
    """, dict (parameters, pass_id = passage.pass_id))

    Variant = collections.namedtuple ('stemma_json_variant', 'varid, varnew, s1, s2')

    rows = list (map (Variant._make, res))

    G = nx.DiGraph ()

    # Add '*' and '?' nodes because there are none in the database
    G.add_node ('*', label = '*', varnew = '*')
    G.add_node ('?', label = '?', varnew = '?')

    for row in rows:
        G.add_node (row.varnew, label = row.varnew, labez = row.varid, varnew = row.varnew)
        G.add_edge (row.s1, row.varnew)
        if row.s2:
            G.add_edge (row.s2, row.varnew)

    return G
