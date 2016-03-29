#!/usr/bin/python
# -*- encoding: utf-8 -*-


"""
Are there passages in the stemma editor where splitted readings
are the source of other readings, being noted incorrectly?
"""
__author__ = "volker.krueger@uni-muenster.de"


def main(database, table, mode="remote"):
    import db_access3
    dba = db_access3.DBA(mode)
    cursor = dba.cursor()
    # get the passages
    cmd = "select distinct begadr, endadr from `%s`.`%s` " % (database, table)
    cursor.execute(cmd)
    rows = cursor.fetchall()
    for r in rows:
        anfadr = r[0]
        endadr = r[1]
        # get the readings and their sources
        cmd = "select varid, varnew from `%s`.`%s` " % (database, table)
        cmd += "where begadr = %d and endadr = %d " % (anfadr, endadr)
        cmd += "and (varnew like '%%1' or "
        cmd += "varnew like '%%2' or "
        cmd += "varnew like '%%3' or "
        cmd += "varnew like '%%4' or "
        cmd += "varnew like '%%5' or "
        cmd += "varnew like '%%6' or "
        cmd += "varnew like '%%7' or "
        cmd += "varnew like '%%8' or "
        cmd += "varnew like '%%9') "
        cursor.execute(cmd)
        result = cursor.fetchall()
        for n in result:
            varid = n[0]
            varnew = n[1]
            # are there any readings having varid instead of varnew as S1 or S2?
            cmd = "select distinct varid, varnew, s1, s2 from `%s`.`%s` " % (database, table)
            cmd += "where begadr = %d and endadr = %d " % (anfadr, endadr)
            cmd += "and (s1 = '%s' or s2 = '%s') " % (varid, varid)
            cmd += "and varid not like 'z%%' "
            cursor.execute(cmd)
            mistakes = cursor.fetchall()
            for m in mistakes:
                print "%d/%d:%s has the wrong source(s): %s" % (anfadr, endadr, varnew, m[2])
    cursor.close()
    dba.close()


if __name__ == '__main__':
    from optparse import OptionParser
    parser = OptionParser()
    parser.add_option("-d", "--database", dest="database")
    parser.add_option("-t", "--table", dest="table")
    (opts, args) = parser.parse_args()
    parser.destroy()
    if opts.database is None or opts.table is None:
        import sys
        print "At least one parameter is missing."
        sys.exit(1)
    main(opts.database, opts.table)