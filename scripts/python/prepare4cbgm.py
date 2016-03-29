#!/usr/bin/python
#-*- encoding: utf-8 -*-
"""
9. Stellenbezogene Lueckenliste fuellen
    9.0. Vorhandene Tabelle leeren
    9.1. Alle Passages auflisten
    9.2. Alle Handschriften der Systematischen Lueckenliste auflisten
    9.3. Schleife ueber alle Handschriften
    9.4. Schleife ueber alle Passages
    9.5. Eintrag in ActsNNattLac, wenn die Handschrift an genannter Stelle
         in der Systematischen Lueckenliste verzeichnet ist
"""
__author__="volker.krueger@uni-muenster.de"

def enter2LocalLacList(cursor, hs, db, lactable, anfadr, endadr):
    import Address
    b, bc, bv, bw, ec, ev, ew = Address.decodeAdr(anfadr, endadr)
    hsnr = Address.hs2hsnr(hs)
    cmd  = "insert into %s.%s " % (db, lactable)
    cmd += "(buch, kapanf, versanf, wortanf, kapend, versend, wortend, "
    cmd += "anfadr, endadr, hs, hsnr, anfalt, endalt) "
    cmd += "values (%d, %d, %d, %d, %d, %d, %d, " % (b, bc, bv, bw, ec, ev, ew)
    cmd += "%d, %d, '%s', %d, %d, %d) " % (anfadr, endadr, hs, hsnr, anfadr, endadr)
    cursor.execute(cmd)

def main_9(db1, db2, tab1, tab2, mode="remote"):
    import db_access3
    dba = db_access3.DBA(mode)
    cursor = dba.cursor()
    sourcetable = tab1
    lactable = sourcetable + "Lac"
    # 0. Truncate table
    cmd  = "truncate %s.%s " % (db1, lactable)
    cursor.execute(cmd)
    dba.commit()
    # 1.1.
    passages, passcount = dba.getPassages(db1, sourcetable)
    # 1.2.
    cmd  = "select distinct hs from %s.%s " % (db2, tab2)
    cmd += "order by hsnr "
    cursor.execute(cmd)
    mss = cursor.fetchall()
    # 1.3.
    for ms in mss:
        hs = ms[0]
        for passage in passages:
            anfadr = passage[0]
            endadr = passage[1]
            cmd  = "select count(id) from %s.%s " % (db2, tab2)
            cmd += "where anfadr <= %d and endadr >= %d " % (anfadr, endadr)
            cmd += "and hs = '%s' " % (hs)
            cursor.execute(cmd)
            result = cursor.fetchone()
            rescount = result[0]
            if rescount > 0:
                enter2LocalLacList(cursor, hs, db1, lactable, anfadr, endadr)
    dba.commit() # it's an InnoDB table
    cursor.close()
    dba.close()

if __name__ == "__main__":
    from optparse import OptionParser
    import sys, time
    print time.ctime()
    parser = OptionParser()
    parser.add_option("-d", "--database", dest="database", help="Giving database")
    parser.add_option("-m", "--mode", dest="mode", help="choose 'local' or 'remote' database access, 'remote' is default")
    parser.add_option("-t", "--table", dest="table", help="Giving table name attestations")
    parser.add_option("-e", "--ref_db", dest="ref_db", help="Database of lacuna table")
    parser.add_option("-l", "--lactable", dest="lactable", help="Systematic lacunae table")
    (opts, args) = parser.parse_args()
    parser.destroy()
    if opts.database == None or opts.table == None or opts.ref_db == None:
        print "Error: At least one parameter necessary is missing!"
        print "See python %s -h" % sys.argv[0]
        sys.exit(1)
    main_9(opts.database, opts.ref_db, opts.table, opts.lactable)
    print "%s finished at %s" % (sys.argv[0], time.ctime())