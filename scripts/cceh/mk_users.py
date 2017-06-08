#!/usr/bin/python3
# -*- encoding: utf-8 -*-

"""Initialize the tables for user authentication and authorization.

"""

import argparse
import datetime
import logging
import os
import sys

import sqlalchemy
from passlib.context import CryptContext

sys.path.append (os.path.dirname (os.path.abspath (__file__)) + "/../..")

from ntg_common import db
from ntg_common import tools
from ntg_common.db import execute
from ntg_common.tools import log
from ntg_common.config import args

if __name__ == '__main__':

    parser = argparse.ArgumentParser (description='Initialize the tables for user auth.')

    parser.add_argument ('profile', metavar='PROFILE', help="the database profile file (required)")

    parser.add_argument ('-e', '--email',    required = True, help='email')
    parser.add_argument ('-u', '--username', default = '',    help='username')
    parser.add_argument ('-p', '--password', default = '',    help='password')

    parser.add_argument ('-v', '--verbose', dest='verbose', action='count',
                         help='increase output verbosity', default=0)

    parser.parse_args (namespace = args)

    config = tools.config_from_pyfile (args.profile)

    args.start_time = datetime.datetime.now ()
    LOG_LEVELS = { 0: logging.CRITICAL, 1: logging.ERROR, 2: logging.WARN, 3: logging.INFO, 4: logging.DEBUG }
    args.log_level = LOG_LEVELS.get (args.verbose, logging.CRITICAL)

    logging.getLogger ().setLevel (args.log_level)
    formatter = logging.Formatter (fmt = '%(relativeCreated)d - %(levelname)s - %(message)s')

    stderr_handler = logging.StreamHandler ()
    stderr_handler.setFormatter (formatter)
    logging.getLogger ().addHandler (stderr_handler)

    file_handler = logging.FileHandler ('mk_users.log')
    file_handler.setFormatter (formatter)
    logging.getLogger ().addHandler (file_handler)

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
