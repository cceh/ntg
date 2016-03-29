#!/usr/bin/python
# -*- encoding: utf-8 -*-
"""
6. Lesarten, die nicht von der ersten Hand stammen, loeschen.
Bei mehreren Lektionslesarten gilt die L1-Lesart.
Ausnahme: Bei Selbstkorrekturen wird die *-Lesart geloescht und die
C*-Lesart beibehalten.

Erweiterung vom 15.02.2013: Wenn die einzige Variante an einer Stelle
nur von einem oder mehreren Korrektoren bezeugt ist (z.B. 26:8/17),
gehoert die Stelle nicht in die Tabelle.
Es muss also noch eine Pruefung stattfinden, ob nach diesem Vorgang
eine Stelle noch immer eine variierte Stelle ist. Wenn nicht, kann
der Datensatz geloescht werden.

Vgl. die Datei ArbeitsablaufCBGMApg1.pdf in der Mail
von Klaus am 25.01.2012
"""
__author__ = "volker.krueger@uni-muenster.de"


def main_6(database, chapter, verbose=False):
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
    # Tabellennamen aus chapter generieren
    sChapter = str(chapter)
    if int(chapter) < 10:
        sChapter = "0" + sChapter
    table = "Acts" + sChapter + "att"
    if database.endswith("2"):
        table += "_2"
    if database.endswith("3"):
        table += "_3"
    # Zuerst die einfachen Faelle:
    cmd = "delete from `%s`.`%s` " % (database, table)
    cmd += "where (lekt = 'L2' or korr in ('C', 'C1', 'C2', 'C3', 'A', 'K')) "
    cmd += "and suffix2 <> '%C*%' "
    printer(cmd)
    cursor.execute(cmd)
    # Nachbesserung notwendig:
    cmd = "delete from `%s`.`%s` " % (database, table)
    cmd += "where suffix2 like '%L2%' or suffix2 like '%A%' "
    cmd += "or suffix2 like '%K%' "
    printer(cmd)
    cursor.execute(cmd)
    # Sonderfall Selbstkorrektur: C*
    cmd = "select anfadr, endadr, hsnr from `%s`.`%s` " % (database, table)
    cmd += "where suffix2 like '%%C*' "
    cursor.execute(cmd)
    rows = cursor.fetchall()
    for row in rows:
        anfadr = row[0]
        endadr = row[1]
        hsnr = row[2]
        cmd = "delete from `%s`.`%s` " % (database, table)
        cmd += "where anfadr = %s and endadr = %s " % (anfadr, endadr)
        cmd += "and hsnr = %d " % (hsnr)
        cmd += "and suffix2 like '%%*%%' and suffix2 not like '%%C*' "
        printer(cmd)
        cursor.execute(cmd)
    dba.commit()
    # Eintraege loeschen, die nun keine Varianten mehr haben
    passages, void = dba.getPassages(database, table)
    for p in passages:
        anfadr = p[0]
        endadr = p[1]
        cmd = "select count(distinct labez) "
        cmd += "from `%s`.`%s` " % (database, table)
        cmd += "where anfadr = %d and endadr = %d " % (anfadr, endadr)
        cmd += "and labez not like 'a' and labez not like 'z%%'"
        cursor.execute(cmd)
        res = cursor.fetchone()
        if res[0] == 0:
            cmd = "delete from `%s`.`%s` " % (database, table)
            cmd += "where anfadr = %d and endadr = %d " % (anfadr, endadr)
            printer(cmd)
            cursor.execute(cmd)
    dba.commit()
    # Eintraege - Ende
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
    main_6(opts.database, opts.chapter, opts.verbose)