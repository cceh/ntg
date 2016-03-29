#!/usr/bin/python
#-*- encoding: utf-8 -*-

__author__ = "volker.krueger@uni-muenster.de"

import sys

def main(table):
    import access
    import db_access3
    DB = "VarGenAtt_ActPh3"
    TABLE = table
    dba = db_access3.DBA(access.get())
    cursor = dba.cursor()
    cmd = "select count(distinct begadr, endadr) from %s.%s " % (DB, TABLE)
    cursor.execute(cmd)
    res = cursor.fetchone()
    PASSCOUNT = res[0]
    print "%s hat %d variierte Stellen." % (TABLE, PASSCOUNT)
    cmd = "select count(distinct ms) from %s.%s " % (DB, TABLE)
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
        cmd = "select distinct ms from %s.%s " % (DB, TABLE)
        cursor.execute(cmd)
        hsnrs = cursor.fetchall()
        for hsnr in hsnrs:
            cmd = "select count(ms) from %s.%s where ms = %d " % (DB, TABLE, hsnr[0])
            cursor.execute(cmd)
            c = cursor.fetchone()
            count = int(c[0])
            if count != PASSCOUNT:
                print hsnr
                if count != PASSCOUNT:
                    # Jede Handschrift darf es pro variierter Stelle nur einmal geben
                    cmd = "select distinct begadr, endadr from %s.%s " % (DB, TABLE)
                    cursor.execute(cmd)
                    passages = cursor.fetchall()
                    for passage in passages:
                        cmd  = "select varid, witn from %s.%s " % (DB, TABLE)
                        cmd += "where begadr = %d and endadr = %d and ms = %d " % (passage[0], passage[1], hsnr[0])
                        cursor.execute(cmd)
                        res = cursor.fetchall()
                        if len(res) > 1:
                            print "\tBei %d/%d ist der Zeuge mehrfach verzeichnet. Vgl. ID:" % (passage[0], passage[1])
                            print "\t", res
                        else:
                            print "\t%s" % (count)
                            break
    cursor.close()
    dba.close()

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print "Please enter table name as single parameter"
        sys.exit(1)
    main(sys.argv[1])
