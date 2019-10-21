# -*- encoding: utf-8 -*-

"""Save the state of the editor tables.

This script saves the tables containing the editorial decisions.  It does not
save the apparatus tables.

"""

import argparse
import logging
import sys

from ntg_common import db
from ntg_common import db_tools
from ntg_common.db_tools import execute
from ntg_common.tools import log
from ntg_common.config import args, init_logging, config_from_pyfile


def build_parser ():
    parser = argparse.ArgumentParser (description = __doc__)

    parser.add_argument ('-v', '--verbose', dest='verbose', action='count',
                         help='increase output verbosity', default=0)
    parser.add_argument ('-o', '--output', metavar='path/to/output.xml',
                         help="the output file (required)", required=True)
    parser.add_argument ('profile', metavar='path/to/file.conf',
                         help="a .conf file (required)")
    return parser


if __name__ == '__main__':

    build_parser ().parse_args (namespace = args)
    config = config_from_pyfile (args.profile)

    init_logging (
        args,
        logging.StreamHandler (), # stderr
        logging.FileHandler ('save_edits.log')
    )

    book = config['BOOK']
    parameters = dict ()
    db = db_tools.PostgreSQLEngine (**config)

    log (logging.INFO, "Saving changes ...")

    if args.output == '-':
        fp = sys.stdout
    else:
        fp = open (args.output, 'w', encoding='utf-8')

    with db.engine.begin () as conn:
        fp.write ('<?xml version="1.0" encoding="utf-8" ?>\n\n')

        fp.write ('<sql profile="%s">\n' % args.profile)

        res = execute (conn, """
        SELECT (table_to_xml ('export_cliques', true, false, ''))
        """, parameters)

        fp.write (res.fetchone ()[0])
        fp.write ('\n')

        res = execute (conn, """
        SELECT (table_to_xml ('export_ms_cliques', true, false, ''))
        """, parameters)

        fp.write (res.fetchone ()[0])
        fp.write ('\n')

        res = execute (conn, """
        SELECT (table_to_xml ('export_locstem', true, false, ''))
        """, parameters)

        fp.write (res.fetchone ()[0])
        fp.write ('\n')

        res = execute (conn, """
        SELECT (table_to_xml ('export_notes', true, false, ''))
        """, parameters)

        fp.write (res.fetchone ()[0])
        fp.write ('</sql>\n')

    if fp != sys.stdout:
        fp.close ()

    log (logging.INFO, "Done")
