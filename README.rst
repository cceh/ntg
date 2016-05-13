.. -*- encoding: utf-8; bidi-paragraph-direction: left-to-right; fill-column: 72 -*-

Projektbeschreibung
===================

Partner: Institut für neutestamentliche Textforschung, Münster

Ziele:

- Umsetzung der CBGM (Coherence-based genealogical method) auf
  Datenbankebene (mysql)

- WeiterEntwicklung eines Web-Frontends


Hintergrundwissen
=================


Das Neue Testament
------------------

Es besteht aus:

- \(e) Evangelien

  - (Mk) Markus

  - (Mt) Matthäus

  - \(L) Lukas

  - \(J) Johannes

- \(a) Apostolos

  - (act)  Apostelgeschichte

  - (cath) Katholische Briefe

- \(p) Paulusbriefe (14 Briefe)

- (r = revelatio) Offenbarung des Johannes


Editionen
---------

Herausgegeben durch das Institut für neutestamentliche Textforschung,
Münster.


Nestle-Aland
~~~~~~~~~~~~

Novum Testamentum Graece, 28. Auflage, 2012,
(NA28) (Editio minor)

Handausgabe, etwa 900 Seiten, ab 28€


Editio Critica Maior
~~~~~~~~~~~~~~~~~~~~

Novum Testamentum Graecum, Editio Critica Maior

Historisch kritische Ausgabe

Bereits erschienen: Band IV/1 und Band IV/2,
enthaltend die katholischen Briefe,
etwa 600 Seiten,
ab 98€

Demnächst erscheint: Apostelgeschichte.  Hierfür ist unsere Mithilfe
erwünscht.

.. figure:: http://rosetta.reltech.org/TC/v03/Aland1998-fig1.jpeg

   Beispielseite: Jak 2,3

Die katholischen Briefe wurden ausgewählt, da sie eine größere Variation
besitzen als das übrige NT und sich daher gut für die Entwicklung der
CBGM eignen. ([LOJ]_ §22)


Die Textzeugen
--------------

Etwa 6000 Handschriften.
Handschriften des NT verwenden fast ausschließlich das Codex-Format.

Folgende Arten von Textzeugen werden herangezogen:


Papyri
~~~~~~

Früheste Überlieferungen.  Dem Originaltext am nächsten.

Ab Jahr 125.  Meist nur fragmentarisch.  Hat sich nur im Wüstenklima
erhalten.

Bezeichnung: '𝔓' gefolgt von hochgestellter Zahl (z.B. 𝔓\ :sup:`52`)


Majuskeln
~~~~~~~~~

Ab dem 4. Jahrhundert.  Auf Pergament.  Viele vollständige Abschriften
des NT sind als Majuskel erhalten.  Sehr unterschiedliche Nähe zum
Originaltext.

Bezeichnung: '0' gefolgt von Zahl (z.B. 0189)

Frühere Bezeichnung: lateinische, griechische oder hebräische
Großbuchstaben

Wichtige Majuskeln:

- 01 (א) Codex Sinaiticus eapr IV

- 02 (A) Codex Alexandrinus eapr† V

- 03 (B) Codex Vaticanus eap† IV

- 04 (C) Codex Ephraemi Syri rescriptus eapr† V

- 05 (D) Codex Bezae Cantabrigiensis ea†


Minuskeln
~~~~~~~~~

Ab dem 9. Jahrhundert.  Auf Pergament oder Papier.  Die allermeisten davon
enthalten den byzantinischen Text und sind für uns uninteressant, aber einige
wenige sind dem Originaltext sehr nahe.  Es sind 2800 Minuskeln bekannt.
([TNT]_ S. 140)

Bezeichnung: Zahl (z.B. 33)


Lektionare
~~~~~~~~~~

Lektionare bringen die Texte des NT in der Reihenfolge, die durch die
Leseordnung der Kirche vorgegeben ist.  Es sind 2300 Lektionare bekannt.
Das Sytem der Lektionare entstand geschätzt im 4 Jhd.  (Kuriosum: da das
Kirchenjahr Ostern anfängt, hat es bis zu 57 Wochen.) ([TNT]_ S. 172ff)

Lektionare können den gleichen Text mehrmals enthalten, die
unterschiedlichen Lesungen werden in den Datenbank mit L1, L2
bezeichnet.

Bezeichnung: 'ℓ' gefolgt von Zahl (z.B. ℓ 1178)


Übersetzungen (Versionen)
~~~~~~~~~~~~~~~~~~~~~~~~~

Latein, Syrisch, Koptisch, ...

Haben ergänzende Funktion.  Sie sind wertvoll wenn sie einen frühen Text
als Vorlage benützt haben.  Wörtliche Übersetzungen sind wertvoller als
idiomatische.

Bezeichnung: Sprachkürzel mit hochgestellten Buchstaben (z.B.
sy\ :sup:`c` für den Cureton-Syrer)


Zitate bei den Kirchenvätern (Kommentare)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Haben ergänzende Funktion.

Kommentarhandschriften enthalten den Text des NT oft mehrmals.  Denn dem
eigentlichen Zitat im laufenden Text des Kommentars ist oft der
vollständige Text des Lemmas vorangestellt.

