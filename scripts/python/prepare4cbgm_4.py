#!/usr/bin/python
# -*- encoding: utf-8 -*-
"""
4. Tabellen in ECM_Acts_Update (bzw. -Ph2) nach ECM_Acts_CBGM (bzw. -Ph2)
    kopieren. Die folgenden Arbeitsschritte (5 ff) beziehen sich auf
    Acts<n>att.

Vgl. die Datei ArbeitsablaufCBGMApg1.pdf in der Mail
von Klaus am 25.01.2012
"""
__author__ = "volker.krueger@uni-muenster.de"


def main_4(source, target, chapter, verbose=False):
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
    # Datenbank auswählen
    cmd = "use %s" % (source)
    cursor.execute(cmd)
    dba.commit()
    # Anfang des Tabellennamens generieren
    sChapter = str(chapter)
    if int(chapter) < 10:
        sChapter = "0" + sChapter
    tablename = "Acts" + sChapter
    # Tabellen erfragen
    cmd = "show tables like '%s%%'" % (tablename)
    cursor.execute(cmd)
    tables = cursor.fetchall()
    for t in tables:
        table = t[0]
        # Ausschneiden der Buch- und Kapitelbezeichnung
        name = tablename[0:6]
        # Neuen Namen zusammensetzen vgl. unten
        name += "att"
        if table.endswith("lac"):
            name += "Lac"
        if target.endswith("2"):
            name += "_2"
        if target.endswith("3"):
            name += "_3"
        # Evtl. vorhandene Tabelle loeschen
        cmd = "drop table if exists `%s`.`%s` " % (target, name)
        printer(cmd)
        cursor.execute(cmd)
        # Tabellen anlegen mit 'create table like ...'
        cmd = "create table `%s`.`%s` " % (target, name)
        cmd += "like `%s`.`%s` " % (source, table)
        printer(cmd)
        cursor.execute(cmd)
        # Befuellen mit 'insert into ... select * from ...'
        cmd = "insert into `%s`.`%s` " % (target, name)
        cmd += "select * from `%s`.`%s` " % (source, table)
        printer(cmd)
        cursor.execute(cmd)
    dba.commit()
    cursor.close()
    dba.close()


if __name__ == "__main__":
    from optparse import OptionParser
    parser = OptionParser()
    parser.add_option("-s", "--source", dest="source",
                      help="Giving source database")
    parser.add_option("-t", "--target", dest="target",
                      help="Giving target database")
    parser.add_option("-c", "--chapter", dest="chapter",
                      help="Giving one chapter")
    parser.add_option("-v", "--verbose", dest="verbose",
                      action="store_true", help="Verbose mode")
    (opts, args) = parser.parse_args()
    parser.destroy()
    if opts.source is None or opts.target is None or opts.chapter is None:
        import sys
        print "At least one parameter is missing!"
        print "Call %s -h" % sys.argv[0]
        sys.exit(1)
    main_4(opts.source, opts.target, opts.chapter, opts.verbose)