# -*- encoding: utf-8 -*-

"""An application server for CBGM.  Root info endpoint. """

import collections

import flask
from flask import current_app
import flask_login

from helpers import make_json_response
from login import user_can_read, user_can_write

bp = flask.Blueprint ('info', __name__)

instances = collections.OrderedDict ()

def init_app (app, instances_):
    """ Initialize the flask app. """

    global instances
    instances.update (instances_)


@bp.route ('/user.json')
def user_json ():
    """Endpoint.  Serve information about the current user."""

    user = flask_login.current_user
    logged_in = user.is_authenticated
    roles = ['public']
    if logged_in:
        roles += [r.name for r in user.roles]

    return make_json_response ({
        'username'  : user.username if logged_in else 'anonymous',
        'roles'     : roles,
        'can_login' : current_app.config['AFTER_LOGIN_URL'] is not None
    })


@bp.route ('/info.json')
def index ():
    """Endpoint.  Serve general info about all registered apps."""

    def copy (a):
        return {
            'application_name'        : a.config['APPLICATION_NAME'],
            'application_root'        : a.config['APPLICATION_DIR'].rstrip ('/') + '/',
            'application_description' : a.config['APPLICATION_DESCRIPTION'],
            'user_can_write'          : user_can_write (a),
        }

    return make_json_response ({
        'instances' : [copy (app) for app in instances.values () if user_can_read (app)],
    })


@bp.route ('/messages.json')
def messages_json ():
    """Endpoint.  Serve the flashed messages."""

    return make_json_response ({
        'messages' : [
            {
                'message'  : m[1],
                'category' : m[0],
            }
            for m in (flask.get_flashed_messages (with_categories = True) or [])
        ]
    })
