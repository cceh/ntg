#!/usr/bin/python
#-*- encoding: utf-8 -*-
"""
Versionelle Einträge (Handschriftennummer > 500000) löschen.
"""
__author__="volker.krueger@uni-muenster.de"

def main_1b(database, chapter=0, verbose=False):
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
    if chapter == 0:
        # 1.1. Anzeige aller Tabellen in der Quelldatenbank
        cmd = "show tables from `%s` like 'Acts%%'; " % (database)
    else:
        # 1.1. Anzeige der (beiden) Tabellen eines Kapitels
        if int(chapter) < 10:
            sChapter = "0" + str(chapter)
        else:
            sChapter = str(chapter)
        cmd = "show tables from `%s` like 'Acts%s%%'; " % (database, sChapter)
    printer(cmd)
    cursor.execute(cmd)
    tables = cursor.fetchall()
    for table in tables:
        # Lückenliste überspringen
        if table[0].endswith("lac"):
            continue
        # 1.2. Datensätze mit Handschriftennummer > 500000 löschen
        cmd = "delete from `%s`.`%s` " % (database, table[0])
        cmd += "where `hsnr` >= 500000 "
        printer(cmd)
        cursor.execute(cmd)
        dba.commit()
    cursor.close()
    dba.close()

if __name__ == "__main__":
    from optparse import OptionParser
    parser = OptionParser()
    parser.add_option("-d", "--database", dest="database", help="Giving database")
    parser.add_option("-c", "--chapter", dest="chapter", help="Optionally giving one chapter")
    parser.add_option("-v", "--verbose", dest="verbose", action="store_true", help="Verbose mode")
    (opts, args) = parser.parse_args()
    parser.destroy()
    if opts.database is None or opts.chapter is None:
        import sys
        print "At least one parameter is missing."
        print "python %s -h" % (sys.argv[0])
        sys.exit(1)
    main_1b(opts.database, opts.chapter, opts.verbose)
