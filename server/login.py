# -*- encoding: utf-8 -*-

"""An application server for CBGM.  User management module.  """

import urllib

import flask
from flask import make_response, current_app
from flask_user import UserMixin
import flask_login

from ntg_common import db as dbx
from ntg_common.exceptions import PrivilegeError
from helpers import make_json_response


bp = flask.Blueprint ('login', __name__)


def init_app (app):
    """ Initialize the flask app. """

    app.config['USER_AFTER_LOGIN_ENDPOINT']  = 'login.after_login'
    app.config['USER_AFTER_LOGOUT_ENDPOINT'] = 'login.after_login'


def user_can_read (app):
    """ Return True if user has read access. """

    read_access = app.config['READ_ACCESS']

    if read_access == 'public':
        return True

    return flask_login.current_user.has_role (read_access)


def user_can_write (app):
    """ Return True if user has write access. """

    write_access = app.config['WRITE_ACCESS']

    if write_access == 'public':
        return True

    return flask_login.current_user.has_role (write_access)


def auth ():
    """ Check if user is authorized to see what follows. """

    if not user_can_read (current_app):
        raise PrivilegeError ('You don\'t have %s privilege.' % read_access)


def edit_auth ():
    """ Check if user is authorized to edit. """

    if not user_can_write (current_app):
        raise PrivilegeError ('You don\'t have %s privilege.' % write_access)


def make_safe_url (url):
    """Turns an unsafe absolute URL into a safe relative URL
    by removing the scheme and the hostname

    Example: make_safe_url('http://hostname/path1/path2?q1=v1&q2=v2#fragment')
             returns: '/path1/path2?q1=v1&q2=v2#fragment

    Copied from flask_user/views.py because it was defective.
    """

    parts = urllib.parse.urlsplit (url)
    return urllib.parse.urlunsplit ( ('', '', parts[2], parts[3], parts[4]) )


def declare_user_model_on (db): # db = flask_sqlalchemy.SQLAlchemy ()
    """ Declare the user model on flask_sqlalchemy. """

    # global User, Role, Roles_Users
    # pylint: disable=protected-access

    class User (db.Model, dbx._User, UserMixin):
        __tablename__ = 'user'

        roles = db.relationship (
            'Role',
            secondary = 'roles_users',
            backref = db.backref ('users', lazy='dynamic')
        )

    class Role (db.Model, dbx._Role):
        __tablename__ = 'role'

    class Roles_Users (db.Model, dbx._Roles_Users):
        __tablename__ = 'roles_users'

    return User, Role, Roles_Users


class AnonymousUserMixin (flask_login.AnonymousUserMixin):
    '''
    This is the default object for representing an anonymous user.
    '''

    def __init__ (self):
        self.id = 666

    def has_role (self, *_specified_role_names):
        return False


@bp.route ('/user/after_login')
def after_login ():
    return flask.redirect (current_app.config['AFTER_LOGIN_URL'])
