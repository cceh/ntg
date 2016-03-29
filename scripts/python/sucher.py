#!/usr/bin/python
#-*- encoding: utf-8 -*-

__author__ = "volker.krueger@uni-muenster.de"

import sys

def main(table):
    import db_access3
    DB = "ECM_Acts_CBGMPh2"
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
    cmd = "select count(*) from %s.%s" % (DB, TABLE)
    cursor.execute(cmd)
    res = cursor.fetchone()
    SUM = res[0]
    if SUM == PASSCOUNT * HSNRCOUNT:
        print "magisches Produkt stimmt"
    else:
        cmd = "select distinct hsnr from %s.%s " % (DB, TABLE)
        cursor.execute(cmd)
        hsnrs = cursor.fetchall()
        for hsnr in hsnrs:
            cmd = "select count(hsnr) from %s.%s where hsnr = %d " % (DB, TABLE, hsnr[0])
            cursor.execute(cmd)
            c = cursor.fetchone()
            if int(c[0]) != PASSCOUNT:
                print hsnr
                if int(c[0]) > PASSCOUNT:
                    # Jede Handschrift darf es pro variierter Stelle nur einmal geben
                    passages, void = dba.getPassages(DB, TABLE)
                    for passage in passages:
                        cmd  = "select id from %s.%s " % (DB, TABLE)
                        cmd += "where anfadr = %d and endadr = %d and hsnr = %d " % (passage[0], passage[1], hsnr[0])
                        cursor.execute(cmd)
                        res = cursor.fetchall()
                        if len(res) > 1:
                            print "\tBei %d/%d ist der Zeuge mehrfach verzeichnet. Vgl. ID:" % (passage[0], passage[1])
                            print "\t", res
                else:
                    print "\t%s" % (c[0])
    cursor.close()
    dba.close()

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print "Please enter table name as single parameter"
        sys.exit(1)
    main(sys.argv[1])