#!/usr/bin/python3
# -*- encoding: utf-8 -*-

"""The API server for CBGM.  The main Flask driver.

This module sets up the main Flask application for user authentication and the
sub-apps for each book.

"""

import argparse
import collections
import glob
import os
import os.path
import time

import flask
from flask import current_app
import flask_sqlalchemy
import flask_user
import flask_login
import flask_mail
from werkzeug.wsgi import DispatcherMiddleware

from ntg_common.config import init_logging
from ntg_common import db_tools
from ntg_common.exceptions import EditException

import login
import main
import textflow
import comparison
import editor
import set_cover

dba = flask_sqlalchemy.SQLAlchemy ()
user, _role, _roles_users = login.declare_user_model_on (dba)
db_adapter = flask_user.SQLAlchemyAdapter (dba, user)
login_manager = flask_login.LoginManager ()
login_manager.anonymous_user = login.AnonymousUserMixin
user_manager = flask_user.UserManager (db_adapter)
mail = flask_mail.Mail ()


class Config ():
    """ Default configuration object. """

    APPLICATION_HOST  = 'localhost'
    APPLICATION_PORT  = 5000
    CONFIG_FILE       = '_global.conf' # default relative to /instance
    USE_RELOADER      = False
    USE_DEBUGGER      = False
    SERVER_START_TIME = str (int (time.time ())) # for cache busting
    READ_ACCESS       = 'none'
    WRITE_ACCESS      = 'none'
    CORS_ALLOW_ORIGIN = '*'
    SQLALCHEMY_TRACK_MODIFICATIONS = False


def build_parser (default_config_file):
    """ Build the commandline parser. """

    parser = argparse.ArgumentParser (description = __doc__)

    parser.add_argument (
        '-v', '--verbose', dest='verbose', action='count',
        help='increase output verbosity', default=0
    )
    parser.add_argument (
        '-c', '--config-file', dest='config_file',
        default=default_config_file, metavar='CONFIG_FILE',
        help="the config file (default='%s')" % default_config_file
    )
    return parser


def do_init_app (app):
    """ Initializations to do on main and sub apps. """

    dba.init_app (app)
    mail.init_app (app)
    login.init_app (app)
    user_manager.init_app (app, login_manager = login_manager,
                           make_safe_url_function = login.make_safe_url)

    @app.errorhandler (EditException)
    def handle_invalid_edit (ex):
        response = flask.jsonify (ex.to_dict ())
        response.status_code = ex.status_code
        return response

    @app.after_request
    def add_headers (response):
        response.headers['Access-Control-Allow-Origin'] = current_app.config['CORS_ALLOW_ORIGIN']
        response.headers['Access-Control-Allow-Credentials'] = 'true'
        response.headers['Server'] = 'Jetty 0.8.15'
        return response

    app.logger.info ("Mounted {name} at {host}:{port}{mount} from conf {conf}".format (
        name  = app.config['APPLICATION_NAME'],
        host  = app.config['APPLICATION_HOST'],
        port  = app.config['APPLICATION_PORT'],
        mount = app.config['APPLICATION_ROOT'],
        conf  = app.config['CONFIG_FILE']
    ))


def create_app (Config):
    """ App creation function """

    app = flask.Flask (__name__, instance_relative_config=True)

    app.config.from_object (Config)
    app.config.from_pyfile (Config.CONFIG_FILE)

    # pylint: disable=no-member
    app.logger.setLevel (Config.LOG_LEVEL)
    app.logger.info ("Instance path: {ip}".format (ip = app.instance_path))

    app.register_blueprint (login.bp)

    app.config.dba = db_tools.PostgreSQLEngine (**app.config)
    user_db_url = app.config.dba.url
    # tell flask_sqlalchemy where the user authentication database is
    app.config['SQLALCHEMY_DATABASE_URI'] = user_db_url

    do_init_app (app)

    instances = collections.OrderedDict ()
    extra_files = [app.instance_path + '/' + Config.CONFIG_FILE]

    for fn in glob.glob (app.instance_path + '/*.conf'):
        extra_files.append (fn)
        fn = os.path.basename (fn)
        if fn == Config.CONFIG_FILE:
            continue

        sub_app = flask.Flask (__name__, instance_relative_config=True)
        sub_app.config.from_object (Config)
        sub_app.config.from_pyfile (Config.CONFIG_FILE)
        sub_app.config.from_pyfile (fn)
        sub_app.config['CONFIG_FILE'] = fn

        sub_app.register_blueprint (main.bp)
        sub_app.register_blueprint (textflow.bp)
        sub_app.register_blueprint (comparison.bp)
        sub_app.register_blueprint (editor.bp)
        sub_app.register_blueprint (set_cover.bp)

        sub_app.config.dba = db_tools.PostgreSQLEngine (**sub_app.config)
        sub_app.config['SQLALCHEMY_DATABASE_URI'] = user_db_url

        do_init_app (sub_app)
        main.init_app (sub_app)
        textflow.init_app (sub_app)
        comparison.init_app (sub_app)
        editor.init_app (sub_app)
        set_cover.init_app (sub_app)

        instances[sub_app.config['APPLICATION_ROOT']] = sub_app

    d = DispatcherMiddleware (app, instances)
    d.config = app.config
    d.config['EXTRA_FILES'] = extra_files
    return d


if __name__ == "__main__":
    from werkzeug.serving import run_simple

    args = build_parser (Config.CONFIG_FILE).parse_args ()
    args = init_logging (args)

    Config.LOG_LEVEL   = args.log_level
    Config.CONFIG_FILE = args.config_file

    app = create_app (Config)

    run_simple (
        app.config['APPLICATION_HOST'],
        app.config['APPLICATION_PORT'],
        app,
        use_reloader = app.config['USE_RELOADER'],
        use_debugger = app.config['USE_DEBUGGER'],
        extra_files  = app.config['EXTRA_FILES']
    )
