#!/usr/bin/python
# -*- encoding: utf-8 -*-
"""
5. Stellen loeschen, an denen nur eine oder mehrere f- oder
o-Lesarten vom A-Text abweichen.

Nicht löschen, wenn an dieser variierten Stelle eine
Variante 'b' - 'y' erscheint.

Änderung 2014-12-16:
Act 28,29/22 gehört zu einem Fehlvers. Dort gibt es u.U. keine Variante neben
b, sondern nur ein Orthographicum. Wir suchen also nicht mehr noch einer
Variante 'b' bis 'y', sondern zählen die Varianten. Liefert getReadings nur 1
zurück, gibt es keine Varianten.

Vgl. die Datei ArbeitsablaufCBGMApg1.pdf in der Mail
von Klaus am 25.01.2012
"""
__author__ = "volker.krueger@uni-muenster.de"


def main_5(database, chapter, verbose=False):
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
    # Alle variierten Stellen auflisten
    passages, void = dba.getPassages(database, table)
    for passage in passages:
        anfadr = passage[0]
        endadr = passage[1]
        # new code
        # get readings without labezsuf and overlapping variants
        cmd = "select distinct anfadr, endadr, labez "
        cmd += "from `%s`.`%s` " % (database, table)
        cmd += "where anfadr = %s and endadr = %s " % (anfadr, endadr)
        cmd += "and labez not like 'z%%'; "
        count = cursor.execute(cmd)
        if count == 1:
            cmd = "delete from `%s`.`%s` " % (database, table)
            cmd += "where anfadr = %s and endadr = %s " % (anfadr, endadr)
            cursor.execute(cmd)
        # old code
        ## Pro variierter Stelle alle Lesarten auflisten
        #readings, void = dba.getReadings(database, table, anfadr, endadr)
        #HasVariant = False
        #for reading in readings:
        #    labez = reading[2]
        #    # Gibt es eine Lesart anders als 'a' oder 'z...'?
        #    if labez in ("b", "c", "d", "e", "f", "g", "h", "i", "j",
        #                 "k", "l", "m", "n", "o", "p", "q", "r", "s",
        #                 "t", "u", "v", "w", "x", "y"):
        #        HasVariant = True
        #        break
        #if not HasVariant:
        #    # Wenn nicht, dann diesen Eintrag loeschen, da es sich nicht
        #    # um eine variierte Stelle handelt: Es gibt keine Varianten
        #    cmd = "delete from `%s`.`%s` " % (database, table)
        #    cmd += "where anfadr = %s and endadr = %s " % (anfadr, endadr)
        #    printer(cmd)
        #    cursor.execute(cmd)
        dba.commit()
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
        print "At least one parameter is missing!"
        print "See python %s -h" % sys.argv[0]
        sys.exit(1)
    main_5(opts.database, opts.chapter, opts.verbose)