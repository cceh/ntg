# -*- encoding: utf-8 -*-

"""An application server for CBGM.  Serve static files.  """

import flask
from flask import request, current_app, send_from_directory


bp = flask.Blueprint ('static', __name__)


def init_app (app):
    """ Initialize the flask app. """
    app.static_folder   = app.config['STATIC_FOLDER']
    app.static_url_path = app.config['STATIC_URL_PATH']


@bp.route ('/api.conf.js')
@bp.route ('/js/<path:path>')
@bp.route ('/images/<path:path>')
@bp.route ('/pdfs/<path:path>')
@bp.route ('/webfonts/<path:path>')
def static_folder (path = None):
    """Endpoint.  Serve static files."""

    return send_from_directory (current_app.static_folder, request.path[1:])


@bp.route ('/<path:path>')
def index_html (path = None):
    """Endpoint.  Serve the index."""

    return send_from_directory (current_app.static_folder, 'index.html')
