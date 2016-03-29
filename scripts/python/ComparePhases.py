#!/usr/bin/python
"""
File name: ComparePhases.py
Feststellung der Unterschiede in den Apparaten von Phase 1 und 2.
"""
__author__ = "volker.krueger@uni-muenster.de"

def main(mode="remote"):
	# static variables
	PHASE1 = "`ECM_ActsPh2`.`Acts15GVZ`"
	PHASE2 = "`ECM_ActsPh4`.`Acts15GVZ`"
	# configure database connection
	import db_access3, Address
	from NestleAland import getBookName
	conn = db_access3.DBA(mode)
	cursor = conn.cursor()
	# print temporary table
	def printTable():
		cmd  = "select anfadr, endadr, labez, labezsuf, reading1 "
		cmd += "from `ECM_Acts`.`TempTable` order by anfadr asc, endadr desc, labez asc; "
		cursor.execute(cmd)
		rows = cursor.fetchall()
		for r in rows:
			anf = r[0]
			end = r[1]
			lab = r[2]
			las = r[3]
			rd1 = r[4]
			b, bc, bv, bw, ec, ev, ew = Address.decodeAdr(anf, end)
			sb = getBookName(b)
			s = db_access3.formatAdr(sb, bc, bv, bw, ec, ev, ew)
			s1 = s2 = ""
			if rd1 != None:
				s1 = "\n\t>" + rd1.decode('utf8') + "< "
			print "%s%s%s%s " % (s, lab, las, s1)
	# file to generate sql statements for patristic citation database
	fd = open("deleatur.sql", "w")
	# create temporary table
	cmd  = "drop table if exists `ECM_Acts`.`TempTable`; "
	cursor.execute(cmd)
	cmd  = "CREATE TABLE `ECM_Acts`.`TempTable` ("
	cmd += "`anfadr` int(11) NOT NULL, "
	cmd += "`endadr` int(11) NOT NULL, "
	cmd += "`labez` varchar(8) NOT NULL, "
	cmd += "`labezsuf` varchar(16) default '', "
	cmd += "`reading1` varchar(1024) character set utf8 collate utf8_bin default NULL"
	cmd += ") ENGINE=MyISAM DEFAULT CHARSET=latin1" 
	cursor.execute(cmd)

	print "old:"
	cmd  = "select distinct anfadr, endadr, labez, labezsuf from %s order by anfadr, endadr desc; " % (PHASE1)
	cursor.execute(cmd)
	rows = cursor.fetchall()
	for row in rows:
		anf = row[0]
		end = row[1]
		lab = row[2]
		las = row[3]
		cmd  = "select count(*) from %s " % (PHASE2)
		cmd += "where anfadr = %s and endadr = %s " % (anf, end)
		cmd += "and labez = '%s' and labezsuf = '%s' " % (lab, las)
		cursor.execute(cmd)
		res = cursor.fetchone()
		if res[0] == 0:
			cmd  = "insert into `ECM_Acts`.`TempTable` "
			cmd += "(anfadr, endadr, labez, labezsuf) values "
			cmd += "(%d, %d, '%s', '%s'); " % (anf, end, lab, las)
			cursor.execute(cmd)
			# generate sql file
			s  = "delete from `Apparat_Zitate`.`Cit2Reading` "
			s += "where anfadr = %d and endadr = %d " % (anf, end)
			s += "and labez = '%s' and labezsuf = '%s'; \n" % (lab, las)
			fd.write(s)
	cmd  = "select distinct a.anfadr, a.endadr, a.labez, a.labezsuf, a.lesart from %s a, %s b " % (PHASE1, PHASE2)
	cmd += "where a.anfadr = b.anfadr and a.endadr = b.endadr "
	cmd += "and a.labez = b.labez and a.labezsuf = b.labezsuf "
	cmd += "and a.lesart <> b.lesart "
	cmd += "order by b.anfadr, b.endadr desc, b.labez; "
	cursor.execute(cmd)
	rows = cursor.fetchall()
	for row in rows:
		anf = row[0]
		end = row[1]
		lab = row[2]
		las = row[3]
		try:
			rdg = row[4].decode('utf8')
		except:
			rdg = ""
		# check if already entered in the table
#		cmd  = "select count(*) from `ECM_Acts`.`TempTable` "
#		cmd += "where anfadr = %s and endadr = %s " % (anf, end)
#		cmd += "and labez = '%s' and labezsuf = '%s'; " % (lab, las)
#		count = cursor.execute(cmd)
#		if count == 0:
		cmd  = "insert into `ECM_Acts`.`TempTable` "
		cmd += "(anfadr, endadr, labez, labezsuf, reading1) values "
		cmd += "(%d, %d, '%s', '%s', '%s'); " % (anf, end, lab, las, rdg)
		cursor.execute(cmd)
	printTable()
	# truncate temp table
	cmd  = "truncate `ECM_Acts`.`TempTable`; "
	cursor.execute(cmd)
	
	print ""
	print "new:"
	cmd  = "select distinct anfadr, endadr, labez, labezsuf from %s order by anfadr, endadr desc; " % (PHASE2)
	cursor.execute(cmd)
	rows = cursor.fetchall()
	for row in rows:
		anf = row[0]
		end = row[1]
		lab = row[2]
		las = row[3]
		cmd  = "select count(*) from %s " % (PHASE1)
		cmd += "where anfadr = %s and endadr = %s " % (anf, end)
		cmd += "and labez = '%s' and labezsuf = '%s' " % (lab, las)
		cursor.execute(cmd)
		res = cursor.fetchone()
		if res[0] == 0:
			cmd  = "insert into `ECM_Acts`.`TempTable` "
			cmd += "(anfadr, endadr, labez, labezsuf) values "
			cmd += "(%d, %d, '%s', '%s'); " % (anf, end, lab, las)
			cursor.execute(cmd)

	cmd  = "select distinct b.anfadr, b.endadr, b.labez, b.labezsuf, b.lesart from %s a, %s b " % (PHASE1, PHASE2)
	cmd += "where a.anfadr = b.anfadr and a.endadr = b.endadr "
	cmd += "and a.labez = b.labez and a.labezsuf = b.labezsuf "
	cmd += "and a.lesart <> b.lesart "
	cmd += "order by b.anfadr, b.endadr desc, b.labez; "
	cursor.execute(cmd)
	rows = cursor.fetchall()
	for row in rows:
		anf = row[0]
		end = row[1]
		lab = row[2]
		las = row[3]
		try:
			rdg = row[4].decode('utf8')
		except:
			rdg = ""
		# check if already entered in the table
#		cmd  = "select count(*) from `ECM_Acts`.`TempTable` "
#		cmd += "where anfadr = %s and endadr = %s " % (anf, end)
#		cmd += "and labez = '%s' and labezsuf = '%s'; " % (lab, las)
#		count = cursor.execute(cmd)
#		if count == 0:
		cmd  = "insert into `ECM_Acts`.`TempTable` "
		cmd += "(anfadr, endadr, labez, labezsuf, reading1) values "
		cmd += "(%d, %d, '%s', '%s', '%s'); " % (anf, end, lab, las, rdg)
		cursor.execute(cmd)
	# read temporary table
	printTable()
	# drop temporary table
	cmd  = "drop table `ECM_Acts`.`TempTable`; "
	cursor.execute(cmd)
	# closing database
	cursor.close()
	conn.close()
	# close file handle
	fd.close()

if __name__ == '__main__':
	main()
