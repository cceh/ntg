#!/usr/bin/python
# -*- encoding: utf-8 -*-
"""
8. Handschriftenliste 'ActsMsList' anlegen. Die Handschrift bekommt in dem
    entsprechenden Kapitel eine 1, wenn sie dort Text enthaelt. Mit anderen
    Worten: Sie bekommt eine 0, wenn das ganze Kapitel eine Luecke ist. 
    Es wird hier auf die systematische Lueckenliste zurueckgegriffen.
    Ergaenzung vom 08.11.2012:
    Es kann sein, dass der erhaltene Text nur als zz bzw. zw gelistet ist. 
    Er kann dann fuer die CBGM nicht verwertet werden. Kapitel, die keine
    echte Variante enthalten, muessen ebenfalls eine 0 erhalten. 

Vgl. die Datei ArbeitsablaufCBGMApg1.pdf in der Mail
von Klaus am 25.01.2012
"""
import parser

__author__ = "volker.krueger@uni-muenster.de"


def checkChapter(cursor, attTable, hsnr):
	"""
	Enthaelt das Kapitel mindestens eine echte Variante?
	"""
	cmd  = "select count(distinct labez) from %s " % (attTable)
	cmd += "where labez not like 'z_' "
	cmd += "and hsnr = %d " % (hsnr)
	#print cmd
	cursor.execute(cmd)
	res = cursor.fetchone()
	count = int(res[0])
	if count > 0:
		return 1
	return 0


def createMsList(cursor, database, table):
    """
    (Neu) Anlegen der Handschriftentabelle.
    """
    # Alte Tabelle löschen, wenn vorhanden
    cmd  = "drop table if exists `%s`.`%s` " % (database, table)
    cursor.execute(cmd)
    # Tabelle neu anlegen
    cmd  = "create table `%s`.`%s` " % (database, table)
    cmd += "(id int auto_increment primary key, "
    cmd += "`CHECK` varchar(1) default '', "
    cmd += "WITN varchar(8) not null default '', "
    cmd += "MS int not null default -1, "
    cmd += "Apg01 int not null default -1, "
    cmd += "Apg02 int not null default -1, "
    cmd += "Apg03 int not null default -1, "
    cmd += "Apg04 int not null default -1, "
    cmd += "Apg05 int not null default -1, "
    cmd += "Apg06 int not null default -1, "
    cmd += "Apg07 int not null default -1, "
    cmd += "Apg08 int not null default -1, "
    cmd += "Apg09 int not null default -1, "
    cmd += "Apg10 int not null default -1, "
    cmd += "Apg11 int not null default -1, "
    cmd += "Apg12 int not null default -1, "
    cmd += "Apg13 int not null default -1, "
    cmd += "Apg14 int not null default -1, "
    cmd += "Apg15 int not null default -1, "
    cmd += "Apg16 int not null default -1, "
    cmd += "Apg17 int not null default -1, "
    cmd += "Apg18 int not null default -1, "
    cmd += "Apg19 int not null default -1, "
    cmd += "Apg20 int not null default -1, "
    cmd += "Apg21 int not null default -1, "
    cmd += "Apg22 int not null default -1, "
    cmd += "Apg23 int not null default -1, "
    cmd += "Apg24 int not null default -1, "
    cmd += "Apg25 int not null default -1, "
    cmd += "Apg26 int not null default -1, "
    cmd += "Apg27 int not null default -1, "
    cmd += "Apg28 int not null default -1, "
    # und eine Spalte als summarische Angabe: 
    cmd += "Apg int not null default -1) "
    cursor.execute(cmd)


def insertMss(cursor, database, table):
    # Handschriftennummern einlesen
    cmd  = "select hsnr, hs from `%s`.`MssActsECM` order by hsnr " % (database)
    cursor.execute(cmd)
    rows = cursor.fetchall()
    for row in rows:
        cmd  = "insert into `%s`.`%s` (ms, witn) value (%s, '%s') " % (database,
        							       table,
        							       row[0],
        							       row[1])
        cursor.execute(cmd)


def main_8(databaseAtt, tab, recreateTable=False, verbose=False):
    def printer(s):
        """
        Print information if needed.
        """
        if verbose:
            print s
    from NestleAland import NA
    import access
    import db_access3
    na = NA()
    dba = db_access3.DBA(access.get())
    cursor = dba.cursor()
    databaseList = "ECM_Acts_Mss"
    table = "ActsMsList_2" 
    chapter = tab[4:6]
    attTable = "`ECM_Acts_CBGMPh3`.`Acts"+chapter+"att_3`"
