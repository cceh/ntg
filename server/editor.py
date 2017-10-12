# -*- encoding: utf-8 -*-

"""An application server for CBGM.  Editor module.  """

import argparse
import collections
import csv
import datetime
import functools
import glob
import io
import itertools
import logging
import math
import operator
import re
import sys
import os
import os.path
import urllib.parse

import flask
from flask import request, current_app
from flask_user import roles_required
import flask_login
import networkx as nx
import sqlalchemy

from ntg_common import tools
from ntg_common import db_tools
from ntg_common.db_tools import execute, rollback
from ntg_common.config import args

from . import helpers
from .helpers import parameters, Bag, Passage, Manuscript, make_json_response

RE_VALID_LABEZ  = re.compile ('^[*]|[?]|[a-y]|z[u-z]$')
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

    action = request.args.get ('action')

    if (action not in ('split', 'merge', 'move', 'move-manuscripts')):
        raise EditError ('Bad request')

    params = { 'original' : False }
    for n in 'labez_old labez_new'.split ():
        params[n] = request.args.get (n)
        if not RE_VALID_LABEZ.match (params[n]):
            raise EditError ('Bad request')
        if params[n] == '*':
            params['original'] = True
        if params[n] in ('*', '?'):
            params[n] = None
    for n in 'clique_old clique_new'.split ():
        params[n] = request.args.get (n)
        if not RE_VALID_CLIQUE.match (params[n]):
            raise EditError ('Bad request')

    with current_app.config.dba.engine.begin () as conn:
        passage = Passage (conn, passage_or_id)
        params['pass_id'] = passage.pass_id

        if action == 'move':
            try:
                res = execute (conn, """
                UPDATE locstem
                SET source_labez = :labez_new, source_clique = :clique_new, original = :original
                WHERE pass_id = :pass_id AND labez = :labez_old AND clique = :clique_old
                """, dict (parameters, **params))
            except sqlalchemy.exc.IntegrityError as e:
                if 'unique_locstem_original' in str (e):
                    raise EditError ('Only one original reading allowed. If you want to change the original reading, first remove the old original reading.')
                raise EditError (str (e))
            except sqlalchemy.exc.DatabaseError as e:
                raise EditError (str (e))

            if res.rowcount > 1:
                raise EditError (
                    'Too many rows ({count}) affected while moving {labez_old}{clique_old} to {labez_new}{clique_new}'
                .format (count = res.rowcount, **params))
            if res.rowcount == 0:
                raise EditError (
                    'Could not move {labez_old}{clique_old} to {labez_new}{clique_new}'
                .format (**params))

            # test the still uncommited changes

            G = db_tools.local_stemma_to_nx (conn, passage.pass_id)

            # test: not a DAG
            if not nx.is_directed_acyclic_graph (G):
                raise EditError ('The graph is not a DAG anymore.')
            # test: not connected
            G.add_edge ('?', '*')
            if nx.isolates (G):
                raise EditError ('The graph is not connected anymore.')
            # test: x derived from x
            for e in G.edges_iter ():
                if e[0][0] == e[1][0]:
                    raise EditError ('A reading cannot be derived from the same reading.  If you want to <b>merge</b> instead, use shift + drag.')

        elif action == 'split':
            res = execute (conn, """
            SELECT max (clique)
            FROM  cliques
            WHERE pass_id = :pass_id AND labez = :labez_old
            """, dict (parameters, **params))

            # the old clique doesn't matter when splitting, replace it with the
            # next free one
            params['clique_old'] = str (int (res.fetchone ()[0]) + 1)

            res = execute (conn, """
            INSERT INTO cliques (pass_id, labez, clique)
            VALUES (:pass_id, :labez_old, :clique_old)
            """, dict (parameters, **params))

            res = execute (conn, """
            INSERT INTO locstem (pass_id, labez, clique, source_labez, source_clique, original)
            VALUES (:pass_id, :labez_old, :clique_old, :labez_new, :clique_new, false)
            """, dict (parameters, **params))

        elif action == 'merge':
            res = execute (conn, """
            UPDATE apparatus
            SET clique = :clique_new
            WHERE (pass_id, labez, clique) = (:pass_id, :labez_old, :clique_old)
            """, dict (parameters, **params))

            res = execute (conn, """
            DELETE FROM locstem
            WHERE (pass_id, labez, clique) = (:pass_id, :labez_old, :clique_old)
            """, dict (parameters, **params))

            res = execute (conn, """
            DELETE FROM cliques
            WHERE (pass_id, labez, clique) = (:pass_id, :labez_old, :clique_old)
            """, dict (parameters, **params))

        elif action == 'move-manuscripts':
            ms_ids = set (request.args.getlist ('ms_ids[]') or [])
            res = execute (conn, """
            UPDATE apparatus
            SET clique = :clique_new
            WHERE (pass_id, labez, clique) = (:pass_id, :labez_old, :clique_old)
              AND ms_id IN :ms_ids
            """, dict (parameters, ms_ids = tuple (ms_ids), **params))

            tools.log (logging.INFO, 'Moved ms_ids: ' + str (ms_ids))


        # return the changed passage
        passage = Passage (conn, passage_or_id)
        return make_json_response (passage.to_json ())

    raise EditError ('Could not edit local stemma.')
