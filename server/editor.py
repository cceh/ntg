#!/usr/bin/python3
# -*- encoding: utf-8 -*-

"""An application server for CBGM.  Editor.  """

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
from flask_babel import gettext as _, ngettext as n_, lazy_gettext as l_
from flask_user import roles_required
import flask_login
import networkx as nx

from ntg_common import db
from ntg_common.db import execute, rollback
from ntg_common.config import args
from ntg_common import tools

import helpers
from helpers import parameters, Bag, Passage, Manuscript, make_json_response

RE_VALID_VARNEW = re.compile ('^[*]|[?]|[a-z0-9]*$')

app = flask.Blueprint ('the_editor', __name__)

class EditException (Exception):
    """ See: http://flask.pocoo.org/docs/0.12/patterns/apierrors/ """

    default_status_code = 400

    def __init__(self, message, status_code=None, payload=None):
        Exception.__init__ (self)
        self.message     = _ ('Error:') + ' ' + message
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
    """Edit a local stemma."""

    if not flask_login.current_user.has_role ('editor'):
        raise PrivilegeError (_('You don\'t have editor privilege.'))

    action = request.args.get ('action') or ''
    parent = request.args.get ('parent') or ''
    child  = request.args.get ('child')  or ''
    varold = request.args.get ('varold') or ''
    varnew = request.args.get ('varnew') or ''
    ms_ids = set (request.args.getlist ('ms_ids[]') or [])

    if (not RE_VALID_VARNEW.match (parent) or not RE_VALID_VARNEW.match (child)
        or action not in ('split', 'merge', 'move', 'move-subtree')):
        raise EditError (_('Bad request'))

    with current_app.config.dba.engine.begin () as conn:
        passage = Passage (conn, passage_or_id)

        if action == 'move':
            res = execute (conn, """
            UPDATE {locstemed}
            SET s1 = :parent
            WHERE pass_id = :pass_id AND varnew = :child
            """, dict (parameters, pass_id = passage.pass_id, parent = parent, child = child))

            if res.rowcount > 1:
                raise EditError (_(
                    'Too many rows {count} affected while moving {child} to {parent}'
                ).format (count = res.rowcount, child = child, parent = parent)
            )
            if res.rowcount == 0:
                raise EditError (_(
                    'Could not move {child} to {parent}'
                ).format (child = child, parent = parent)
            )

            # test the still uncommited changes

            G = helpers.local_stemma_to_nx (conn, passage)

            # test: not a DAG
            if not nx.is_directed_acyclic_graph (G):
                raise EditError (_('The graph is not a DAG anymore.'))
            # test: not connected
            G.add_edge ('?', '*')
            if nx.isolates (G):
                raise EditError (_('The graph is not connected anymore.'))
            # test: more than one original reading
            if G.out_degree ('*') > 1:
                raise EditError (_('More than one original reading.'))
            # test: x derived from x
            for e in G.edges_iter ():
                if e[0][0] == e[1][0]:
                    raise EditError (_('Reading derived from same reading.'))


        elif action == 'split':
            varid = child[0]

            res = execute (conn, """
            SELECT varnew
            FROM  {locstemed}
            WHERE pass_id = :pass_id AND varnew ~ :re
            """, dict (parameters, pass_id = passage.pass_id, re = '^' + varid))

            max_split = 0
            for row in res.fetchall ():
                max_split = max (max_split, int (row[0][1:] or '0'))
            varnew = varid + str (max_split + 1)

            # FIXME: remember to avoid this in the new database structure !
            if max_split == 0:
                # update 'x' => 'x1'
                res = execute (conn, """
                UPDATE {locstemed}
                SET varnew = :varnew
                WHERE (pass_id, varnew) = (:pass_id, :varold)
                """, dict (parameters, pass_id = passage.pass_id, varold = varnew, varnew = varid + '1'))

                res = execute (conn, """
                UPDATE {var}
                SET varnew = :varnew
                WHERE (pass_id, varnew) = (:pass_id, :varold)
                """, dict (parameters, pass_id = passage.pass_id, varold = varnew, varnew = varid + '1'))

            res = execute (conn, """
            INSERT INTO {locstemed} (pass_id, varid, varnew, s1)
            VALUES (:pass_id, :varid, :varnew, :s1)
            """, dict (parameters, pass_id = passage.pass_id, varid = varid, varnew = varnew, s1 = '?'))

        elif action == 'merge':
            res = execute (conn, """
            UPDATE {var}
            SET varnew = :varnew
            WHERE (pass_id, varnew) = (:pass_id, :varold)
            """, dict (parameters, pass_id = passage.pass_id, varold = child, varnew = parent))

            res = execute (conn, """
            DELETE FROM {locstemed}
            WHERE pass_id = :pass_id AND varnew = :varnew
            """, dict (parameters, pass_id = passage.pass_id, varnew = child))

        elif action == 'move-subtree':
            res = execute (conn, """
            UPDATE {var}
            SET varnew = :varnew
            WHERE (pass_id, varnew) = (:pass_id, :varold) AND ms_id IN :ms_ids
            """, dict (parameters, pass_id = passage.pass_id,
                       ms_ids = tuple (ms_ids), varold = varold, varnew = varnew))

            tools.log (logging.INFO, 'Moved ms_ids: ' + str (ms_ids))


        # return the changed passage
        passage = Passage (conn, passage_or_id)
        return make_json_response (passage.to_json ())

    raise EditError (_('Could not edit local stemma.'))
