# -*- encoding: utf-8 -*-

"""An application server for CBGM.  Editor module.  """

import logging
import re

import flask
from flask import request, current_app
import flask_login
import networkx as nx
import sqlalchemy

from ntg_common import tools
from ntg_common import db_tools
from ntg_common.db_tools import execute

from .helpers import parameters, Passage, make_json_response, make_text_response

RE_VALID_LABEZ  = re.compile ('^([*]|[?]|[a-y]|z[u-z])$')
RE_VALID_CLIQUE = re.compile ('^[0-9]$')

app = flask.Blueprint ('the_editor', __name__)

class EditException (Exception):
    """ See: http://flask.pocoo.org/docs/0.12/patterns/apierrors/ """

    default_status_code = 400

    def __init__ (self, message, status_code=None, payload=None):
        Exception.__init__ (self)
        self.message     = 'Error: ' + message
        self.status_code = status_code or self.default_status_code
        self.payload     = payload

    def to_dict (self):
        rv = dict ()
        rv['status']  = self.status_code
        rv['message'] = self.message
        if self.payload:
            rv['payload'] = self.payload
        return rv


class EditError (EditException):
    pass


class PrivilegeError (EditException):
    pass


@app.app_errorhandler (EditException)
def handle_invalid_edit (ex):
    response = flask.jsonify (ex.to_dict ())
    response.status_code = ex.status_code
    return response


@app.endpoint ('stemma-edit')
def stemma_edit (passage_or_id):
    """Edit a local stemma.

    Called from local-stemma.js (split, merge, move) and textflow.js (move-manuscripts).

    """

    if not flask_login.current_user.has_role ('editor'):
        raise PrivilegeError ('You don\'t have editor privilege.')

    args = request.get_json ()

    action = args.get ('action')

    if action not in ('split', 'merge', 'move', 'move-manuscripts'):
        raise EditError ('Bad request')

    params = { 'original_new' : args.get ('labez_new') == '*' }
    for n in 'labez_old labez_new'.split ():
        params[n] = args.get (n)
        if not RE_VALID_LABEZ.match (params[n]):
            raise EditError ('Bad request')
        if params[n] in ('*', '?'):
            params[n] = None
    for n in 'clique_old clique_new'.split ():
        params[n] = args.get (n)
        if not RE_VALID_CLIQUE.match (params[n]):
            raise EditError ('Bad request')
        if params[n] == '0':
            params[n] = None

    with current_app.config.dba.engine.begin () as conn:
        passage = Passage (conn, passage_or_id)
        params['pass_id'] = passage.pass_id
        params['user_id'] = flask_login.current_user.id

        res = execute (conn, """
        SET LOCAL ntg.user_id = :user_id;
        """, dict (parameters, **params))

        if action == 'move':
            try:
                res = execute (conn, """
                UPDATE locstem
                SET source_labez = :labez_new, source_clique = :clique_new, original = :original_new
                WHERE pass_id = :pass_id AND labez = :labez_old AND clique = :clique_old
                """, dict (parameters, **params))
            except sqlalchemy.exc.IntegrityError as e:
                if 'unique constraint' in str (e):
                    raise EditError (
                        '''Only one original reading allowed. If you want to change the original
                        reading, first remove the old original reading.<br/><br/>''' + str (e)
                    )
                raise EditError (str (e))
            except sqlalchemy.exc.DatabaseError as e:
                raise EditError (str (e))

            # test the still uncommited changes

            graph = db_tools.local_stemma_to_nx (conn, passage.pass_id)

            # test: not a DAG
            if not nx.is_directed_acyclic_graph (graph):
                raise EditError ('The graph is not a DAG anymore.')
            # test: not connected
            graph.add_edge ('*', '?')
            if not nx.is_weakly_connected (graph):
                raise EditError ('The graph is not connected anymore.')
            # test: x derived from x
            for e in graph.edges:
                if e[0][0] == e[1][0]:
                    raise EditError (
                        '''A reading cannot be derived from the same reading.
                        If you want to <b>merge</b> instead, use shift + drag.'''
                    )
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
            INSERT INTO locstem (pass_id, labez, clique, source_labez, source_clique, original)
            VALUES (:pass_id, :labez_old, :clique_next, NULL, NULL, false)
            """, dict (parameters, **params))

        elif action == 'merge':
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
            ms_ids = set (args.get ('ms_ids') or [])

            # reassign manuscripts to new clique
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


@app.endpoint ('notes.txt')
def notes (passage_or_id):
    """Get the editor notes for a passage

    """

    if not flask_login.current_user.has_role ('editor'):
        raise PrivilegeError ('You don\'t have editor privilege.')

    with current_app.config.dba.engine.begin () as conn:
        passage = Passage (conn, passage_or_id)

        if request.method == 'PUT':
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
