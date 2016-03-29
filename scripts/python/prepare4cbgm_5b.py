#!/usr/bin/python
# -*- encoding: utf-8 -*-
"""
5b. 20. Mai 2015
Commentary manuscripts like 307 cannot be treated like lectionaries where we
choose the first text. If a T1 or T2 reading is found they have to be
deleted. A new zw reading is created containing the old readings as suffix.

This has to be done as long as both witnesses are present.

If the counterpart of one entry belongs to the list of lacunae
the witness will be treated as normal witness. The T notation can be deleted.
"""
__author__ = "volker.krueger@uni-muenster.de"


def getTableName(cursor, database, chapter):
    """
    Tabellennamen aus chapter generieren.
    Es gibt eine Apparattabelle und eine Lückenliste pro Kapitel.
    """
    table = ""
    sChapter = str(chapter)
    if int(chapter) < 10:
        sChapter = "0" + sChapter
    cmd = "SHOW TABLES FROM %s LIKE 'Acts%s%%';" % (database, sChapter)
    cursor.execute(cmd)
    tables = cursor.fetchall()
    for t in tables:
        s = str(t[0])
        if s.endswith("lac"):
            continue
        table = s
    return table

def main_5b(database, chapter, verbose=False):
    def printer(s):
        """
        Print information if needed.
        """
        if verbose:
            print s
    import access
    import db_access3
    # Open handles
    dba = db_access3.DBA(access.get())
    cursor = dba.cursor()
    # Choose database
    cmd = "USE %s;" % (database)
    cursor.execute(cmd)
    dba.commit()
    table = getTableName(cursor, database, chapter)
    # Select T+number witnesses ordered by addresses
    cmd = "SELECT DISTINCT `ANFADR`, `ENDADR` FROM `%s`.`%s` " % (database, table)
    cmd += "WHERE `HS` LIKE '%%T%%' "
    cmd += "ORDER BY `ANFADR`, `ENDADR` DESC;"
    cursor.execute(cmd)
    addresses = cursor.fetchall()
    for adr in addresses:
        anf = adr[0]
        end = adr[1]
        cmd = "SELECT DISTINCT `HSNR` FROM `%s`.`%s` " % (database, table)
        cmd += "WHERE `ANFADR` = %s AND `ENDADR` = %s " % (anf, end)
        cmd += "AND `HS` LIKE '%%T%%';"
        cursor.execute(cmd)
        hss = cursor.fetchall()
        for hsnr in hss:
            # three lists to store information:
            del_ids = []
            labez_s = []
            labezsuf_s = []
            cmd = "SELECT `ID`, `HS`, `LABEZ`, `ANFADR`, `ENDADR`, `BUCH`, "
            cmd += "`KAPANF`, `VERSANF`, `WORTANF`, `KAPEND`, `VERSEND`, `WORTEND`, "
            cmd += "`HSNR`, `LABEZSUF` "
            cmd += "FROM `%s`.`%s` " % (database, table)
            cmd += "WHERE `HS` LIKE '%%T%%' "
            cmd += "AND `ANFADR` = %s AND `ENDADR` = %s " % (anf, end)
            cmd += "AND `HSNR` = %s " % (hsnr)
            cmd += "ORDER BY `LABEZ`, `LABEZSUF`;"
            count = cursor.execute(cmd)
            if count == 1:
                # the counterpart seems to be a lacuna: treat this entry as
                # normal witness and delete the T notation
                row = cursor.fetchone()
                ident = row[0]
                hs = row[1]
                pos = hs.find("T")
                hs = hs[:len(hs)-2] # chop off T1 etc.
                cmd = "UPDATE `%s`.`%s` " % (database, table)
                cmd += "SET HS = '%s' " % (hs)
                cmd += "WHERE id = %s;" % (ident)
                print cmd
#               cursor.execute(cmd)
            else: # count > 1
                rows = cursor.fetchall()
                for row in rows:
                    del_ids.append(row[0])
                    labez_s.append(row[2])
                    labezsuf_s.append(row[13])
                    book = row[5]
                    bc = row[6]
                    bv = row[7]
                    bw = row[8]
                    ec = row[9]
                    ev = row[10]
                    ew = row[11]
                    anf = row[3]
                    end = row[4]
                    labez = row[2]
                    hs = row[1]
                    hsnr = row[12]
                    pos = hs.find("T")
                    hs = hs[:pos]
                # Delete these witnesses
                for i in del_ids:
                    cmd = "DELETE FROM `%s`.`%s` " % (database, table)
                    cmd += "WHERE `ID` = %d;" % (i)
                    print cmd
#                    cursor.execute(cmd)
                # Insert a new zw reading
                suffix2 = ""
                for n in range(len(del_ids)):
                    l1 = labez_s[n]
                    l2 = labezsuf_s[n]
                    suffix2 = suffix2 + l1
                    if len(l2) > 0:
                        suffix2 = suffix2 + "_" + l2
                    suffix2 = suffix2 + "/"
                suffix2 = suffix2[:len(suffix2)-1] # chop off last slash
                cmd = "INSERT INTO `%s`.`%s` " % (database, table)
                cmd += "(BUCH, KAPANF, VERSANF, WORTANF, KAPEND, VERSEND, WORTEND, "
                cmd += "ANFADR, ENDADR, LABEZ, LABEZSUF, HS, HSNR) VALUES ("
                cmd += "%d, %d, %d, %d, %d, %d, %d, " % (book, bc, bv, bw, ec, ev, ew)
                cmd += "%d, %d, 'zw', '%s', '%s', %d" % (anf, end, suffix2, hs, hsnr)
                cmd += ");"
                print cmd
#               cursor.execute(cmd)
    # Inno-DB tables need an explicit commit statement
    dba.commit()
    # Close handles
    cursor.close()
    dba.close()

if __name__ == "__main__":
    from optparse import OptionParser
    parser = OptionParser()
    parser.add_option("-d", "--database", dest="database",
                      help="Giving database name")
    parser.add_option("-c", "--chapter", dest="chapter",
                      help="Giving chapter number")
    parser.add_option("-v", "--verbose", dest="verbose",
                      action="store_true", help="Verbose mode")
    (opts, args) = parser.parse_args()
    parser.destroy()
    if opts.database is None or opts.chapter is None:
        import sys
        print "At least one parameter necessary is missing!"
        print "See python %s -h" % sys.argv[0]
        sys.exit(1)
    main_5b(opts.database, opts.chapter, opts.verbose)