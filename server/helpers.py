#!/usr/bin/python3
# -*- encoding: utf-8 -*-

""" An application server for CBGM.  Helper classes. """

import collections
import itertools
import re
import os
import os.path

import flask
import flask_login

from ntg_common import tools
from ntg_common.db_tools import execute, to_csv


parameters = dict ()


LANGUAGES = {
    'en': 'English',
    'de': 'Deutsch'
}


LABEZ_I18N = {
    'zu':      'Overlap',
    'zv':      'Lac',
    'zw':      'Dubious',
    'zz':      'Lac',
    'lac':     'Lac',
    'all':     'All',
    'all+lac': 'All+Lac',
}


EXCLUDE_REGEX_MAP = {
    'A'  : 'A',
    'MT' : 'MT',
    'F'  : 'F[1-9Π][0-9]*'
}
""" Regexes for the include/exclude toolbar buttons. """


def get_excluded_ms_ids (conn, include):
    """Get the ms_ids of manuscripts to exclude.

    Helps to implement the buttons "A", "MT", and "F" in the toolbar.

    """

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


class Bag ():
    """ Class to stick values in. """


class Manuscript ():
    """ Represent one manuscript. """

    RE_HSNR = re.compile (r'^\d{6}$')             # 300180
    RE_MSID = re.compile (r'^id\d+$')             # id123
    RE_HS   = re.compile (r'^([PL]?[s\d]+|A|MT)$', re.I)   # 01.

    def __init__ (self, conn, manuscript_id_or_hs_or_hsnr):
        """ Initialize from manuscript id or hs or hsnr. """

        self.conn = conn
        self.ms_id = self.hs = self.hsnr = None
        param = manuscript_id_or_hs_or_hsnr

        if Manuscript.RE_HSNR.search (param):
            where = 'hsnr = :param'
            param = int (param)
        elif Manuscript.RE_MSID.search (param):
            where = 'ms_id = :param'
            param = int (param[2:])
        elif Manuscript.RE_HS.search (param):
            where = 'hs = :param'
        else:
            return

        res = execute (conn, """
        SELECT ms_id, hs, hsnr
        FROM manuscripts
        WHERE {where}
        """, dict (parameters, where = where, param = param))

        self.ms_id, self.hs, self.hsnr = res.first ()


    def get_length (self, rg_id):
        # Get the length of the manuscript, ie. the no. of existing passages

        res = execute (self.conn, """
        SELECT length
        FROM ms_ranges
        WHERE ms_id = :ms_id AND rg_id = :rg_id
        """, dict (parameters, ms_id = self.ms_id, rg_id = rg_id))

        return res.fetchone ()[0]


    def to_json (self):
        return {
            'ms_id'  : self.ms_id,
            'hs'     : self.hs,
            'hsnr'   : self.hsnr,
        }


class Word ():
    """ Represents one word address. """

    RE_HR_WORD = re.compile (r'^(?:(\d?\w+)\s+)?(?:(\d+):)?(?:(\d+)/)?(\d+)$')

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
        # Parse an address from the format: "Act 1:2/3-4"
        m = Word.RE_HR_WORD.match (s)
        if m:
            self.book = 0
            if m.group (1):
                bk = m.group (1).lower ()
                books = [book for book in enumerate (tools.BOOKS)
                         if book[1][1].lower () == bk or book[1][2].lower () == bk]
                self.book = books[0][0] + 1
            self.chapter = int (m.group (2) or '0')
            self.verse   = int (m.group (3) or '0')
            self.word    = int (m.group (4) or '0')
        return self


    def format (self, start = None):
        # Format a word to the format: "Acts 1:2/3-4"
        if start is None:
            return "%s %d:%d/%d" % (
                tools.BOOKS[self.book - 1][1], self.chapter, self.verse, self.word)

        if start.book != self.book:
            return " - %s %d:%d/%d" % (
                tools.BOOKS[self.book - 1][1], self.chapter, self.verse, self.word)
        if start.chapter != self.chapter:
            return " - %d:%d/%d" % (self.chapter, self.verse, self.word)
        if start.verse != self.verse:
            return " - %d/%d" % (self.verse, self.word)
        if start.word != self.word:
            return "-%d" % self.word
        return ""


