#! /usr/bin/python
#-*- encoding: utf-8 -*-
'''
Module imported by printer3.py and printer4.py etc.
'''
__author__ = "volker.krueger@uni-muenster.de"

import MySQLdb

#Configure database access here
local_dict = {
    "host"   : "localhost",
    "user"   : "root",
    "passwd" : "xxx",
    "db"     : "apparat",
    "charset": "utf8" }

remote_dict = {
    "host"   : "your_hostname",
    "user"   : "your_username",
    "passwd" : "your_password",
    "db"     : "Apparat",
    "charset": "utf8" }


class DBA(object):
    def __init__(self, s):
        self.__d = {}
        if s == "local":
            self.__d = local_dict
        elif s == "remote":
            self.__d = remote_dict
        else:
            self.__d = None
        if self.__d != None:
            self.connection = MySQLdb.connect(host=self.__d.get("host"), \
                                              user=self.__d.get("user"), \
                                              passwd=self.__d.get("passwd"), \
                                              db=self.__d.get("db"), \
                                              charset=self.__d.get("charset"))
            self.owncursor = self.connection.cursor()
    def __del__(self):
        #self.close()
        pass
    def getHost(self):
        return self.__d.get("host")
    def getUser(self):
        return self.__d.get("user")
    def getPasswd(self):
        return self.__d.get("passwd")
    def getDb(self):
        return self.__d.get("db")
    def getCharset(self):
        return self.__d.get("charset")
    def autocommit(self, value):
        self.connection.autocommit(value)
    def commit(self):
        self.connection.commit()
    def rollback(self):
        self.connection.rollback()
    def cursor(self):
        return self.connection.cursor()
    def close(self):
        self.connection.close()
    def getMssAvailable(self, book):
        '''
        Giving all manuscripts collated for the book identified by the parameter.
        '''
        cmd  = "select hsnr from `Apparat`.`mss_available` "
        cmd += "where book = %d " % (book)
        cmd += "and hsnr < 500000 " # Fehlverse ausschliessen
        cmd += "order by hsnr "
        self.owncursor.execute(cmd)
        return self.owncursor.fetchall()
    def getPassages(self, database, table, startverse = 0, endverse = 0, firstword = 0, lastword = 0):
        """
        Getting all passages of a witness table. The program should work
        independently from a LesartenOnly table.
        """
        cmd  = "select distinct anfadr, endadr, buch, kapanf, versanf, wortanf, "
        cmd += "kapend, versend, wortend from `%s`.`%s` where 1 " % (database, table)
        cond = ""
        if int(startverse) > 0 and int(endverse) > 0:
            cond  = "and versanf >= %s and versend <= %s " % (startverse, endverse)
            if int(firstword) > 0 and int(lastword) > 0:
                cond  = "and ((versanf = %s and wortanf >= %s) or versanf > %s) " % (startverse, firstword, startverse)
                cond += "and ((versend = %s and wortend <= %s) or versend < %s) " % (endverse, lastword, endverse)
        cmd += cond + "order by anfadr asc, endadr desc "
        count = self.owncursor.execute(cmd)
        return self.owncursor.fetchall(), count
    def getReadings(self, database, table, anfadr, endadr):
        """
        Getting all the readings which belong to an address described by the
        result set of 'row_passages'.
        """
        cmd  = "select distinct anfadr, endadr, labez, labezsuf, "
        cmd += "buch, kapanf, versanf, wortanf, kapend, versend, wortend, lesart "
        cmd += "from `%s`.`%s` " % (database, table)
        cmd += "where anfadr = %d and endadr = %d " % (anfadr, endadr)
        cmd += "order by labez, labezsuf "
        #print cmd
        count = self.owncursor.execute(cmd)
        return self.owncursor.fetchall(), count
    def getReadings2(self, database, table, anfadr, endadr):
        """
        Getting all readings which belong to one passage. Fehlerlesarten
        are included - orthographica too.
        """
        cmd  = "select distinct anfadr, endadr, labez, '', "
        cmd += "buch, kapanf, versanf, wortanf, kapend, versend, wortend, lesart "
        cmd += "from `%s`.`%s` " % (database, table)
        cmd += "where anfadr = %d and endadr = %d " % (anfadr, endadr)
        cmd += "order by labez, labezsuf "
        count = self.owncursor.execute(cmd)
        return self.owncursor.fetchall(), count
    def getWitnesses(self, database, table, anfadr, endadr, labez, labezsuf):
        """
        Getting all witnesses of a reading described by the result set of
        'row_readings'.
        """
        cmd  = "select hs, suffix2, hsnr, lemma, lesart, fehler from `%s`.`%s` " % (database, table)
        cmd += "where anfadr = %s and endadr = %s " % (anfadr, endadr)
        cmd += "and labez = '%s' and labezsuf = '%s' " % (labez, labezsuf)
        cmd += "order by hsnr, labezsuf "
        #  print cmd
        count = self.owncursor.execute(cmd)
        return self.owncursor.fetchall(), count
    def getVersions(self, database, table, anfadr, endadr, labez, labezsuf):
        cmd  = "select hss, suffix2, hsnr, vers_lesart, fehler from `%s`.`%s` " % (database, table)
        cmd += "where anfadr = %s and endadr = %s " % (anfadr, endadr)
        cmd += "and labez = '%s' and labezsuf = '%s' " % (labez.encode('utf-8'), labezsuf.encode('utf-8'))
        cmd += "order by hsnr, labezsuf "
        #  print cmd
        count = self.owncursor.execute(cmd)
        return self.owncursor.fetchall(), count
    def getAllWitnesses(self, database, table, anfadr, endadr):
        """
        Returns all witnesses of a passage.
        """
        cmd  = "select hs, hsnr from `%s`.`%s` " % (database, table)
        cmd += "where anfadr = %d and endadr = %d " % (anfadr, endadr)
        cmd += "order by hsnr "
        count = self.owncursor.execute(cmd)
        return self.owncursor.fetchall(), count
    def countWitnessesDifferentFromA(self, database, table, anfadr, endadr):
        '''
        How many greek witnesses differ from the Ausgangstext?
        Orthographica are not included.
        '''
        cmd  = "select count(hsnr) from `%s`.`%s` " % (database, table)
        cmd += "where anfadr = %d and endadr = %d " % (anfadr, endadr)
        cmd += "and (labez <> 'a' "
        cmd += "or labez = 'a' and (labezsuf <> '' or labezsuf is not null)) "
        cmd += "and hsnr < 500000 "
        void = self.owncursor.execute(cmd)
        res  = self.owncursor.fetchone()
        return res[0]
    def getLacunaeAndDubia(self, database, table, anfadr, endadr, lacunae = None):
        '''
        Returns witnesses having a lacuna at the passage or having labez 'zz'.
        '''
        if lacunae == None:
            lacunae = table + "lac"
        cmd  = "(select hs, hsnr from %s.%s " % (database, lacunae) # here: table of lacunae
        cmd += "where anfadr <= %d and endadr >= %d " % (int(endadr), int(anfadr))
        cmd += "order by hsnr, suffix2) union "
        cmd += "(select hs, hsnr from %s.%s " % (database, table) # here: table of witnesses
        cmd += "where anfadr = %d and endadr = %d " % (anfadr, endadr)
        cmd += "and labez = 'zz' "
        cmd += "order by hsnr) "
        count = self.owncursor.execute(cmd)
        # sort result sets into an ascending order
        res  = [] # tupel to return
        rel  = {} # dictionary hsnr: hs
        hsnr = [] # list containing hsnr
        rows = self.owncursor.fetchall()
        for row in rows:
            hs = row[0]
            nr = row[1]
            if nr not in hsnr:
                hsnr.append(nr)
                rel[nr] = (hs, nr, )
        hsnr.sort()
        for nr in hsnr:
            res.append(rel[nr])
        return res, count


def formatAdr(b, bc, bv, bw, ec, ev, ew):
    """
    Write the seven parameters in a nicely formatted way.
    """
    s = ""
    if bc == ec and bv == ev and bw == ew:
        s = "%s%s:%s/%s" % (b, bc, bv, bw)
    else:
        if bc == ec and bv == ev:
            s = "%s%s:%s/%s-%s" % (b, bc, bv, bw, ew)
        else:
            if bc == ec:
                s = "%s%s:%s/%s-%s/%s" % (b, bc, bv, bw, ev, ew)
            else:
                s = "%s%s:%s/%s-%s:%s/%s" % (b, bc, bv, bw, ec, ev, ew)
    return s
