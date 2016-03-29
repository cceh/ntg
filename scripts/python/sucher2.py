#!/usr/bin/python
#-*- encoding: utf-8 -*-

__author__ = "volker.krueger@uni-muenster.de"

import sys

def main(table):
    import db_access3
    DB = "ECM_Acts_CBGM"
    TABLE = table
    dba = db_access3.DBA("remote")
    cursor = dba.cursor()
    cmd = "select count(distinct anfadr, endadr) from %s.%s " % (DB, TABLE)
    cursor.execute(cmd)
    res = cursor.fetchone()
    PASSCOUNT = res[0]
    print "%s hat %d variierte Stellen." % (TABLE, PASSCOUNT)
    cmd = "select count(distinct hsnr) from %s.%s " % (DB, TABLE)
    cursor.execute(cmd)
    res = cursor.fetchone()
    HSNRCOUNT = res[0]
    print "%s hat %d Handschriften." % (TABLE, HSNRCOUNT)
    cmd = "select distinct hsnr from %s.%s " % (DB, TABLE)
    cursor.execute(cmd)
    hsnrs = cursor.fetchall()
    cmd = "select distinct anfadr, endadr from %s.%s " % (DB, TABLE)
    cursor.execute(cmd)
    passages = cursor.fetchall()
    for hsnr in hsnrs:
        for passage in passages:
            cmd  = "select count(id) from %s.%s " % (DB, TABLE)
            cmd += "where hsnr = %d " % (hsnr[0])
            cmd += "and anfadr = %d and endadr = %d " % (passage[0], passage[1])
            cursor.execute(cmd)
            res = cursor.fetchone()
            if res[0] != 1:
                print "Fehler bei Handschrift %d an Stelle %d/%d. " % (hsnr[0], passage[0], passage[1])
    cursor.close()
    dba.close()

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print "Please enter table name as single parameter"
        sys.exit(1)
    main(sys.argv[1])