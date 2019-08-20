# -*- encoding: utf-8 -*-

"""The API server for CBGM.  Stemma editing module. """

import collections
import logging
import re

import flask
from flask import request, current_app
import flask_login
import networkx as nx
import sqlalchemy

from ntg_common import tools
from ntg_common import db_tools
from ntg_common.exceptions import EditError, PrivilegeError
from ntg_common.db_tools import execute

from helpers import parameters, Passage, make_json_response, make_text_response

# FIXME: this is too lax but we need to accomodate one spurious 'z' reading
RE_VALID_LABEZ  = re.compile ('^([*]|[?]|[a-z]{1,2}|z[u-z])$')
RE_VALID_CLIQUE = re.compile ('^[0-9]$')

# FIXME: this is too lax but we need to accomodate one spurious 'z' reading
RE_EXTRACT_LABEZ = re.compile ('^([*]|[?]|[a-z]{1,2})')

bp = flask.Blueprint ('editor', __name__)

def init_app (_app):
    """ Initialize the flask app. """


def edit_auth ():
    """ Check if user is authorized to edit. """

    conf = flask.current_app.config
    write_access = conf['WRITE_ACCESS']

    if write_access != 'public':
        if not flask_login.current_user.has_role (write_access):
            raise PrivilegeError ('You don\'t have %s privilege.' % write_access)


@bp.route ('/stemma-edit/<passage_or_id>', methods = ['POST'])
def stemma_edit (passage_or_id):
    """Edit a local stemma.

    Called from local-stemma.js (split, merge, move) and textflow.js (move-manuscripts).

    """

    edit_auth ()

    args = request.get_json ()

    action = args.get ('action')

    if action not in ('add', 'del', 'split', 'merge', 'move', 'move-manuscripts'):
        raise EditError ('Bad request')

    params = { }
    for n in 'labez_old labez_new source_labez'.split ():
        if n in args:
            params[n] = args.get (n)
            if not RE_VALID_LABEZ.match (params[n]):
                raise EditError ('Bad request')
    for n in 'clique_old clique_new source_clique'.split ():
        if n in args:
            params[n] = args.get (n)
            if not RE_VALID_CLIQUE.match (params[n]):
                raise EditError ('Bad request')

    def integrity_error (e):
        if 'ix_locstem_unique_original' in str (e):
            raise EditError (
                '''Only one original reading allowed. If you want to change the original
                reading, first remove the old original reading.<br/><br/>''' + str (e)
            )
        if 'locstem_pkey' in str (e):
            raise EditError (
                '''This readings already dependes on that reading.<br/><br/>''' + str (e)
            )
        if 'same_source' in str (e):
            raise EditError (
                '''A reading cannot be derived from the same reading.
                If you want to <b>merge two readings</b>, use shift + drag.'''
            )
        raise EditError (str (e))

    with current_app.config.dba.engine.begin () as conn:
        passage = Passage (conn, passage_or_id)
        params['pass_id'] = passage.pass_id
        params['user_id'] = flask_login.current_user.id

        res = execute (conn, """
        SET LOCAL ntg.user_id = :user_id;
        """, dict (parameters, **params))

        if action == 'move':
            # reassign a source reading
            # there may be multiple existent assignments, there'll be only one left
            try:
                res = execute (conn, """
                DELETE FROM locstem
                WHERE (pass_id, labez, clique) = (:pass_id, :labez_old, :clique_old);
                INSERT INTO locstem (pass_id, labez, clique, source_labez, source_clique)
                VALUES (:pass_id, :labez_old, :clique_old, :labez_new, :clique_new)
                """, dict (parameters, **params))
            except sqlalchemy.exc.IntegrityError as e:
                integrity_error (e)
            except sqlalchemy.exc.DatabaseError as e:
                raise EditError (str (e))

        if action == 'del':
            # remove a source reading
            try:
                # check if we are asked to remove the only link,
                # in that case reassign to 'unknown'
                res = execute (conn, """
                SELECT pass_id
                FROM locstem
                WHERE (pass_id, labez, clique) = (:pass_id, :labez_old, :clique_old);
                """, dict (parameters, **params))

                tools.log (logging.INFO, 'Deleting: ' + str (params))

                if res.rowcount > 1:
                    res = execute (conn, """
                    DELETE FROM locstem
                    WHERE (pass_id, labez, clique) = (:pass_id, :labez_old, :clique_old)
                      AND (source_labez, source_clique) = (:source_labez, :source_clique)
                    """, dict (parameters, **params))
                else:
                    res = execute (conn, """
                    UPDATE locstem
                    SET (source_labez, source_clique) = ('?', '1')
                    WHERE (pass_id, labez, clique) = (:pass_id, :labez_old, :clique_old);
                    """, dict (parameters, **params))
            except sqlalchemy.exc.IntegrityError as e:
                integrity_error (e)
            except sqlalchemy.exc.DatabaseError as e:
                raise EditError (str (e))

        if action == 'add':
            # add a source reading
            try:
                res = execute (conn, """
                INSERT INTO locstem (pass_id, labez, clique, source_labez, source_clique)
                VALUES (:pass_id, :labez_old, :clique_old, :labez_new, :clique_new)
                """, dict (parameters, **params))
            except sqlalchemy.exc.IntegrityError as e:
                integrity_error (e)
            except sqlalchemy.exc.DatabaseError as e:
                raise EditError (str (e))

        if action in ('add', 'del', 'move'):
            # test the still uncommitted changes

            graph = db_tools.local_stemma_to_nx (conn, passage.pass_id)

            # test: not a DAG
            if not nx.is_directed_acyclic_graph (graph):
                raise EditError ('The new graph contains cycles.')
            # test: not connected
            graph.add_edge ('*', '?')
            if not nx.is_weakly_connected (graph):
                raise EditError ('The new graph is not connected.')

        elif action == 'split':
            # get the next free clique
            res = execute (conn, """
            SELECT max (clique)
            FROM  cliques
            WHERE pass_id = :pass_id AND labez = :labez_old
            """, dict (parameters, **params))
            params['clique_next'] = str (int (res.fetchone ()[0]) + 1)

            # insert into cliques table
            res = execute (conn, """
            INSERT INTO cliques (pass_id, labez, clique)
            VALUES (:pass_id, :labez_old, :clique_next)
            """, dict (parameters, **params))

            # insert into locstem table with source = '?'
            res = execute (conn, """
            INSERT INTO locstem (pass_id, labez, clique, source_labez, source_clique)
            VALUES (:pass_id, :labez_old, :clique_next, '?', '1')
            """, dict (parameters, **params))

        elif action == 'merge':
            # merge two cliques (eg. b1, b2) into one clique (eg. b1)
            #
            # reassign manuscripts to merged clique
            res = execute (conn, """
            UPDATE ms_cliques
            SET clique = :clique_new
            WHERE (pass_id, labez, clique) = (:pass_id, :labez_old, :clique_old)
            """, dict (parameters, **params))

            # reassign sources to merged clique
            res = execute (conn, """
            UPDATE locstem
            SET source_clique = :clique_new
            WHERE (pass_id, source_labez, source_clique) = (:pass_id, :labez_old, :clique_old)
            """, dict (parameters, **params))

            # remove clique from locstem
            res = execute (conn, """
            DELETE FROM locstem
            WHERE (pass_id, labez, clique) = (:pass_id, :labez_old, :clique_old)
            """, dict (parameters, **params))

            # remove clique from cliques
            res = execute (conn, """
            DELETE FROM cliques
            WHERE (pass_id, labez, clique) = (:pass_id, :labez_old, :clique_old)
            """, dict (parameters, **params))

        elif action == 'move-manuscripts':
            # reassign a set of manuscripts to a new clique
            ms_ids = set (args.get ('ms_ids') or [])

            res = execute (conn, """
            UPDATE apparatus_cliques_view
            SET clique = :clique_new
            WHERE (pass_id, labez, clique) = (:pass_id, :labez_old, :clique_old)
              AND ms_id IN :ms_ids
            """, dict (parameters, ms_ids = tuple (ms_ids), **params))

            tools.log (logging.INFO, 'Moved ms_ids: ' + str (ms_ids))

        # return the changed passage
        passage = Passage (conn, passage_or_id)
        return make_json_response (passage.to_json ())

    raise EditError ('Could not edit local stemma.')


