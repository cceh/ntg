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
from flask_user import login_required
import networkx as nx

from ntg_common import db
from ntg_common.db import execute, rollback
from ntg_common.config import args
from ntg_common import tools

import helpers
from helpers import parameters, Bag, Passage, Manuscript, make_json_response

app = flask.Blueprint ('the_editor', __name__)

@app.endpoint ('stemma-edit')
@login_required
def stemma_edit (passage_or_id):
    """Edit a local stemma."""

    RE_VALID = re.compile ('^[*]|[?]|[a-z0-9]*$')

    action = request.args.get ('action') or ''
    parent = request.args.get ('parent') or ''
    child  = request.args.get ('child')  or ''

    if not RE_VALID.match (parent) or not RE_VALID.match (child) or action not in ('split', 'merge', 'move'):
        return make_json_response (status = 400, message = _('Bad request'))

    with current_app.config.dba.engine.begin () as conn:
        passage = Passage (conn, passage_or_id)

        if action == 'move':
            res = execute (conn, """
            UPDATE {locstemed}
            SET s1 = :parent
            WHERE pass_id = :pass_id AND varnew = :child
            """, dict (parameters, pass_id = passage.pass_id, parent = parent, child = child))

            if res.rowcount > 1:
                rollback (conn)
                return make_json_response (
                    status = 400,
                    message = _(
                        'Too many rows {count} affected while moving {child} to {parent}'
                    ).format (count = res.rowcount, child = child, parent = parent)
                )
            if res.rowcount == 0:
                return make_json_response (
                    status = 400,
                    message = _('Could not move {child} to {parent}').format (child = child, parent = parent)
                )

            # test the still uncommited changes

            G = helpers.local_stemma_to_nx (conn, passage)

            # test: not a DAG
            if not nx.is_directed_acyclic_graph (G):
                rollback (conn)
            # test: not connected
            G.add_edge ('?', '*')
            if nx.isolates (G):
                rollback (conn)
            # test: more than one original reading
            if G.out_degree ('*') > 1:
                rollback (conn)


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

        # return the changed passage
        passage = Passage (conn, passage_or_id)
        return make_json_response (passage.to_json ())

    return make_json_response (status = 400, message = _('Could not edit local stemma.'))
