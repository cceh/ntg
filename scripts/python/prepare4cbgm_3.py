#!/usr/bin/python
# -*- encoding: utf-8 -*-
"""
3. Tabellenstruktur bereinigen: Felder SUFFIX1, ADR,
   ZUSATZ, LesartenKey loeschen

   3.1. Anzeige aller Tabellen in der Datenbank
   3.2. Tabellenfelder loeschen mit 'alter table ..., drop ...'
Vgl. die Datei ArbeitsablaufCBGMApg1.pdf in der Mail
von Klaus am 25.01.2012
"""
__author__ = "volker.krueger@uni-muenster.de"


def main_3(db, chapter, verbose=False):
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
    # Tabellennamen erschließen
    sChapter = str(chapter)
    if int(chapter) < 10:
        sChapter = "0" + sChapter
    cmd = "show tables from `%s` like 'Acts%s%%'; " % (db, sChapter)
    cursor.execute(cmd)
    tables = cursor.fetchall()
    for table in tables:
        # Tabellenfelder loeschen mit 'alter table ..., drop ...'
        cmd = "alter table `%s`.`%s` " % (db, table[0])
        cmd += "drop SUFFIX1, drop ADR, drop ZUSATZ, drop LesartenKey "
        printer(cmd)
        try:
            cursor.execute(cmd)
        except:
            pass
    dba.commit()
    cursor.close()
    dba.close()

if __name__ == "__main__":
    from optparse import OptionParser
    parser = OptionParser()
    parser.add_option("-d", "--database", dest="database")
    parser.add_option("-c", "--chapter", dest="chapter")
    parser.add_option("-v", "--verbose", dest="verbose", action="store_true", help="Verbose mode")
    (opts, args) = parser.parse_args()
    parser.destroy()
    if opts.database is None or opts.chapter is None:
        import sys
        print "Error: At least one parameter necessary is missing!"
        print "See python %s -h" % sys.argv[0]
        sys.exit(1)
    main_3(opts.database, opts.chapter, opts.verbose)