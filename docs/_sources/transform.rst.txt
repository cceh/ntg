======================
 Transformation tools
======================

Transform the Nestle-Aland database into a database suitable for the CBGM.

Die mysql-Datenbank, die uns zur Verfügung gestellt wurde, enthält 28 +
28 Tabellen, je zwei für jedes Kapitel der Apostelgeschichte.  Die erste
Tabelle enthält die Lesarten, die zweite die Lücken.

Aus diesen Tabellen wird der Nestle-Aland automagisch erstellt.

Die Tabellen müssen nun für die CBGM umgeformt werden.  Dafür gibt es
eine Reihe von Skripten (in perl und python).

Die Tabelle der Lesarten ist ein negativer Apparat.  Sie enthält den Text
des Archetypus (HS = A) und alle davon abweichenden Stellen.

Für die CBGM benötigen wir einen positiven Apparat.  Dieser wird aus dem
negativen Apparat und der Tabelle der Lücken erstellt.  Zuerst wird für
jede Passage und jede Handschrift ein Lückeneintrag erstellt wenn diese
Handschrift an dieser Passage eine Lücke aufweist.  Dann wird für jede
Passage und jede Handschrift die Lesart der HS A eingefügt, falls diese
Handschrift an dieser Passage noch keinen Text oder Lückeneintrag hat.
Am Ende haben wir für jede Passage und jede Handschrift einen Datensatz.

Die Datenbank wird auch von Lesarten bereinigt, die für den
Nestle-Aland, aber nicht für die CBGM relevant sind.  Das sind z.B. alle
Passagen die nur eine Lesart aufweisen (2/3 (!) des NT), alle
Korrekturen, die nicht von der ersten Hand stammen und Lesarten die auf
orthographische Fehler oder unterschiedliche orthographische
Konventionen zurückgehen.

    Ausgangspunkt ist der Apparat mit allen für die Druckfassung notwendigen
    Informationen.  Diese Datenbasis muss für die CBGM bearbeitet werden.  Die
    Ausgangsdaten stellen einen negativen Apparat dar, d.h. die griechischen
    handschriftlichen Zeugen, die mit dem rekonstruierten Ausgangstext
    übereinstimmen, werden nicht ausdrücklich aufgelistet.  Aufgelistet werden
    alle Zeugen, die von diesem Text abweichen bzw. Korrekturen oder
    Alternativlesarten haben.  Ziel ist es, einen positiven Apparat zu erhalten.
    Wir benötigen einen Datensatz pro griechischem handschriftlichen Zeugen
    erster Hand und variierten Stelle (einschließlich der Lücken).  D.h. für
    jede variierte Stelle liegt die explizite Information vor, ob die
    Handschrift dem Ausgangstext folgt, einen anderen Text oder gar keinen Text
    hat, weil z.B. die Seite beschädigt ist.  Korrekturen oder
    Alternativlesarten werden für die CBGM ignoriert.

    -- ArbeitsablaufCBGMApg_Db.docx


Tabellen und Felder
===================


Felder in der Tabelle LocStemEd
-------------------------------

.. attribute:: id

  Primärer Schlüssel

.. attribute:: varid

  id der variierten Stelle

.. attribute:: varnew

  Gleich wie varid oder neue id nach Splitt.

.. attribute:: s1

  Ursprung der Variante

.. attribute:: s2

  Eventueller zweiter Ursprung der Variante.

.. attribute:: begadr, endar

  Stelle (Passage)

.. attribute:: w

  Flag für "Westlicher Text".  Hat für die CBGM keine Bedeutung.


:mod:`scripts.cceh.prepare4cbgm` --- prepare4cbgm
=================================================

.. automodule:: scripts.cceh.prepare4cbgm
   :members:
