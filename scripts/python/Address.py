#! /usr/bin/python
#-*- encoding: utf-8 -*-
"""
Hilfsmodul zur Verwaltung von Bibelstellen.
"""
__author__="volker.krueger@uni-muenster.de"

def decodeAdr(anfadr, endadr):
    """
    Generiere siebenteilige Adressvariablen aus den zusammengesetzten
    Anfang- und Endadresse.
    """
    sAnf    = str(anfadr)
    sEnd    = str(endadr)
    if len(sAnf) == 8:
        buch    = int(sAnf[0])
        kapanf  = int(sAnf[1:3])
        versanf = int(sAnf[3:5])
        wortanf = int(sAnf[5:])
    else:
        buch    = int(sAnf[0:2])
        kapanf  = int(sAnf[2:4])
        versanf = int(sAnf[4:6])
        wortanf = int(sAnf[6:])
    if len(sEnd) == 8:
        kapend  = int(sEnd[1:3])
        versend = int(sEnd[3:5])
        wortend = int(sEnd[5:])
    else:
        kapend  = int(sEnd[2:4])
        versend = int(sEnd[4:6])
        wortend = int(sEnd[6:])
    return buch, kapanf, versanf, wortanf, kapend, versend, wortend
def encodeAdr(buch, kapanf, versanf, wortanf, kapend, versend, wortend):
    """
    Generiere zusammengesetzte Adressen (als Zahlen) aus sieben Einzelvariablen.
    """
    sAnf = sEnd = ""
    sAnf += str(buch)
    sAnf += formatNumber(kapanf, 2)
    sAnf += formatNumber(versanf, 2)
    sAnf += formatNumber(wortanf, 3)
    sEnd += str(buch)
    sEnd += formatNumber(kapend, 2)
    sEnd += formatNumber(versend, 2)
    sEnd += formatNumber(wortend, 3)
    return int(sAnf), int(sEnd)

def encodeSingleAdr(buch, kapitel, vers, wort):
    s  = ""
    s += str(buch)
    s += formatNumber(kapitel, 2)
    s += formatNumber(vers, 2)
    s += formatNumber(wort, 3)
    return int(s)

def formatNumber(number, count):
    """
    Gibt eine Zahl als String zurueck. Fehlende Stellen koennen mit Nullen
    aufgefuellt werden.
    """
    s = str(number)
    while len(s) < count:
        s = "0" + s
    return s

def hs2hsnr(hs):
    if hs == "A":
        return 0
    result = ""
    shs = str(hs)
    # cut off '*' or 'C', 'C1' etc.
    delimiters = ("*", "C", "A", "K", "L", "T", "V")
    for delim in delimiters:
        sPos = shs.find(delim, 1) # not the first position of the string
        if sPos >= 1:
            shs = shs[:sPos]
    # check first character
    if shs[0] == "P":
        result = "1"
        shs = shs[1:]
    elif shs[0] == "0":
        result = "2"
        shs = shs[1:]
    elif shs[0] == "L":
        result = "4"
        shs = shs[1:]
    else:
        result = "3"
    # looking for a supplement
    supplement = "0"
    sPos = -1
    sPos = shs.find("S")
    if sPos < 0:
        sPos = shs.find("s")
        if sPos >= 0:
            supplement = "1"
    else:
        supplement = "1"
    if sPos >= 0:
        if not (shs.endswith("s") or shs.endswith("S")):
            supplement = shs[sPos+1:]
        result += formatNumber(shs[:sPos], 4) + supplement
    else:
        result += formatNumber(shs, 4) + supplement
    return int(result)

def hsnr2hs(hsnr):
    """
    Handschriftennummer -> GA-Nummer
    """
    if hsnr == 0:
        return "A"
    result = ""
    s = str(hsnr)
    if s.startswith("1"):
        result += "P"
    elif s.startswith("2"):
        result += "0"
    elif s.startswith("4"):
        result += "L"
    nr = s[1:5]
    result += str(int(nr))
    if s[5] != "0":
        result += "s" + s[5]
    return result
