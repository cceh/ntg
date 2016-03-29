#!/usr/bin/python

__author__ = "volker.krueger@uni-muenster.de"

class Fehlvers(object):
	"""
	Die Klasse Fehlvers enthaelt in der Liste addresses
	die Anfang- und Endadressen (je als Tupel) der Fehl-
	verse. 
	Da es sich um eine uebersichtliche Liste handelt,
	lege ich sie nicht in der Datenbank ab.
	Die Liste wird im Laufe der Bearbeitung wachsen.
	"""
	def __init__(self):
		self.addresses = []
		self.addresses.append((50837002, 50837046))
		self.addresses.append((51534002, 51534012))
		self.addresses.append((52406020, 52408014))
		self.addresses.append((52829002, 52829024))

	def isFehlvers(self, address):
		"""
		Die Methode gibt True zurueck, wenn die genannte
		Adresse in einem Fehlvers liegt.
		Liegt sie nur teilweise im Fehlvers, so wird False
		zurueckgegeben.
		"""
		for addr in self.addresses:
			if address >= addr[0] and address <= addr[1]:
				return True
		return False
