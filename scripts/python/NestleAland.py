#!/usr/bin/python
# -*- encoding: utf-8 -*-
'''
Tools
'''
import Fehlverse
import db_access3
import Address

NT = { 1: ("Mt", "Matthew"),
	   2: ("Mc", "Mark"),
	   3: ("L", "Luke"),
	   4: ("J", "John"),
	   5: ("Act", "Acts"),
	   6: ("R", "Romans"),
	   7: ("1K", "1Corinthians"),
	   8: ("2K", "2Corinthians"),
	   9: ("G", "Galatians"),
	  10: ("E", "Ephesians"),
	  11: ("Ph", "Philippians"),
	  12: ("Kol", "Colossians"),
	  13: ("1Th", "1Thessalonians"),
	  14: ("2Th", "2Thessalonians"),
	  15: ("1T", "1Timothy"),
	  16: ("2T", "2Timothy"),
	  17: ("Tt", "Titus"),
	  18: ("Phm", "Philemon"),
	  19: ("H", "Hebrews"),
	  20: ("Jc", "James"),
	  21: ("1P", "1Peter"),
	  22: ("2P", "2Peter"),
	  23: ("1J", "1John"),
	  24: ("2J", "2John"),
	  25: ("3J", "3John"),
	  26: ("Jd", "Jude"),
	  27: ("Ap", "Revelation")
	 }

def getBookName(number):
    try:
        return NT[number][0]
    except KeyError:
        return ""
def getLongName(number):
    try:
        return NT[number][1]
    except KeyError:
        return ""

def getBookNumber(name):
    '''
    Returning the ordering number of the given book
    according to NA27.
    '''
    for n in range(1, 28):
        if name == NT[n][0] or name == NT[n][1]:
            return n
    return 0

def getMaxWord(dbcursor, book, chapter, verse):
    """
    Return the maximal word number of a verse.
    The method is used to correct errors of Collate.
    """
    try:
        cmd  = "select max(word) from Apparat.Nestle "
        cmd += "where book = %d " % book
        cmd += "and chapter = %d " % chapter
        cmd += "and verse = %d " % verse
        dbcursor.execute(cmd)
        row = dbcursor.fetchone()
        return row[0]
    except:
        print "Error in NestleAland.getMaxWord()"

class NA:
    def __init__(self, _edition=28):
        '''
        Konstruktor
        Die Datenbank enthält den Nestletext der Auflagen 28 und
        der gerade entstehenden 29. Auflage (= ECM Acta). Andere
        Auflagen können nicht abgefragt werden.
        '''
        #import MySQLdb
        self.fehlverse = Fehlverse.Fehlvers()
        dba = db_access3.DBA("remote")
        self.cursor = dba.cursor()
        self.edition = _edition
        if self.edition < 28 or self.edition > 29:
            print "Selected edition is not available!"
            print "Using edition 28 instead."
            self.edition = 28

    def __del__(self):
        '''
        Destruktor
        '''
        self.cursor.close()

    def getMaxChapter(self, book):
        """
        FIXME: Datenbasis R + 1K checken!
        """
        cmd  = "select max(chapter) from Apparat.Nestle "
        cmd+= "where book = %d " % (book)
        self.cursor.execute(cmd)
        row = self.cursor.fetchone()
        if row == None:
            return 0
        return row[0]

    def getMaxVerse(self, book, chapter):
        cmd  = "select max(verse) from Apparat.Nestle "
        cmd += "where book = %d and chapter = %d " % (book, chapter)
        self.cursor.execute(cmd)
        row = self.cursor.fetchone()
        if row == None:
            return 0 # Fehlverse
        return row[0]

    def getMaxWord(self, book, chapter, verse):
        cmd  = "select max(word) from Apparat.Nestle "
        cmd += "where book = %d and chapter = %d and verse = %d " % (book, chapter, verse)
        self.cursor.execute(cmd)
        row = self.cursor.fetchone()
        if row == None:
            return 0
        return row[0]

    def getNestleText(self, book, bchap, bvers, bword, echap, evers, eword, additamenta=False):
        """
        If the address represents an additamentum and the parameter additamenta is false,
        the text will be skipped. It is printed only if this parameter is set to true.
        """
        result = ""
        fehlvers_active = False
        fehlvers_started = False
        if not additamenta and bword % 2 == 1 and eword % 2 == 1:
            return result
        chapter  = bchap
        verse    = bvers
        word     = bword
        maxverse = self.getMaxVerse(book, chapter)
        maxword  = self.getMaxWord(book, chapter, verse)
        if maxword == 0:
            return result
        if eword == maxword + 1: # Endlosschleife verhindern
            maxword += 1
        while True:
            address = Address.encodeSingleAdr(book, chapter, verse, word) # ->Address.py
            fehlvers_active = self.fehlverse.isFehlvers(address)
            cmd  = "select content from Apparat.Nestle where book = %d " % (book)
            cmd += "and chapter = %d and verse = %d and word = %d " % (chapter, verse, word)
            self.cursor.execute(cmd)
            row = self.cursor.fetchone()
            if row == None:
                pass 
            else:
                # Anfangsklammern setzen
                if fehlvers_active and not fehlvers_started:
                    result += "[["
                    fehlvers_started = True
                # Schlussklammern setzen
                if not fehlvers_active and fehlvers_started:
                    result += "]]"
                    fehlvers_started = False
                # Rueckgabestring schreiben
                result += row[0] + " "
            # Abbruchbedingung definieren
            if chapter == echap and verse == evers and word == eword:
                break
            # second condition in case of an error in Apparat.LookUpNT
            if chapter > echap:
                break
            word += 1
            if word > maxword:
                verse += 1
                if verse > maxverse:
                    chapter += 1
                    verse = 1
                word   = 2
                maxword = self.getMaxWord(book, chapter, verse)
                maxverse = self.getMaxVerse(book, chapter)
        result[:-1] # cut off last white space
        if fehlvers_started: # schliessende Doppelklammer falls geoeffnet
            result += "]]"
        return result
