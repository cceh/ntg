#!/usr/bin/python
# -*- encoding: utf-8 -*-
"""
7. zw-Lesarten der uebergeordneten Variante zuordnen, wenn ausschliesslich
verschiedene Lesarten derselben Variante infrage kommen (z.B. zw a/ao oder
b/bo_f). In diesen Faellen tritt die Buchstabenkennung der uebergeordneten
Variante in LABEZ an die Stelle von 'zw'.

Da die Stringmethode strip() nicht wie gewuenscht funktioniert, schreibe ich
mir eine eigene: mystrip.

Vgl. die Datei ArbeitsablaufCBGMApg1.pdf in der Mail
von Klaus am 25.01.2012
"""
__author__ = "volker.krueger@uni-muenster.de"


def mystrip(source, pattern):
    """
    Entfernen der in pattern genannten Zeichen aus der Zeichenkette 'source'.
    """
    result = source[0]
    for c in source[1:]:
        if c not in pattern:
            result += c
    return result


def matches(pattern, input):
    """
    Stimmt jedes einzelne Zeichen in 'input' mit dem
    Zeichen 'pattern' ueberein?
    """
    result = True
    for c in input:
        if c != pattern:
            return False
    return result


def main_7(database, chapter, verbose=False):
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
    # Zu loeschende Zeichen definieren
    pattern = "fo_1234567890/"
    # Alle 'zw'-Lesarten auflisten
    cmd = "select labezsuf, anfadr, endadr from `%s`.`%s` " % (database, table)
    cmd += "where labez like 'zw' "
    # Fälle wie "zw e/f" müssen aber stehen bleiben, z.B. Acta 4,2/20-34
    # alternativ könnte man die beiden folgenden Zeilen streichen,
    # und in der Schleife ein continue setzen, wenn ein RegEx zutrifft.
    cmd += "and labezsuf not like 'f%%' "
    cmd += "and labezsuf not like '%%/f%%' "
    cursor.execute(cmd)
    rows = cursor.fetchall()
    for row in rows:
        labezsuf = row[0]
        anfadr = row[1]
        endadr = row[2]
        s = mystrip(labezsuf, pattern)
        # Labez einheitlich immer gleich?
        b = matches(s[0], s)
        # Wenn wahr, dann diesen Datensatz updaten
        if b:
            cmd = "update `%s`.`%s` " % (database, table)
            cmd += "set labez = '%s' " % (s[0])
            cmd += "where labez like 'zw' "
            cmd += "and labezsuf like '%s' " % (labezsuf)
            cmd += "and anfadr = %s and endadr = %s " % (anfadr, endadr)
            printer(cmd)
            cursor.execute(cmd)
        dba.commit()
    cursor.close()
    dba.close()

if __name__ == '__main__':
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
    main_7(opts.database, opts.chapter, opts.verbose)