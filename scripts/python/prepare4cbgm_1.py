#!/usr/bin/python
#-*- encoding: utf-8 -*-
"""
1. Tabelle fuer die Korrektur mit neuem Datum von
    `ECM_Acts` nach `ECM_Acts_Update` kopieren.
    (Z.B. Acts01C20111223 >> Acts01C20120125)
    1.0. Loeschen der bereits vorhandenen Tabellen in der Zieldatenbank
    1.1. Anzeige aller Tabellen in der Quelldatenbank
    1.2. Generieren eines Datumsstempels
    1.3. Ausschneiden der Buch-, Kapitel- und Versionsbezeichnung
    1.4. Tabellen anlegen mit 'create table like ...'
    1.5. Befuellen mit 'insert into ... select * from ...'
Vgl. die Datei ArbeitsablaufCBGMApg1.pdf in der Mail
von Klaus am 25.01.2012
"""
__author__="volker.krueger@uni-muenster.de"

def main_1(sourceDB, targetDB, chapter=0, verbose=False):
    def printer(s):
        """
        Print information if needed.
        """
        if verbose:
            print s
    import access
    import db_access3, datetime
    dba = db_access3.DBA(access.get())
    cursor = dba.cursor()
#    sourceDB = "Apparat_Annette"
#    targetDB = "ECM_Acts_UpdatePh2"
    # 1.0. Loeschen der bereits vorhandenen Tabellen in der Zieldatenbank
    cmd  = "drop database `%s` " % (targetDB)
    cursor.execute(cmd)
    cmd  = "create database `%s` " % (targetDB)
    cursor.execute(cmd)
    if chapter == 0:
        # 1.1. Anzeige aller Tabellen in der Quelldatenbank
        cmd = "show tables from `%s` like 'Acts%%'; " % (sourceDB)
    else:
        # 1.1. Anzeige der (beiden) Tabellen eines Kapitels
        if chapter < 10:
            sChapter = "0" + str(chapter)
        else:
            sChapter = str(chapter)
        cmd = "show tables from `%s` like 'Acts%s%%'; " % (sourceDB, sChapter)
    printer(cmd)
    cursor.execute(cmd)
    tables = cursor.fetchall()
    for table in tables:
        # 1.2. Generieren eines Datumsstempels
        d = "%s" % datetime.date.today()
        datum = d[:4] + d[5:7] + d[8:]
        # 1.3. Ausschneiden der Buch-, Kapitel- und Versionsbezeichnung
        name = table[0][:9]
        # Neuen Namen zusammensetzen
        name += datum
        # Bei Bedarf das Suffix 'lac' anfuegen
        if table[0].endswith("lac"):
            name += "lac"
        # 1.4. Tabellen anlegen mit 'create table like ...'
        cmd = "create table `%s`.`%s` " % (targetDB, name)
        cmd += "like `%s`.`%s` " % (sourceDB, table[0])
        printer(cmd)
        cursor.execute(cmd)
        # 1.5. Befuellen mit 'insert into ... select * from ...'
        cmd  = "insert into `%s`.`%s` " % (targetDB, name)
        cmd += "select * from `%s`.`%s` " % (sourceDB, table[0])
        printer(cmd)
        cursor.execute(cmd)
        dba.commit()
    cursor.close()
    dba.close()

if __name__ == "__main__":
    import sys
    from optparse import OptionParser
    usage = "Usage: %s [options]" % sys.argv[0]
    usage += "\nCopy apparatus data into a new database."
    usage += "\nTAKE CARE:"
    usage += "\nThe script copies all chapters of a database!"
    parser = OptionParser(usage=usage)
    parser.add_option("-s", "--source", dest="source", help="Giving source database")
    parser.add_option("-t", "--target", dest="target", help="Giving target database")
    parser.add_option("-c", "--chapter", dest="chapter", help="Optionally giving one chapter")
    parser.add_option("-v", "--verbose", dest="verbose", action="store_true", help="Verbose mode")
    (opts, args) = parser.parse_args()
    parser.destroy()
    source = target = ""
    chapter = 0
    try:
        if len(opts.source) > 0:
            source = opts.source
        if len(opts.target) > 0:
            target = opts.target
        if len(opts.chapter) > 0:
            chapter = int(opts.chapter)
    except:
        pass
    if source == "" or target == "":
        print "At least one parameter is missing."
        print "python %s -h" % (sys.argv[0])
        sys.exit(1)
    main_1(source, target, chapter, opts.verbose)