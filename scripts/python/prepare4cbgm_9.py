#!/usr/bin/python
# -*- encoding: utf-8 -*-
"""
9. Stellenbezogene Lueckenliste fuellen
    9.0. Vorhandene Tabelle leeren
    9.1. Alle Passages auflisten
    9.2. Alle Handschriften der Systematischen Lueckenliste auflisten
    9.3. Schleife ueber alle Handschriften
    9.4. Schleife ueber alle Passages
    9.5. Eintrag in ActsNNattLac, wenn die Handschrift an
         genannter Stelle in der Systematischen Lueckenliste verzeichnet ist

Vgl. die Datei ArbeitsablaufCBGMApg1.pdf in der Mail
von Klaus am 25.01.2012
"""
__author__ = "volker.krueger@uni-muenster.de"


def enter2LocalLacList(cursor, hs, db, lactable, anfadr, endadr):
    """
    Insert new dataset into resulting table.
    """
    import Address
    b, bc, bv, bw, ec, ev, ew = Address.decodeAdr(anfadr, endadr)
    hsnr = Address.hs2hsnr(hs)
    cmd = "insert into %s.%s " % (db, lactable)
    cmd += "(buch, kapanf, versanf, wortanf, kapend, versend, wortend, "
    cmd += "anfadr, endadr, hs, hsnr, anfalt, endalt) "
    cmd += "values (%d, %d, %d, %d, %d, %d, %d, " % (b, bc, bv, bw,
                                                     ec, ev, ew)
    cmd += "%d, %d, '%s', %d, %d, %d)" % (anfadr, endadr, hs, hsnr,
                                          anfadr, endadr)
    #print cmd
    cursor.execute(cmd)


def getSysLacTable(cursor, db, sChapter):
    """
    Looking for the name of the systematic lacuna table.
    """
    pattern = "Acts" + sChapter + "%lac"
    cmd = "use `%s`" % (db)
    cursor.execute(cmd)
    cmd = "show tables like '%s'" % (pattern)
    cursor.execute(cmd)
    tables = cursor.fetchall()
    #print tables
    return tables[0][0]


def main_9(db1, db2, chapter, verbose=False):
    def printer(s):
        """
        Print information if needed.
        """
        if verbose:
            print s
    import access
    import db_access3
    dba = db_access3.DBA(access.get())
    cursor = dba.cursor()
    # Generate name of newtable and lactable
    sChapter = str(chapter)
    if int(chapter) < 10:
        sChapter = "0" + sChapter
    newtable = "Acts" + sChapter + "att"
    lactable = newtable + "Lac"
    if db1.endswith("2"):
        newtable += "_2"
        lactable += "_2"
    if db1.endswith("3"):
        newtable += "_3"
        lactable += "_3"
    # Query systematic lacuna table name
    sys_lac_table = getSysLacTable(cursor, db2, sChapter)
    # 9.0. Truncate lacuna table
    cmd = "truncate %s.%s " % (db1, lactable)
    printer(cmd)
    cursor.execute(cmd)
    dba.commit()
    # 9.1.
    passages, passcount = dba.getPassages(db1, newtable)
    # 9.2.
    cmd = "select distinct hs from %s.%s " % (db2, sys_lac_table)
    cmd += "order by hsnr "
    printer(cmd)
    cursor.execute(cmd)
    mss = cursor.fetchall()
    # get max endadr
    cmd = "select max(endadr) from `%s`.`%s` " % (db2, sys_lac_table)
    cursor.execute(cmd)
    result = cursor.fetchone()
    max_endadr = result[0]
    # 9.3.
    for ms in mss:
        hs = ms[0]
        # 9.4.
        for passage in passages:
            anfadr = passage[0]
            endadr = passage[1]
            cmd = "select count(id) from %s.%s " % (db2, sys_lac_table)
            if endadr < max_endadr:
                cmd += "where anfadr <= %d and endadr >= %d " % (anfadr,
                                                                 endadr)
            else:
                cmd += "where anfadr <= %d and endadr >= %d " % (anfadr,
                                                                 endadr-1)
            cmd += "and hs = '%s' " % (hs)
            printer(cmd)
            cursor.execute(cmd)
            result = cursor.fetchone()
            rescount = result[0]
            # 9.5.
            if rescount > 0:
                enter2LocalLacList(cursor, hs, db1, lactable, anfadr, endadr)
    dba.commit()  # it's an InnoDB table
    cursor.close()
    dba.close()

if __name__ == "__main__":
    from optparse import OptionParser
    parser = OptionParser()
    parser.add_option("-d", "--database", dest="database",
                      help="Giving database")
    parser.add_option("-e", "--ref_db", dest="ref_db",
                      help="Database of lacuna table")
    parser.add_option("-c", "--chapter", dest="chapter",
                      help="Chapter number")
    parser.add_option("-v", "--verbose", dest="verbose",
                      action="store_true", help="Verbose mode")
    (opts, args) = parser.parse_args()
    parser.destroy()
    if opts.database is None or opts.ref_db is None or opts.chapter is None:
        import sys
        print "Error: At least one parameter necessary is missing!"
        print "See python %s -h" % sys.argv[0]
        sys.exit(1)
    main_9(opts.database, opts.ref_db, opts.chapter, opts.verbose)