class Passage ():
    """ Represents one passage. """

    def __init__ (self, conn, passage_or_id):
        """ Initialize from passage or passage id. """

        self.conn = conn
        self.pass_id, self.start, self.end, self.bk_id, self.chapter = 0, 0, 0, 0, 0
        start, end =  self.fix (str (passage_or_id))

        if int (start) > 10000000:
            res = execute (conn, """
            SELECT pass_id, begadr, endadr, adr2bk_id (begadr), adr2chapter (begadr)
            FROM passages
            WHERE begadr = :begadr AND endadr = :endadr
            """, dict (parameters, begadr = start, endadr = end))
        else:
            res = execute (conn, """
            SELECT pass_id, begadr, endadr, adr2bk_id (begadr), adr2chapter (begadr)
            FROM passages
            WHERE pass_id = :pass_id
            """, dict (parameters, pass_id = start))

        res = res.first ()
        if res is not None:
            self.pass_id, self.start, self.end, self.bk_id, self.chapter = res


    @staticmethod
    def static_to_hr (start, end):
        # return passage in human-readable format
        s = Word (start)
        if start == end:
            return s.format ()
        e = Word (end)
        return s.format () + e.format (s)


    def to_hr (self):
        # return passage in human-readable format
        return Passage.static_to_hr (self.start, self.end)


    def to_json (self):
        s = Word (self.start)
        hr = self.to_hr ()
        bk = tools.BOOKS[self.bk_id - 1]
        return {
            'pass_id'  : self.pass_id,
            'hr'       : hr,
            'start'    : str (self.start),
            'end'      : str (self.end),
            'passage'  : self.to_passage (),
            'bk_id'    : self.bk_id,
            'rg_id'    : self.range_id (),
            'siglum'   : bk[1],
            'book'     : bk[2],
            'chapter'  : str (self.chapter),
            'verse'    : s.verse,
            'word'     : hr.split ('/', 1)[1],
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


    def range_id (self, range_ = None):
        """ Return the id of the range containing this passage. """

        range_ = range_ or str (self.chapter)

        res = execute (self.conn, """
        SELECT rg_id
        FROM ranges_view
        WHERE bk_id = :bk_id AND range = :range_
        """, dict (parameters, bk_id = self.bk_id, range_ = range_))

        res = res.first ()
        return res[0] if res is not None else None


    def request_rg_id (self, request):
        return int (request.args.get ('rg_id', 0)) or self.range_id ('All')


    def to_passage (self):
        # get a passage id in the form "start-end"
        if self.start == self.end:
            return str (self.start)
        common = len (os.path.commonprefix ((str (self.start), str (self.end))))
        return str (self.start) + '-' + str (self.end)[common:]


    def readings (self, prefix = None, suffix = None, delete = None):
        # Get a list of all readings for this passage

        prefix = prefix or []
        suffix = suffix or []
        delete = delete or []

        res = execute (self.conn, """
        SELECT labez
        FROM readings
        WHERE pass_id = :pass_id AND labez != 'zz'
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

        Readings = collections.namedtuple ('Readings', 'labez labez_i18n')
        return [ Readings._make (r)._asdict () for r in d.items () ]


    def cliques (self, prefix = None, suffix = None, delete = None):
        # Get a list of all cliques for this passage

        prefix = prefix or []
        suffix = suffix or []
        delete = delete or []

        res = execute (self.conn, """
        SELECT labez, clique, labez_clique (labez, clique) AS labez_clique
        FROM cliques
        WHERE pass_id = :pass_id
        ORDER BY labez, clique
        """, dict (parameters, pass_id = self.pass_id))

        Cliques = collections.namedtuple ('Cliques', 'labez clique labez_clique')
        return [ Cliques._make (r)._asdict ()
                 for r in prefix + list (res.fetchall ()) + suffix if r not in delete ]


def get_locale ():
    return flask.request.accept_languages.best_match ('en')
    # return flask.request.accept_languages.best_match (LANGUAGES.keys ())


def cache (response):
    response.headers['Cache-Control'] = 'private, max-age=3600'
    return response


def make_json_response (json = None, status = 200, message = None):
    d = dict (status = status)
    if json is not None:
        d['data'] = json
    if message is not None:
        d['message'] = message
    return flask.make_response (flask.json.jsonify (d), status, {
        'content-type' : 'application/json;charset=utf-8',
        'Access-Control-Allow-Origin' : '*',
    })


def make_dot_response (dot, status = 200):
    return flask.make_response (dot, status, {
        'content-type' : 'text/vnd.graphviz;charset=utf-8',
        'Access-Control-Allow-Origin' : '*',
    })


def make_csv_response (csv, status = 200):
    return flask.make_response (csv, status, {
        'content-type' : 'text/csv;charset=utf-8',
        'Access-Control-Allow-Origin' : '*',
    })


def make_png_response (png, status = 200):
    return flask.make_response (png, status, {
        'content-type' : 'image/png',
        'Access-Control-Allow-Origin' : '*',
    })


def make_text_response (text, status = 200):
    return flask.make_response (text, status, {
        'content-type' : 'text/plain;charset=utf-8',
        'Access-Control-Allow-Origin' : '*',
    })


def csvify (fields, rows):
    """ Send a HTTP response in CSV format. """

    return make_csv_response (to_csv (fields, rows))


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
    return max (lo, min (hi, float (x)))


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


def nx_to_dot (graph, width = 960.0, fontsize = 10.0, nodesep = 0.1):
    """Convert an nx graph into a dot file.

    We'd like to sort the nodes in the graph, but nx internally uses
    dictionaries "all the way down".  Thus the only chance to sort nodes and
    edges is while writing the file.  This function is a lightweight
    re-implementation of nx.nx_pydot.to_pydot ().

    """

    dot = dot_skeleton (width = width, fontsize = fontsize, nodesep = nodesep)

    # Copy nodes and sort them.  (Sorting nodes is important too.)
    for n, nodedata in sorted (graph.nodes (data = True)):
        dot.append ("\"%s\" [%s];" %
                    (n, ','.join (["\"%s\"=\"%s\"" % (k, v) for k, v in nodedata.items ()])))

    # Copy edges and sort them.
    for u, v, edgedata in sorted (graph.edges (data = True)):
        dot.append ("\"%s\" -> \"%s\" [%s];" %
                    (u, v, ','.join (["\"%s\"=\"%s\"" % (k, v) for k, v in edgedata.items ()])))

    dot.append ('}\n')

    return '\n'.join (dot)


def nx_to_dot_subgraphs (graph, field, width = 960.0, fontsize = 10.0):
    """Convert an nx graph into a dot file.

    We'd like to sort the nodes in the graph, but nx internally uses
    dictionaries "all the way down".  Thus the only chance to sort nodes and
    edges is while writing the file.  This function is a lightweight
    re-implementation of nx.nx_pydot.to_pydot ().

    """

    dot = dot_skeleton (width = width, fontsize = fontsize, ranksep = 1.2)

    # Copy nodes and sort them.  (Sorting nodes is important too.)
    sorted_nodes = sorted (graph, key = lambda n: (graph.nodes[n][field], graph.nodes[n]['hsnr']))
    for key, nodes_for_key in itertools.groupby (sorted_nodes,
                                                 key = lambda n: graph.nodes[n][field]):
        dot.append ("subgraph \"cluster_%s\" {" % key)
        dot.append ("style=rounded")
        dot.append ("labeljust=l")
        dot.append ("labelloc=c")
        dot.append ("rank=%s" % ('source' if key in ('a', 'a1') else 'same'))
        dot.append ("label=\"%s\"" % key)
        for n in nodes_for_key:
            attr = graph.nodes[n]
            dot.append ("\"%s\" [%s];" %
                        (n, ','.join (["\"%s\"=\"%s\"" % (k, v) for k, v in attr.items ()])))
        dot.append ("}")

    # Copy edges and sort them.
    for u, v, edgedata in sorted (graph.edges (data = True)):
        dot.append ("\"%s\" -> \"%s\" [%s];" %
                    (u, v, ','.join (["\"%s\"=\"%s\"" % (k, v) for k, v in edgedata.items ()])))

    dot.append ('}\n')

    return '\n'.join (dot)