@bp.route ('/notes.txt/<passage_or_id>', methods = ['GET', 'PUT'])
def notes_txt (passage_or_id):
    """Get the editor notes for a passage

    """

    edit_auth ()

    with current_app.config.dba.engine.begin () as conn:
        passage = Passage (conn, passage_or_id)

        if request.method == 'PUT':
            res = execute (conn, """
            SET LOCAL ntg.user_id = :user_id;
            """, dict (parameters, user_id = flask_login.current_user.id))

            res = execute (conn, """
            INSERT INTO notes AS n (pass_id, note)
            VALUES (:pass_id, :note)
            ON CONFLICT (pass_id) DO
            UPDATE
            SET note = :note
            WHERE n.pass_id = EXCLUDED.pass_id
            """, dict (parameters,
                       pass_id = passage.pass_id,
                       note = request.get_json ()['remarks']))

            return make_json_response (message = 'Notes saved.')
        res = execute (conn, """
        SELECT note
        FROM notes
        WHERE pass_id = :pass_id
        """, dict (parameters, pass_id = passage.pass_id))

        if res.rowcount > 0:
            return make_text_response (res.fetchone ()[0])
        return make_text_response ('')


@bp.route ('/notes.json')
def notes_json ():
    """Endpoint.  Get a list of all editor notes."""

    edit_auth ()

    with current_app.config.dba.engine.begin () as conn:
        res = execute (conn, """
        SELECT pass_id, begadr, endadr, note
        FROM passages_view
        JOIN notes
          USING (pass_id)
        """, dict (parameters))

        Notes = collections.namedtuple ('Notes', 'pass_id, begadr, endadr, note')
        notes = []
        for r in res:
            note = Notes._make (r)._asdict ()
            note['hr'] = Passage.static_to_hr (note['begadr'], note['endadr'])
            notes.append (note)

        return make_json_response (notes)
