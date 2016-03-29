#!/usr/bin/python
# -*- encoding: utf-8 -*-
"""
10. Bezeugung der a-Lesarten auffuellen. Sie setzt sich zusammen aus allen
    in der 'ActsMsList' fuer das jeweilige Kapitel gefuehrten Handschriften,
    die an der jeweils bearbeiteten Stelle noch nicht bei einer Variante
    oder in der Lueckenliste stehen.

    Besondere Aufmerksamkeit ist bei den Fehlversen notwendig:
    Im Bereich der Fehlverse darf nicht einfach die a-Bezeugung
    aufgefuellt werden. Stattdessen muss, wenn die variierte Stelle
    zu einer umfassten Einheit gehoert und das Feld 'base' den
    Inhalt 'a' hat, die neue Lesartenbezeichnung 'zu' eingetragen werden.
    'base = b' steht für eine alternative Subvariante (dem Textus receptus).

    Eine variierte Stelle ist eine umfasste Stelle, wenn comp = 'x' ist.

Vgl. die Datei ArbeitsablaufCBGMApg1.pdf in der Mail
von Klaus am 25.01.2012

Ergänzung vom 13.03.2015:
Das Skript arbeitet mit zwei Unterabfragen auf die Bezeugungstabelle und 
auf die stellenbezogene Lückenliste. Die Performance kann man dabei spürbar 
erhöhen, wenn man je einen Index auf das gesuchte Feld HSNR erstellt:
CREATE INDEX hsnr_index ON ActsNNatt (hsnr);
CREATE INDEX hsnr_index ON ActsNNattLac (hsnr);
"""
__author__ = "volker.krueger@uni-muenster.de"


def main_10(database, chapter, verbose=False):
    def printer(s):
        """
        Print information if needed.
        """
        if verbose:
            print s
    import access
    import db_access3
    from Address import formatNumber, decodeAdr
    dba = db_access3.DBA(access.get())
    cursor = dba.cursor()
    databaseAtt = database
    # Generate name of newtable and lactable
    sChapter = str(chapter)
    if int(chapter) < 10:
        sChapter = "0" + sChapter
    tableAtt = "Acts" + sChapter + "att"
    tableAttLac = tableAtt + "Lac"
    if database.endswith("2"):
        tableAtt += "_2"
        tableAttLac += "_2"
    if database.endswith("3"):
        tableAtt += "_3"
        tableAttLac += "_3"

    databaseList = "ECM_Acts_Mss"
    tableList = "ActsMsList_2"  # "ActsMsList"
    pattern = "Apg" + formatNumber(chapter, 2)
    # Alle variierten Stellen mit ihren a-Lesarten
    cmd = "select distinct anfadr, endadr, lesart, labez, base "
    cmd += "from `%s`.`%s` " % (databaseAtt, tableAtt)
    cmd += "where `hs` = 'A' "
