#!/usr/bin/python3
# -*- encoding: utf-8 -*-

"""An application server for CBGM."""

import argparse
import collections
import itertools
import math
import re
import sys
import os.path

import flask
import flask_babel
from sqlalchemy import create_engine, MetaData, Table
from sqlalchemy.sql import text

sys.path.append (os.path.dirname (os.path.abspath (__file__)) + "/..")

from ntg_common import db
from ntg_common.db import execute
from ntg_common.config import args
from ntg_common import tools

LANGUAGES = {
    'en': 'English',
    'de': 'Deutsch'
}

app = flask.Flask ("server")
babel = flask_babel.Babel (app)

@babel.localeselector
def get_locale ():
    return flask.request.accept_languages.best_match (LANGUAGES.keys ())

class Bag (object):
    """ Class to stick values in. """
    pass


def fix_passage (start, end):
    if end is None:
        end = start
    start = str (int (start))
    end   = str (int (end))
    cut   = len (start) - len (end)
    return start, start[:cut] + end


def format_passage (start, end):
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


@app.route ("/")
def index ():
    return flask.render_template ('index.html')


@app.route('/relatives.json/<int:hsnr>')
@app.route('/relatives.json/<int:hsnr>/<int:chapter>')
@app.route('/relatives.json/<int:hsnr>/<int:chapter>/<int:limit>')
def ms_info (hsnr, chapter = 0, limit = 10):
    """ Unused """

    with dba.engine.begin () as conn:

        res = execute (conn, """
        SELECT id FROM Manuscripts WHERE hsnr = :hsnr
        """, { 'hsnr' : hsnr } )
        id1 = res.scalar ()

        res = execute (conn, """
        SELECT hsnr, common, equal, affinity
        FROM {aff} aff
          JOIN {ms} ms1
          JOIN {ms} ms2
        ON aff.id1 = ms1.id AND aff.id2 = ms2.id AND ms2.length >= ms1.length / 2
        WHERE chapter = :chapter AND aff.id1 = :id1
        ORDER BY affinity DESC LIMIT :limit
        """, dict (parameters, id1 = id1, chapter = chapter, limit = limit))

        # convert tuples to lists
        return flask.json.jsonify ( [list (row) for row in res] )


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
@app.route('/relatives/<int:pass_id>/<int:hsnr>/<int:chapter>')
@app.route('/relatives/<int:pass_id>/<int:hsnr>/<int:chapter>/<int:limit>')
def relatives (hsnr, pass_id, chapter = 0, limit = 10):
    """Output a table of the nearest relatives of a manuscript.

    Output a table of the nearest relatives of a manuscript and what they
    attest.

    """

    with dba.engine.begin () as conn:

        # Get the manuscript name
        ms = Bag ()
        res = execute (conn, """
        SELECT id - 1 as id, hs FROM {ms} WHERE hsnr = :hsnr
        """, dict (parameters, hsnr = hsnr))
        ms.id_, ms.hs = res.fetchone ()

        # Get the attestation (labez) of the manuscript
        res = execute (conn, """
        SELECT char_labez (labez) as labez, labezsuf
        FROM {labez}
        WHERE ms_id = :ms_id AND pass_id = :pass_id
        """, dict (parameters, ms_id = ms.id_ + 1, pass_id = pass_id))
        ms.labez, ms.labezsuf = res.fetchone ()

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

        # Get the X most similar manuscripts and their attestations
        res = execute (conn, """
        SELECT ms2.id - 1 as id, ms2.hs, ms2.hsnr, aff.common, aff.equal, aff.affinity,
               char_labez (labez.labez) as labez, labez.labezsuf
        FROM {aff} aff
          JOIN {ms} ms1
          JOIN {ms} ms2
            JOIN {labez} labez
        ON aff.id1 = ms1.id AND aff.id2 = ms2.id AND ms2.length >= ms1.length / 2
          AND ms2.id = labez.ms_id AND labez.labez > 0 AND aff.common > 0
        WHERE ms1.hsnr = :hsnr AND labez.pass_id = :pass_id AND chapter = :chapter
        ORDER BY affinity DESC
        LIMIT :limit
        """, dict (parameters, hsnr = hsnr, pass_id = pass_id, chapter = chapter, limit = limit))

        Relatives = collections.namedtuple ('Relatives', 'id hs hsnr common equal affinity labez labezsuf')
        relatives = list (map (Relatives._make, res))

        # convert tuples to lists
        return flask.render_template ("relatives.html", ms = ms, mt = mt, rows = relatives)


@app.route('/coherence/attestation/<start>')
@app.route('/coherence/attestation/<start>/<end>')
def coherence_attestation (start, end = None):

    values = Bag ()
    values.start, values.end =  fix_passage (start, end)
    values.hr_pass = format_passage (values.start, values.end)

    with dba.engine.begin () as conn:

        res = execute (conn, """
        SELECT id
        FROM {pass}
        WHERE anfadr = :anfadr AND endadr = :endadr
        """, dict (parameters, anfadr = values.start, endadr =  values.end))
        values.pass_id = res.scalar ()

        # list of labez
        res = execute (conn, """
        SELECT DISTINCT labez, labezsuf, ord_labez (labez) as ord_labez, lesart
        FROM {att}
        WHERE anfadr = :anfadr AND endadr = :endadr AND NOT labez REGEXP '^z'
        ORDER BY labez, labezsuf
        """, dict (parameters, anfadr = values.start, endadr = values.end))

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
            """, dict (parameters, anfadr = values.start, endadr = values.end, labez = r.labez, labezsuf = r.labezsuf))

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
        """, dict (parameters, pass_id = values.pass_id))

        Attestation = collections.namedtuple ('Attestation', 'id labez labezsuf')
        values.attestation = list (map (Attestation._make, res))

        return flask.render_template ('coherence_attestation.html', values = values)

    return 'Error'


@app.route('/coherence/attestation.json/<pass_id>')
def coherence_attestation_json (pass_id):

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

    dba = db.DBA (args.profile)

    parameters = tools.init_parameters (tools.DEFAULTS)

    app.run ()
