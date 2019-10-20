# -*- encoding: utf-8 -*-

"""The API server for CBGM.  The main functions."""

import collections
import re

import flask
from flask import request, current_app
import flask_login

from ntg_common.db_tools import execute

from login import auth
from helpers import parameters, Passage, Manuscript, cache, csvify, get_excluded_ms_ids, \
     make_json_response

bp = flask.Blueprint ('main', __name__)


def init_app (app):
    """ Initialize the flask app. """

    app.config.bk_id = None
    app.config.rg_id_all = None

    with app.config.dba.engine.begin () as conn:
        try:
            res = execute (conn, """
            SELECT bk_id
            FROM books
            WHERE book = :book
            """, { 'book' : app.config['BOOK'] })
            app.config.bk_id = res.fetchone ()[0]

            res = execute (conn, """
            SELECT rg_id
            FROM ranges
            WHERE bk_id = :bk_id AND range = 'All'
            """, { 'bk_id' : app.config.bk_id })
            rg_id = res.fetchone ()[0]

            app.config.rg_id_all = rg_id
        except:
            pass # FIXME


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


@bp.route ('/application.json')
def application_json ():
    """Endpoint.  Serve information about the application."""

    conf = current_app.config

    return make_json_response ({
        'name'         : conf['APPLICATION_NAME'],
        'root'         : conf['APPLICATION_ROOT'],
        'read_access'  : conf['READ_ACCESS'],
        'write_access' : conf['WRITE_ACCESS'],
        'start'        : conf['SERVER_START_TIME'],
        'rg_id_all'    : conf.rg_id_all,
    })


@bp.route ('/ranges.json/')
def ranges_json ():
    """Endpoint.  Serve a list of ranges.

    Serves a list of the configured ranges that are contained inside a book in
    the NT.

    """

    conf = current_app.config
    with conf.dba.engine.begin () as conn:
        res = execute (conn, """
        SELECT DISTINCT bk_id, book, rg_id, range, lower (rg.passage) as begadr, upper (rg.passage) as endadr
        FROM ranges_view rg
        WHERE bk_id = :bk_id
        ORDER BY begadr, endadr DESC
        """, dict (parameters, bk_id = conf.bk_id))

        Ranges = collections.namedtuple ('Ranges', 'bk_id, book, rg_id, range, begadr, endadr')
        ranges = [ Ranges._make (r)._asdict () for r in res ]

        return cache (make_json_response (ranges))


@bp.route ('/passage.json/')
@bp.route ('/passage.json/<passage_or_id>')
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

    auth ()

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
        return cache (make_json_response (passage.to_json ()))


@bp.route ('/readings.json/<passage_or_id>')
def readings_json (passage_or_id):
    """ Endpoint.  Serve all readings found in a passage.

    :param string passage_or_id: The passage id.

    """

    auth ()

    with current_app.config.dba.engine.begin () as conn:
        passage = Passage (conn, passage_or_id)
        return cache (make_json_response (passage.readings ()))


@bp.route ('/cliques.json/<passage_or_id>')
def cliques_json (passage_or_id):
    """ Endpoint.  Serve all cliques found in a passage.

    :param string passage_or_id: The passage id.

    """

    auth ()

    with current_app.config.dba.engine.begin () as conn:
        passage = Passage (conn, passage_or_id)
        return make_json_response (passage.cliques ())


