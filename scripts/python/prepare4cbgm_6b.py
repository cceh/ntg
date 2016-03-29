#!/usr/bin/python
# -*- encoding: utf-8 -*-
"""
4b. Die Eintrag 'videtur', gekennzeichnet durch ein 'V'
hinter der Handschriftennummer, spielt fuer die CBGM keine Rolle.
Ein eventuell vorhandenes 'V' muss getilgt werden.
Gleiches gilt fuer die Eintraege '*' und 'C*'.

"""
__author__ = "volker.krueger@uni-muenster.de"


def killVStarC(s):
    """
    killVStarC() entfernt ein 'V', '*', 'T1' und 'C*' aus einer Zeichenkette.

    The method deletes a 'V', 'C', 'T' or a star from a string.
    """
    pattern = ("V", "C", "*")
    for char in pattern:
        pos = s.find(char)
        if pos > -1:
            s = s[:pos] + s[pos+1:]
    pos = s.find("T1")
    if pos > -1:
        s = s[:pos]
    return s


def main_6b(database, chapter, verbose=False):
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
    # Alle in Frage kommenden Stellen auflisten
    cmd = "select anfadr, endadr, HS from `%s`.`%s` " % (database, table)
    cmd += "where HS like '%%V%%' or HS like '%%*%%' or HS like '%%C%%' "
    cursor.execute(cmd)
    rows = cursor.fetchall()
    for r in rows:
        anf = r[0]
        end = r[1]
        wit = r[2]
        # 'V', 'C' oder '*' aus der Handschriftenbezeichnung entfernen
        wit_new = killVStarC(wit)
        # Update der Datenbanktabelle
        cmd = "update `%s`.`%s` " % (database, table)
        cmd += "set HS = '%s' " % (wit_new)
        cmd += "where anfadr = %d and endadr = %d " % (anf, end)
        cmd += "and HS = '%s' " % (wit)
        printer(cmd)  # Kontrollausgabe
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
    main_6b(opts.database, opts.chapter, opts.verbose)