#    cmd += "where (labez like 'a' and labezsuf like '' and base like 'a') "
#    cmd += "or (labez like 'b' and labezsuf like '' and base like 'b') "
#    cmd += "order by anfadr asc, endadr desc "
#    print cmd
    cursor.execute(cmd)
    passages = cursor.fetchall()
    for passage in passages:
        anfadr = passage[0]
        endadr = passage[1]
        s = "Working on %d/%d." % (anfadr, endadr)
        printer(s)
        lesart = passage[2]
        labez = passage[3]
        base = passage[4]
        if lesart is None:
            lesart = ""
        b, bc, bv, bw, ec, ev, ew = decodeAdr(anfadr, endadr)
        # Alle Handschriften, die in diesem Kapitel Text,
        # d.h. keine Lücke haben, die das ganze Kapitel umfasst.
        # 1. 'a' auffuellen
        cmd = "insert into `%s`.`%s` " % (databaseAtt, tableAtt)
        cmd += "(hsnr, hs, anfadr, endadr, buch, kapanf, versanf, wortanf, "
        cmd += "kapend, versend, wortend, labez, labezsuf, anfalt, endalt, "
        cmd += "lesart, base) "
        cmd += "select ms, witn, %d, %d, " % (anfadr, endadr)
        cmd += "%d, %d, %d, %d, " % (b, bc, bv, bw)
        cmd += "%d, %d, %d, " % (ec, ev, ew)
        cmd += "'%s', '', " % (labez)
        cmd += "%d, " % (anfadr)
        cmd += "%d, " % (endadr)
        cmd += "'%s', " % (lesart.decode("utf-8"))
        cmd += "'%s' " % (base)
        cmd += "from `%s`.`%s` " % (databaseList, tableList)  # ActsMsList
        cmd += "where %s = 1 " % (pattern)
        cmd += "and ms not in (select hsnr from `%s`.`%s` " % (databaseAtt,
                                                               tableAttLac)
        cmd += "where anfadr >= %d and endadr <= %d) " % (anfadr, endadr)
        cmd += "and ms not in (select hsnr from `%s`.`%s` " % (databaseAtt,
                                                               tableAtt)
        cmd += "where anfadr = %d and endadr = %d ) " % (anfadr, endadr)
        cmd += "order by ms "
        cursor.execute(cmd)
        dba.commit()
        # 2. 'zz' auffuellen
        cmd = "insert into `%s`.`%s` " % (databaseAtt, tableAtt)
        cmd += "(hsnr, hs, anfadr, endadr, buch, kapanf, versanf, wortanf, "
        cmd += "kapend, versend, wortend, labez, labezsuf, anfalt, endalt, "
        cmd += "lesart) "
        cmd += "select ms, witn, %d, %d, " % (anfadr, endadr)
        cmd += "%d, %d, %d, %d, " % (b, bc, bv, bw)
        cmd += "%d, %d, %d, 'zz', '', %d, %d, '%s' " % (ec, ev, ew, anfadr,
                                                        endadr, lesart)
        cmd += "from `%s`.`%s` " % (databaseList, tableList)
        cmd += "where %s = 1 " % (pattern)
        cmd += "and ms not in (select hsnr from `%s`.`%s` " % (databaseAtt,
                                                               tableAtt)
        cmd += "where anfadr = %d and endadr = %d ) " % (anfadr, endadr)
        cmd += "order by ms "
        cursor.execute(cmd)
        dba.commit()
        # Ergaenzendes Update zur korrekten Verzeichnung der Fehlverse
        # 3. Update der umfassten variierten Stellen
        # Das Feld 'comp' wird durch das Skript umfasstevarianten.py
        # beschrieben und kennzeichnet umfasste Varianten.
        cmd = "update `%s`.`%s` " % (databaseAtt, tableAtt)
        cmd += "set labez = 'zu', "
        cmd += "lesart = '' "
        cmd += "where comp like 'x' and base like 'a' "
        # Adressen der Fehlverse hier hart kodieren:
        # vgl. die Datenbanktabelle Apparat.Fehlverse.
        # Diese Adressen schließen Additamenta ein.
        cmd += "and ("
        cmd += "anfadr >= 50837002 and endadr <= 50837047 "
        cmd += "or anfadr >= 51534002 and endadr <= 51534013 "
        cmd += "or anfadr >= 52506020 and endadr <= 52408015 "
        cmd += "or anfadr >= 52829002 and endadr <= 52829025 "
        cmd += "); "
        cursor.execute(cmd)
        dba.commit()
        ## Weitere Ergaenzung:
        ## 4. Quelle der b-Lesarten gilt als urspruenglich, alle
        ## anderen Lesarten stammen per default von b ab.
        #cmd = "update `%s`.`%s` " % (databaseAtt, tableAtt)
        #cmd += "set s1 = '*' "
        #cmd += "where labez = 'b' and ("
        #cmd += "anfadr >= 50837002 and endadr <= 50837047 "
        #cmd += "or anfadr >= 51534002 and endadr <= 51534013 "
        #cmd += "or anfadr >= 52506020 and endadr <= 52408015 "
        #cmd += "or anfadr >= 52829002 and endadr <= 52829025) "
        #cursor.execute(cmd)  # FIXME: TESTEN
        #cmd = "update `%s`.`%s` " % (databaseAtt, tableAtt)
        #cmd += "set s1 = 'b' "
        #cmd += "where labez <> 'b' and ("
        #cmd += "anfadr >= 50837002 and endadr <= 50837047 "
        #cmd += "or anfadr >= 51534002 and endadr <= 51534013 "
        #cmd += "or anfadr >= 52506020 and endadr <= 52408015 "
        #cmd += "or anfadr >= 52829002 and endadr <= 52829025) "
        #cursor.execute(cmd)  # FIXME: TESTEN
    # Nachbesserung: zz-Zeugen haben keine Lesart
    cmd = "update `%s`.`%s` " % (databaseAtt, tableAtt)
    cmd += "set lesart = '' where labez = 'zz' "
    cursor.execute(cmd)
    dba.commit()
    cursor.close()
    dba.close()

if __name__ == "__main__":
    from optparse import OptionParser
    parser = OptionParser()
    parser.add_option("-d", "--database", dest="database",
                      help="Giving database name")
    parser.add_option("-c", "--chapter", dest="chapter",
                      help="Chapter to add a-testation")
    parser.add_option("-v", "--verbose", dest="verbose",
                      action="store_true", help="Verbose mode")
    (opts, args) = parser.parse_args()
    parser.destroy()
    if opts.database is None or opts.chapter is None:
        import sys
        print "At least one parameter is missing!"
        print "See python %s -h" % sys.argv[0]
        sys.exit(1)
    main_10(opts.database, opts.chapter, opts.verbose)