@bp.route ('/leitzeile.json/<passage_or_id>')
def leitzeile_json (passage_or_id):
    """Endpoint.  Serve the leitzeile for the verse containing passage_or_id. """

    auth ()

    with current_app.config.dba.engine.begin () as conn:
        passage = Passage (conn, passage_or_id)
        verse_start = (passage.start // 1000) * 1000
        verse_end = verse_start + 999

        res = execute (conn, """
        SELECT l.begadr, l.endadr, l.lemma, ARRAY_AGG (p.pass_id)
        FROM nestle l
          LEFT JOIN passages p ON (p.passage @> l.passage)
        WHERE int4range (:start, :end + 1) @> l.passage
        GROUP BY l.begadr, l.endadr, l.lemma

        UNION -- get the insertions

        SELECT p.begadr, p.endadr, '', ARRAY_AGG (p.pass_id)
        FROM passages_view p
        WHERE int4range (:start, :end + 1) @> p.passage AND (begadr % 2) = 1
        GROUP BY p.begadr, p.endadr

        ORDER BY begadr, endadr DESC
        """, dict (parameters, start = verse_start, end = verse_end))

        Leitzeile = collections.namedtuple (
            'Leitzeile', 'begadr, endadr, lemma, pass_ids')
        leitzeile = [ Leitzeile._make (r)._asdict () for r in res ]

        return make_json_response (leitzeile)


@bp.route ('/suggest.json')
def suggest_json ():
    """Endpoint.  The suggestion drop-downs in the navigator.

    Serves a list of books, chapters, verses, or words that the user can enter
    in the navigation gadget.  It suggests only entities that are actually in
    the database.

    """

    auth ()

    # the name of the current field
    field   = request.args.get ('currentfield')

    # the term the user entered in the current field
    term    = request.args.get ('term') or ''
    term    = '^' + re.escape (term.split ('-')[0])

    # terms entered in previous fields
    siglum  = request.args.get ('siglum')  or ''
    chapter = request.args.get ('chapter') or 0
    verse   = request.args.get ('verse')   or 0

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


@bp.route ('/manuscript.json/<hs_hsnr_id>')
def manuscript_json (hs_hsnr_id):
    """Endpoint.  Serve information about a manuscript.

    :param string hs_hsnr_id: The hs, hsnr or id of the manuscript.

    """

    auth ()

    hs_hsnr_id = request.args.get ('ms_id') or hs_hsnr_id

    with current_app.config.dba.engine.begin () as conn:
        ms = Manuscript (conn, hs_hsnr_id)
        return make_json_response (ms.to_json ())


@bp.route ('/manuscript-full.json/<passage_or_id>/<hs_hsnr_id>')
def manuscript_full_json (passage_or_id, hs_hsnr_id):
    """Endpoint.  Serve information about a manuscript.

    :param string hs_hsnr_id: The hs, hsnr or id of the manuscript.

    """

    auth ()

    hs_hsnr_id = request.args.get ('ms_id') or hs_hsnr_id

    with current_app.config.dba.engine.begin () as conn:
        passage   = Passage (conn, passage_or_id)
        ms        = Manuscript (conn, hs_hsnr_id)
        rg_id     = passage.request_rg_id (request)

        json = ms.to_json ()
        json['length'] = ms.get_length (rg_id)

        # Get the attestation(s) of the manuscript (may be uncertain eg. a/b/c)
        res = execute (conn, """
        SELECT labez, clique, labez_clique, certainty
        FROM apparatus_view_agg
        WHERE ms_id = :ms_id AND pass_id = :pass_id
        """, dict (parameters, ms_id = ms.ms_id, pass_id = passage.pass_id))
        json['labez'], json['clique'], json['labez_clique'], json['certainty'] = res.fetchone ()

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

        return cache (make_json_response (json))


@bp.route ('/relatives.csv/<passage_or_id>/<hs_hsnr_id>')
def relatives_csv (passage_or_id, hs_hsnr_id):
    """Output a table of the nearest relatives of a manuscript.

    Output a table of the nearest relatives/ancestors/descendants of a
    manuscript and what they attest.

    """

    auth ()

    type_     = request.args.get ('type') or 'rel'
    limit     = int (request.args.get ('limit') or 0)
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
        rg_id     = passage.request_rg_id (request)

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
               a.labez,
               a.certainty
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
            'rank ms_id hs hsnr length common equal older newer unclear norel direction affinity labez certainty'
        )
        return csvify (Relatives._fields, list (map (Relatives._make, res)))


@bp.route ('/apparatus.json/<passage_or_id>')
def apparatus_json (passage_or_id):
    """ The contents of the apparatus table. """

    auth ()

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
        FROM apparatus_view_agg
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


@bp.route ('/attestation.json/<passage_or_id>')
def attestation_json (passage_or_id):
    """Answer with a list of the attestations of all manuscripts at one specified
    passage."""

    auth ()

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


@bp.route ('/attesting.csv/<passage_or_id>/<labez>')
def attesting_csv (passage_or_id, labez):
    """ Serve all relatives of all mss. attesting labez at passage. """

    auth ()

    with current_app.config.dba.engine.begin () as conn:
        passage = Passage (conn, passage_or_id)

        res = execute (conn, """
        SELECT ms_id, hs, hsnr
        FROM apparatus_view
        WHERE pass_id = :pass_id AND labez = :labez
        ORDER BY hsnr
        """, dict (parameters, pass_id = passage.pass_id, labez = labez))

        Attesting = collections.namedtuple ('Attesting', 'ms_id hs hsnr')

        return csvify (Attesting._fields, list (map (Attesting._make, res)))
