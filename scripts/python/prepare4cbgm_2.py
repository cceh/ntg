#!/usr/bin/python
# -*- encoding: utf-8 -*-
"""
2. Korrekturen in den Acts-Tabellen: L-Notierungen nur im Feld LEKT,
*- u. C-Notierungen nur im Feld KORR.
Gelegentlich steht an Stellen, an denen mehrere Lektionen desselben
Lektionars zu verzeichnen sind, in KORR ein ueberfluessiges 'L' ohne Nummer.
Es kommt auch vor, dass L1 und L2 in KORR stehen oder C-Notierungen in LEKT.

Vgl. die Datei ArbeitsablaufCBGMApg1.pdf in der Mail
von Klaus am 25.01.2012
"""
__author__ = "volker.krueger@uni-muenster.de"


def main_2(db, chapter, verbose=False):
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
        cmd = "select korr, lekt, id from %s.%s " % (db, table[0])
        cursor.execute(cmd)
        rows = cursor.fetchall()
        for row in rows:
            korr = row[0]
            lekt = row[1]
            id = row[2]
            if korr is not None:
                if korr.find("L") >= 0:
                    cmd = "update %s.%s " % (db, table[0])
                    cmd += "set lekt = '%s' where id = %d " % (korr, id)
                    printer(cmd)
                    cursor.execute(cmd)
                    cmd = "update %s.%s " % (db, table[0])
                    cmd += "set korr = '' where id = %d " % (id)
                    printer(cmd)
                    cursor.execute(cmd)
            if lekt is not None:
                pos = lekt.find("C")
                if pos >= 0:
                    pass
                else:
                    pos = lekt.find("*")
                if pos >= 0:
                    cmd = "update %s.%s " % (db, table[0])
                    cmd += "set korr = '%s' where id = %d " % (lekt, id)
                    printer(cmd)
                    cursor.execute(cmd)
                    cmd = "update %s.%s " % (db, table[0])
                    cmd += "set lekt = '' where id = %d " % (id)
                    printer(cmd)
                    cursor.execute(cmd)
            dba.commit()
    cursor.close()
    dba.close()

if __name__ == '__main__':
    import sys
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
        print "Error: At least one parameter necessary is missing!"
        print "See python %s -h" % sys.argv[0]
        sys.exit(1)
    main_2(opts.database, opts.chapter, opts.verbose)