Das eigentliche Zitat genießt eine höheren Wert.  Der Lemma-Text wurde
hingegegen oft durch einen geläufigeren Text ersetzt.  ([TNT]_ S. 179)

Die unterschiedlichen Lesungen werden in der Datenbank mit T1, T2
bezeichnet.

Bezeichnung: Name oder Abkürzung (z.B. Or für Origenes)


Textformen (Texttypen)
----------------------

- Alexandrinischer Text

- Byzantinischer Text (Koine, Mehrheitstext)

- Westlicher Text (D-Text) Textgruppe, die im wesentlichen aus der
  D-Majuskel entstanden ist.

Der byzantinische Text ist am weitesten verbreitet.  (Offizieller Text.)
Durch seine Geläufigkeit bei den Schreibern wurden alte Lesarten oft
durch ihn ersetzt.  Er gilt als minderwertig weil er erst spät
entstanden ist.

Textus Receptus: der von Erasmus von Rotterdam im Jahre 1516 gedruckte
Text.  Er gilt als besonders minderwertig, da Erasmus überstürzt
gearbeitet hat und nur wenige Textzeugen verwendet hat.


Die Datenbank
=============

Die mysql-Datenbank, die uns zur Verfügung gestellt wurde, enthält 28 +
28 Tabellen, je zwei für jedes Kapitel der Apostelgeschichte.  Die erste
Tabelle enthält die Lesarten, die zweite die Lücken (loc, vac).

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


Tabellen und Felder
-------------------

Felder in der Tabelle Att

anfadr, endadr
  Zusammengesetzt aus Buch, Kapitel, Vers, Wort.  Es werden Wörter und
  Zwischenräume gezählt.  Gerade Zahlen bezeichnen ein Wort, ungerade
  einen Zwischenraum.

hsnr
  Interne Handschriftnummer.

hs
  Siglum der Handschrift.  An das Siglum werden Suffixe angehängt, die
  die Hand und die Lesung bezeichnen.  Im Laufe der Verarbeitung werden
  die Lesarten reduziert, bis nur eine Lesart pro Handschrift
  übrigbleibt.  Parallel dazu werden die Suffixe von den Siglen
  entfernt.

labez
  Lesartbezeichnung.  'a' bezeichnet die Lesart im Text und 'b' bis 'y'
  die Lesarten im Apparat.  Lesarten beginnend mit 'z' haben eine
  besondere Bedeutung:

  zu
    ??? Umfaßte Stellen, Fehlverse (Kuckucksverse)

  zv
    There is an illegible addition in the manuscript(s) cited which
    makes it impossible to ascribe it to a known variant.

  zw
    What remains of the text of the manuscript(s) cited would allow
    reconstruction in agreement with two or more different variants.

    In diesm Fall enthält das Feld labezsuf eine durch "/" getrennte
    Liste der LesartBezeichnungen, die in Frage kommen.

  zz
    While at least one letter is extant in the manuscript(s) cited, the
    reading is too lacunose to be identified.

    Alle Lesarten, die aus der Tabelle der Lacunae erzeugt wurden,
    erhalten labez = 'zz'.

  Caveat: die Lesart 'a' kann für dieselbe Passage mehrmals vergeben
  worden sein, immer dann wenn im Nestle-Aland ein positiver Apparat
  benutzt wurde.

labezsuf
  Lesarten können hier mit zusätzlichen Hinweisen versehen werden:

  f
    Fehler (scribal error)

  o
    Orthographicum (orthographical difference)

  durch "/" getrennte Liste
    z.B. "a/b_o/c_f"


Abkürzungen, Suffixe
--------------------

Gebräuchliche Abkürzungen, Symbole, Suffixe.  Werden in der Datenbank in
einigen Feldern benützt aber auch auch an das Siglum der Hs angehängt.

\*
  Erste, ursprüngliche Hand

C*
  Von erster Hand korrigiert

C1
  Erster Korrektor (Korrektoren der ersten Stunde)

C2
  Zweiter Korrektor (Korrektoren aus späteren Jahrhunderten)

C
  Korrektor (Korrektor aus ungewisser Epoche)

L1, L2
  Unterschiedliche Lesungen in einem Lektionar.

T1, T2
  Unterschiedliche Lesungen in einer Kommentarhandschrift.

s, s1, s2
  (supplement) Nachträgliche Ergänzung verlorener Stellen.
  Sie können nicht die Authorität der jeweiligen Hs beanspruchen.

V, vid
  (ut videtur) augenscheinlich.  Unsichere aber höchst wahrscheinliche
  Lesung.

In variants:

lac
  Fehlendes Substrat (lacuna)

vac
  Fehlendes Substrat (vacat)

om
  Fehlender Text (omissio)


Literatur
=========

.. [TNT] Aland, Kurt, and Barbara Aland.  2006.  *Der Text des Neuen
   Testaments: Einführung in die wissenschaftlichen Ausgaben sowie in
   Theorie und Praxis der modernen Textkritik.*  Stuttgart: Dt. Bibelges.

.. [LOJ] Aland, Barbara.  1998.  *Novum Testamentum Graecum Editio
   Critica Maior: Presentation of the First Part: The Letter of James.*
   Münster.  http://rosetta.reltech.org/TC/v03/Aland1998.html