#    # Anlegen der Tabelle
#    if recreateTable:
#        createMsList(cursor, databaseList, table)
#        # Einlesen der Handschriftennummern - mehr noch nicht
#        insertMss(cursor, databaseList, table)
    # Welche Handschriftennummern gibt es in der Tabelle?
    cmd  = "select ms from `%s`.`%s` order by `ms` " % (databaseList, table)
    cursor.execute(cmd)
    mss = cursor.fetchall()
    for ms in mss:
        # Update der einzelnen Zellen pro Handschrift und Kapitel
        cmd = "select versanf, versend, wortanf, wortend "
        cmd += "from `%s`.`%s` " % (databaseAtt, tab)
        cmd += "where hsnr = %d and kapanf = %d " % (ms[0], int(chapter))
        #print cmd
        # tab ist hier die Lueckenliste!
        counter = cursor.execute(cmd)
        #print "counter ist ",counter
        result = cursor.fetchone()
        if counter == 1:
            try:
                #print "ms ist ", ms
                #print result
                versanf = result[0]
                versend = result[1]
                wortanf = result[2]
                wortend = result[3]
                maxvers = na.getMaxVerse(5, int(chapter))
                maxword = na.getMaxWord(5, int(chapter), int(maxvers))
                if versanf == 1 and wortanf == 2 and versend == maxvers and wortend >= maxword: # Lacune umgreift ganzes Kapitel
                    value = 0
                else: # es ist (mindestens teilweise) Text erhalten
                    value = checkChapter(cursor, attTable, ms)
            except TypeError:
                value = 1
        else:
            #value = 1
            value = checkChapter(cursor, attTable, ms)
        cmd  = "update `%s`.`%s` " % (databaseList, table)
        cmd += "set Apg%s = %d where ms = %s " % (chapter, value, ms[0])
        printer(cmd)
        cursor.execute(cmd)
        #print cmd
    # Update der summarischen Angabe 'Apg'
    for ms in mss:
        cmd  = "select Apg01, Apg02, Apg03, Apg04, Apg05, Apg06, Apg07, Apg08, "
        cmd += "Apg09, Apg10, Apg11, Apg12, Apg13, Apg14, Apg15, Apg16, Apg17, Apg18, "
        cmd += "Apg19, Apg20, Apg21, Apg22, Apg23, Apg24, Apg25, Apg26, Apg27, Apg28 "
        cmd += "from `%s`.`%s` " % (databaseList, table)
        cmd += "where ms = %s " % (ms[0])
        cursor.execute(cmd)
        result = cursor.fetchone()
        sum = 0
        for n in range(28):
            sum += int(result[n])
        # Summe == 28 d.h. alle Kapitel haben Text
        if sum == 28:
            cmd  = "update `%s`.`%s` " % (databaseList, table)
            cmd += "set Apg = 1 where ms = %s " % (ms[0])
        else:
            cmd  = "update `%s`.`%s` " % (databaseList, table)
            cmd += "set Apg = 0 where ms = %s " % (ms[0])
        cursor.execute(cmd)
    cursor.close()
    dba.close()

if __name__ == "__main__":
    import sys
    from optparse import OptionParser
    parser = OptionParser()
    parser.add_option("-r", "--recreate", dest="recreate", action="store_true", help="Recreate ECM_Acts_Mss.ActsMsList_2")
    parser.add_option("-d", "--database", dest="database", help="Database containing systematic lacunae list")
    parser.add_option("-t", "--table", dest="table", help="Giving name systematic lacunae list")
    parser.add_option("-v", "--verbose", dest="verbose", action="store_true", help="Verbose mode")
    (opts, args) = parser.parse_args()
    parser.destroy()
    if opts.database is None:
        print "Error: Database name is missing!"
        print "See python %s -h" % sys.argv[0]
        sys.exit(1)
    if opts.table is None:
        print "Error: Table name is missing!"
        print "See python %s -h" % sys.argv[0]
        sys.exit(1)
    if opts.recreate is None:
        main_8(opts.database, opts.table, opts.verbose)
    else:
        main_8(opts.database, opts.table, opts.recreate, opts.verbose)
