#!/usr/bin/python3
# -*- encoding: utf-8 -*-

"""Initialize the database for user authentication and authorization."""

import argparse
import datetime
import logging

from passlib.context import CryptContext

from ntg_common import db
from ntg_common.db_tools import execute
from ntg_common.tools import log
from ntg_common.config import init_cmdline


def build_parser ():
    parser = argparse.ArgumentParser (description = __doc__)

    parser.add_argument ('profile', metavar='path/to/_global.conf',
                         help="path to the _global.conf file (required)")

    parser.add_argument ('-e', '--email',    required = True, help='email')
    parser.add_argument ('-u', '--username', default = '',    help='username')
    parser.add_argument ('-p', '--password', default = '',    help='password')

    parser.add_argument ('-v', '--verbose', dest='verbose', action='count',
                         help='increase output verbosity', default=0)
    return parser


if __name__ == '__main__':

    args, config = init_cmdline (build_parser ())

    dba = db.PostgreSQLEngine (**config)

    db.Base3.metadata.drop_all   (dba.engine)
    db.Base3.metadata.create_all (dba.engine)

    pwd_context = CryptContext (schemes = [ config['USER_PASSWORD_HASH'] ])

    with dba.engine.begin () as src:
        execute (src, "INSERT INTO role (id, name, description) VALUES (1, 'admin',  'Administrator')", {})
        execute (src, "INSERT INTO role (id, name, description) VALUES (2, 'editor', 'Editor')", {})

        if args.email:
            params = {
                "username"     : args.username,
                "email"        : args.email,
                "password"     : pwd_context.hash (args.password) if args.password else '',
                "active"       : True,
                "confirmed_at" : datetime.datetime.now ()
            }

            execute (src,
                     "INSERT INTO \"user\" (id, username, email, password, active, confirmed_at) " +
                     "VALUES (1, :username, :email, :password, :active, :confirmed_at)",
                     params)
            execute (src, "INSERT INTO roles_users (id, user_id, role_id) VALUES (1, 1, 1)", {})
            execute (src, "INSERT INTO roles_users (id, user_id, role_id) VALUES (2, 1, 2)", {})
