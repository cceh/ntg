# -*- encoding: utf-8 -*-

"""An application server for CBGM.  User management module.  """

import sqlalchemy
from sqlalchemy import String, Integer, Float, Boolean, DateTime, Column, Index, UniqueConstraint, ForeignKey

from flask_user import UserMixin
import flask_login

from ntg_common import db as dbx


def declare_user_model (db): # db = flask_sqlalchemy.SQLAlchemy ()
    global User, Role, Roles_Users

    class User (db.Model, dbx._User, UserMixin):
        __tablename__ = 'user'

        roles = db.relationship (
            'Role',
            secondary = 'roles_users',
            backref = db.backref ('users', lazy='dynamic')
        )

    class Role (db.Model, dbx._Role):
        __tablename__ = 'role'

        pass

    class Roles_Users (db.Model, dbx._Roles_Users):
        __tablename__ = 'roles_users'

        pass


class AnonymousUserMixin (flask_login.AnonymousUserMixin):
    '''
    This is the default object for representing an anonymous user.
    '''

    def has_role (self, *specified_role_names):
        return False
