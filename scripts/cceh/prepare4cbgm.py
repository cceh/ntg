#!/usr/bin/python
# -*- encoding: utf-8 -*-

"""Prepare for CBGM

This script converts the tables used for the production of Nestle-Aland into
tables suitable for CBGM.  Basically it copies the tables, removes unwanted
readings, and converts the apparatus into a positive one.

Author: Marcello Perathoner <marcello.perathoner@uni-koeln.de>

See: https://github.com/cceh/ntg/wiki

"""

from __future__ import unicode_literals

import argparse
import datetime
import itertools
import operator
import re
import sys

import six

import ntg_db
import ntg_tools as tools
from ntg_tools import message, execute, fix


"""
Before manuscript numbers:
    L      lectionary

After manuscript numbers:
    *      original reading
    C      correction (C1, C2: subsequent corrections)
    L1, L2 first, second reading (in lectionaries)
    s      supplement (s1, s2: supplements 1, 2)
    V      ut videtur (apparently)

Instead of letters denoting variants:
    zv     there is an illegible addition in the manuscript(s) cited which
           makes it impossible to ascribe it to a known variant.
    zw     what remains of the text of the manuscript(s) cited would allow
           reconstruction in agreement with two or more different variants
    zz     while at least one letter is extant in the manuscript(s) cited,
           the reading is too lacunose to be identified

After letters denoting variants:
    f      Fehler (scribal error)
    o      orthographicum (orthographical difference)

In variants:
    lac    lacuna
    om     omissio (omission)
"""

DEFAULTS = {
    #'target_table'        : 'ActsAtt_3',
    #'target_table_lac'    : 'ActsLac_3',
    #'target_table_attlac' : 'ActsAttLac_3',
    #'target_table_tmp'    : 'ActsTmp_3',
    'target_table'        : 'Att',
    'target_table_lac'    : 'Lac',
    'target_table_attlac' : 'AttLac',
    'target_table_tmp'    : 'Tmp',
}

CREATE_TABLE_ATT = """
(
  "id"          INTEGER       AUTO_INCREMENT PRIMARY KEY,
  "buch"        INTEGER       DEFAULT NULL,
  "kapanf"      INTEGER       DEFAULT NULL,
  "versanf"     INTEGER       DEFAULT NULL,
  "wortanf"     INTEGER       DEFAULT NULL,
  "kapend"      INTEGER       DEFAULT 0,
  "versend"     INTEGER       DEFAULT 0,
  "wortend"     INTEGER       DEFAULT NULL,
  "hsnr"        INTEGER       DEFAULT NULL,
  "hs"          VARCHAR(32)   DEFAULT NULL,
  "anfadr"      INTEGER       DEFAULT NULL,
  "endadr"      INTEGER       DEFAULT NULL,
  "labez"       VARCHAR(32)   DEFAULT '',
  "labezsuf"    VARCHAR(32)   DEFAULT '',
  "lemma"       VARCHAR(1024) DEFAULT '',
  "lesart"      VARCHAR(1024) DEFAULT '',
  "suffix2"     VARCHAR(255)  DEFAULT '',
  "kontrolle"   VARCHAR(1)    DEFAULT '',
  "fehler"      INTEGER       DEFAULT 0,
  "suff"        VARCHAR(32)   DEFAULT '',
  "vid"         VARCHAR(32)   DEFAULT '',
  "vl"          VARCHAR(32)   DEFAULT '',
  "korr"        VARCHAR(32)   DEFAULT '',
  "lekt"        VARCHAR(32)   DEFAULT '',
  "komm"        VARCHAR(32)   DEFAULT '',
  "anfalt"      INTEGER       DEFAULT NULL,
  "endalt"      INTEGER       DEFAULT NULL,
  "labezalt"    VARCHAR(32)   DEFAULT '',
  "lasufalt"    VARCHAR(32)   DEFAULT '',
  "base"        VARCHAR(1)    DEFAULT '',
  "over"        VARCHAR(1)    DEFAULT '',
  "comp"        VARCHAR(1)    DEFAULT '',
  "over1"       VARCHAR(1)    DEFAULT '',
  "comp1"       VARCHAR(1)    DEFAULT '',
  "printout"    VARCHAR(32)   DEFAULT '',
  "category"    VARCHAR(1)    DEFAULT '',
  "created"     DATE          DEFAULT NULL
)
"""

CREATE_TABLE_LAC = """
(
  "id"        INTEGER       AUTO_INCREMENT PRIMARY KEY,
  "buch"      INTEGER       NOT NULL,
  "kapanf"    INTEGER       NOT NULL,
  "versanf"   INTEGER       NOT NULL,
  "wortanf"   INTEGER       NOT NULL,
  "wortend"   INTEGER       DEFAULT NULL,
  "hsnr"      INTEGER       DEFAULT NULL,
  "hs"        VARCHAR(32)   DEFAULT NULL,
  "anfadr"    INTEGER       DEFAULT NULL,
  "endadr"    INTEGER       DEFAULT NULL,
  "labez"     VARCHAR(32)   NOT NULL,
  "labezsuf"  VARCHAR(32)   DEFAULT NULL,
  "lemma"     VARCHAR(1024) NOT NULL,
  "lesart"    VARCHAR(1024) DEFAULT NULL,
  "suffix2"   VARCHAR(32)   DEFAULT NULL,
  "kontrolle" VARCHAR(1)    DEFAULT NULL,
  "kapend"    INTEGER       DEFAULT 0,
  "versend"   INTEGER       DEFAULT 0,
  "fehler"    INTEGER       DEFAULT 0,
  "suff"      VARCHAR(32)   DEFAULT NULL,
  "vid"       VARCHAR(32)   DEFAULT NULL,
  "vl"        VARCHAR(32)   DEFAULT NULL,
  "korr"      VARCHAR(32)   DEFAULT NULL,
  "lekt"      VARCHAR(32)   DEFAULT NULL,
  "komm"      VARCHAR(32)   DEFAULT NULL,
  "anfalt"    INTEGER       DEFAULT NULL,
  "endalt"    INTEGER       DEFAULT NULL,
  "labezalt"  VARCHAR(32)   DEFAULT NULL,
  "lasufalt"  VARCHAR(32)   DEFAULT NULL,
  "printout"  VARCHAR(32)   DEFAULT NULL,
  "category"  VARCHAR(1)    DEFAULT NULL,
  "base"      VARCHAR(1)    DEFAULT '',
  "over"      VARCHAR(1)    DEFAULT '',
  "comp"      VARCHAR(1)    DEFAULT '',
  "over1"     VARCHAR(1)    DEFAULT '',
  "comp1"     VARCHAR(1)    DEFAULT '',
  "created"   DATE          DEFAULT NULL
)
"""

def fehlverse ():
    return """
    (
      anfadr >= 50837002 and endadr <= 50837047 or
      anfadr >= 51534002 and endadr <= 51534013 or
      anfadr >= 52506020 and endadr <= 52408015 or
      anfadr >= 52829002 and endadr <= 52829025
    )
    """


def lacunae_in_chapters_without_text (dba, parameters):

    cursor = dba.cursor()

    cursor.execute ("""
    SELECT lac.hs, lac.anfadr, lac.endadr
    FROM ActsLac_3 AS lac
    LEFT JOIN ActsAtt_3 AS att
    ON att.hs = lac.hs AND att.kapanf = lac.kapanf
    WHERE att.id IS NULL
    ORDER BY hs, anfadr, endadr

    """.format (**parameters))


def create_indices(cursor):
    message (2, "          Creating indices ...")

    cursor.execute ('CREATE INDEX Hs     ON {target} (hs)'.format (**parameters))
    cursor.execute ('CREATE INDEX Hsnr   ON {target} (hsnr)'.format (**parameters))
    cursor.execute ('CREATE INDEX Anfadr ON {target} (anfadr)'.format (**parameters))
    cursor.execute ('CREATE INDEX Endadr ON {target} (endadr)'.format (**parameters))

    cursor.execute ('CREATE INDEX HsAdr  ON {target} (hs, anfadr, endadr)'.format (**parameters))


def drop_indices(cursor):
    message (2, "          Dropping indices ...")

    cursor.execute ('DROP INDEX IF EXISTS Hs     ON {target}'.format (**parameters))
    cursor.execute ('DROP INDEX IF EXISTS Hsnr   ON {target}'.format (**parameters))
    cursor.execute ('DROP INDEX IF EXISTS Anfadr ON {target}'.format (**parameters))
    cursor.execute ('DROP INDEX IF EXISTS Endadr ON {target}'.format (**parameters))

    cursor.execute ('DROP INDEX IF EXISTS HsAdr  ON {target}'.format (**parameters))


def step1_single(dba, parameters):
    """ Copy tables to new database

    Copy the (28 * 2) tables to 2 tables in a new database.
    Do NOT copy version manuscripts (bible translations).
    Create indices and some views.

    """

    cursor = dba.cursor()

    # Eventually create the database and table
    cursor.execute ('CREATE DATABASE IF NOT EXISTS {target_db}'.format (**parameters))
    # drop_indices (cursor)
    cursor.execute ('DROP TABLE IF EXISTS {target}'.format (**parameters))
    cursor.execute ('DROP TABLE IF EXISTS {target_lac}'.format (**parameters))
    cursor.execute ('DROP TABLE IF EXISTS {target_attlac}'.format (**parameters))
    cursor.execute ('DROP TABLE IF EXISTS {target_tmp}'.format (**parameters))

    cursor.execute ('CREATE TABLE {target} '       .format (**parameters) + CREATE_TABLE_ATT)
    cursor.execute ('CREATE TABLE {target_lac} '   .format (**parameters) + CREATE_TABLE_LAC)
    cursor.execute ('CREATE TABLE {target_attlac} '.format (**parameters) + CREATE_TABLE_ATT)

    cursor.execute ('SHOW COLUMNS IN {target}'.format (**parameters))
    target_columns_att = set ([row[0].lower() for row in cursor.fetchall()])
    cursor.execute ('SHOW COLUMNS IN {target_lac}'.format (**parameters))
    target_columns_lac = set ([row[0].lower() for row in cursor.fetchall()])

    # these columns get special treatment
    target_columns_att -= set (('id', 'created'))
    target_columns_lac -= set (('id', 'created'))

    # Get a list of tables (there are two tables per chapter)
    cursor.execute ('SHOW TABLES FROM {source_db} LIKE %(table_mask)s'.format (**parameters), parameters)

    message (1, "Step  1 : Copying tables ...")

    for row in cursor.fetchall():
        parameters['source_table'] = row[0]
        parameters['source'] = '{source_db}."{source_table}"'.format (**parameters)

        is_lac_table = parameters['source_table'].endswith('lac')
        parameters['t'] = parameters['target_lac'] if is_lac_table else parameters['target']
        target_columns = target_columns_lac if is_lac_table else target_columns_att

        cursor.execute ('SHOW COLUMNS IN {source}'.format (**parameters))
        source_columns = [row[0].lower() for row in cursor.fetchall()]
        common_columns = [column for column in source_columns if column in target_columns]

        parameters['fields']  = ', '.join (common_columns)
        parameters['created'] = datetime.date.today().strftime ("%Y-%m-%d")

        message (2, 'Step  1 : Copying table {source_table}'.format (**parameters))

        cursor.execute ("""
        INSERT INTO {t} ({fields}, created)
        SELECT {fields}, '{created}'
        FROM {source}
        WHERE hsnr < 500000
        """.format (**parameters))

        dba.commit()

    message (1, "Step  1 : Creating indices ...")
    create_indices(cursor)

    execute (cursor, """
    CREATE OR REPLACE VIEW {target_db}.Passages AS
    SELECT DISTINCT buch, kapanf, versanf, wortanf, kapend, versend, wortend, anfadr, endadr
    FROM {target}
    """, parameters)

    execute (cursor, """
    CREATE OR REPLACE VIEW {target_db}.NestedPassages AS
    SELECT a.anfadr AS ianfadr, a.endadr AS iendadr, b.anfadr AS oanfadr, b.endadr AS oendadr
    FROM Passages a
    JOIN Passages b
    WHERE a.anfadr >= b.anfadr AND a.endadr <= b.endadr AND
      NOT (a.anfadr = b.anfadr AND a.endadr = b.endadr)
    ORDER BY a.anfadr, a.endadr DESC
    """, parameters)

    dba.commit()


def step1b_single (dba, parameters):
    """ No need to delete translations because we didn't copy them in the
    first place. """


def step1c_single (dba, parameters):
    """ Fix data entry errors.

    Fix a bogus hsnr.

    These errors should be fixed in the original database.

    """

    message (1, "Step  1c: Data entry fixes ...")
    cursor = dba.cursor()

    fix (cursor, "Wrong hsnr", """
    SELECT DISTINCT hs, hsnr, kapanf
    FROM {target}
    WHERE hs LIKE 'L1188s2%%' AND hsnr = 411881
    """, """
    UPDATE {target}
    SET hsnr = 411882
    WHERE hs LIKE 'L1188s2%%'
    """, parameters)

    dba.commit()


def step2_single (dba, parameters):
    """Data cleanup

    Delete spurious '\r' characters in suffix2 field.
    Replace NULL entries with ''.

    2. Korrekturen in den Acts-Tabellen: L-Notierungen nur im Feld LEKT,
    *- u. C-Notierungen nur im Feld KORR.

    Gelegentlich steht an Stellen, an denen mehrere Lektionen desselben
    Lektionars zu verzeichnen sind, in KORR ein ueberfluessiges 'L' ohne Nummer.
    Es kommt auch vor, dass L1 und L2 in KORR stehen oder C-Notierungen in LEKT.

    """

    message (1, "Step  2 : Generic cleanup ...")
    cursor = dba.cursor()

    for parameters['t'] in (parameters['target'], parameters['target_lac']):
        # Delete spurious '\r' characters in suffix2 field.
        cursor.execute ("""
        UPDATE {t}
        SET suffix2 = REGEXP_REPLACE (suffix2, '\r', '')
        WHERE suffix2 LIKE '%\r%'
        """.format (**parameters))

        # replace NULL fields with ''
        for parameters['col'] in ('lekt', 'korr', 'suffix2', 'komm', 'lemma', 'comp', 'base'):
            cursor.execute ("""
            UPDATE {t} SET {col} = '' WHERE {col} IS NULL
            """.format (**parameters))

    message (1, "Step  2 : Fix korr and lekt ...")

    execute (cursor, """
    UPDATE {target} SET lekt = korr, korr = '' WHERE korr REGEXP '^L'
    """, parameters)

    execute (cursor, """
    UPDATE {target} SET korr = lekt, lekt = '' WHERE lekt REGEXP '[C*]'
    """, parameters)

    execute (cursor, """
    UPDATE {target} SET korr = '*'  WHERE korr = '' AND suffix2 REGEXP '[*]'
    """, parameters)

    cursor.execute ("""
    UPDATE {target} SET lekt = REGEXP_SUBSTR (suffix2, 'L[1-9]')
    WHERE lekt IN ('', 'L') AND suffix2 REGEXP 'L[1-9]'
    """.format (**parameters))

    cursor.execute ("""
    UPDATE {target} SET korr = REGEXP_SUBSTR (suffix2, 'C[1-9*]')
    WHERE korr IN ('', 'C') AND suffix2 REGEXP 'C[1-9*]'
    """.format (**parameters))

    fix (cursor, "Wrong labez", """
    SELECT labez, labezsuf, kapanf, count (*) AS anz FROM {target}
    WHERE labez REGEXP '.[fo]'
    GROUP BY labez, labezsuf, kapanf
    ORDER BY labez, labezsuf, kapanf
    """, """
    UPDATE {target}
    SET labez = SUBSTRING (labez, 1, 1),
        labezsuf = SUBSTRING (labez, 2, 1)
    WHERE labez REGEXP '.[fo]'
    """, parameters)

    dba.commit()


def step3_single (dba, parameters):
    # No need to drop fields because we didn't copy them in the first place
    pass


def step4_single (dba, parameters):
    # No need to copy the table because we already created it in the right place
    pass


def step5_single (dba, parameters):
    """ Delete passages without variants

    5. Stellen löschen, an denen nur eine oder mehrere f- oder o-Lesarten vom
    A-Text abweichen. Hier gibt es also keine Variante.

    Stellen ohne Varianten sind für die CBGM irrelevant.  Stellen mit
    ausschließlich 'z%' Lesearten ebenso.

    Nicht löschen, wenn an dieser variierten Stelle eine
    Variante 'b' - 'y' erscheint.

    Änderung 2014-12-16:
    Act 28,29/22 gehört zu einem Fehlvers. Dort gibt es u.U. keine Variante neben
    b, sondern nur ein Orthographicum. Wir suchen also nicht mehr nach einer
    Variante 'b' bis 'y', sondern zählen die Varianten. Liefert getReadings nur 1
    zurück, gibt es keine Varianten.

    """

    message (1, "Step  5 : Delete passages without variants ...")

    cursor = dba.cursor()
    # We need a nested subquery to avoid MySQL limitations. See:
    # https://dev.mysql.com/doc/refman/5.7/en/subquery-restrictions.html
    execute (cursor, """
    DELETE FROM {target} WHERE (anfadr, endadr) IN (
      SELECT anfadr, endadr FROM (
        SELECT anfadr, endadr FROM {target}
        WHERE labez NOT REGEXP '^z' OR labezsuf NOT REGEXP 'f|o'
        GROUP BY anfadr, endadr, labez
        HAVING count(*) = 1
      ) AS tmp
    )
    """, parameters)
    dba.commit()


def step5b_single (dba, parameters):
    """Process Commentaries

    Wenn bei Wiederholung des Lemmatextes in Kommentarhandschriften Varianten
    entstanden sind, wird mit zw (=zweifelhaft) verzeichnet.

    5b. 20. Mai 2015
    Commentary manuscripts like 307 cannot be treated like lectionaries where we
    choose the first text. If a T1 or T2 reading is found they have to be
    deleted. A new zw reading is created containing the old readings as suffix.

    This has to be done as long as both witnesses are present.

    If the counterpart of one entry belongs to the list of lacunae
    the witness will be treated as normal witness. The T notation can be deleted.

    DIVINATIO: If there is only one T1 or T2 reading for that passage and
    manuscript, unset the 'T' suffix.  If there are both T1 and T2 readings, merge
    them into one 'zw' reading.

    """

    message (1, "Step  5b: Processing Commentaries ...")

    cursor = dba.cursor()

    fix (cursor, "Incompatible lekt and suffix2 for T reading", """
    SELECT hs, anfadr, lekt, suffix2
    FROM {target}
    WHERE hs REGEXP 'T[1-9]' AND hs NOT REGEXP suffix2
    """, """
    UPDATE {target}
    SET lekt    = REPLACE (REGEXP_SUBSTR (hs, 'T[1-9]'), 'T', 'L'),
        suffix2 = REGEXP_SUBSTR (hs, 'T[1-9]')
    WHERE hs REGEXP 'T[1-9]'
    """, parameters)

    # T1 or T2 but not both
    # promote to 'non-commentary' status by stripping T[1-9] from hs
    execute (cursor, """
    UPDATE {target} u
    JOIN (
      SELECT id
      FROM {target}
      WHERE hs REGEXP 'T[1-9]'
      GROUP BY hsnr, anfadr, endadr
      HAVING COUNT(*) = 1
    ) AS t
    ON u.id = t.id
    SET hs = REGEXP_REPLACE (hs, 'T[1-9]', ''),
        suffix2 = REGEXP_REPLACE (suffix2, 'T[1-9]', '')
    """, parameters)

    # T1 and T2
    # group both T readings into one variant and set labez = 'zw'
    execute (cursor, """
    SELECT id, labez, labezsuf, CONCAT (hsnr, anfadr, endadr) AS k
    FROM {target}
    WHERE (hsnr, anfadr, endadr) IN (
      SELECT DISTINCT hsnr, anfadr, endadr
      FROM {target}
      WHERE hs REGEXP 'T[1-9]'
    )
    ORDER BY k  /* key for itertools.groupby */
    """, parameters)

    rows = cursor.fetchall ()
    if len (rows):
        for k, group in itertools.groupby (rows, operator.itemgetter (3)):
            ids = []
            labez = set ()
            for row in group:
                ids.append (six.text_type (row[0]))
                labez.add (row[1] + ('_' + row[2] if row[2] else ''))

            assert len (ids) > 1, "Programming error in commentary processing."

            parameters['ids'] = ', '.join (ids[1:])
            execute (cursor, """
            DELETE FROM {target}
            WHERE id IN ({ids})
            """, parameters)

            parameters['id'] = ids[0]
            parameters['labezsuf'] = '/'.join (sorted (labez))
            execute (cursor, """
            UPDATE {target}
            SET labez = 'zw',
                labezsuf = '{labezsuf}',
                hs = REGEXP_REPLACE (hs, 'T[1-9]', ''),
                suffix2 = REGEXP_REPLACE (suffix2, 'T[1-9]', '')
            WHERE id = {id}
            """, parameters)

    dba.commit()


def step6_single (dba, parameters):
    """ Delete later hands

    6. Lesarten, die nicht von der ersten Hand stammen, loeschen.  Bei
    mehreren Lektionslesarten gilt die L1-Lesart.  Ausnahme: Bei
    Selbstkorrekturen wird die *-Lesart geloescht und die C*-Lesart
    beibehalten.

    Erweiterung vom 15.02.2013: Wenn die einzige Variante an einer Stelle nur
    von einem oder mehreren Korrektoren bezeugt ist (z.B. 26:8/17), gehoert
    die Stelle nicht in die Tabelle.  Es muss also noch eine Pruefung
    stattfinden, ob nach diesem Vorgang eine Stelle noch immer eine variierte
    Stelle ist. Wenn nicht, kann der Datensatz geloescht werden.

    QUESTION: what is lekt = 'N'?
    QUESTION: what is suffix2 = 'A'?

    """
    message (1, "Step  6 : Delete later hands ...")

    cursor = dba.cursor()

    for parameters['t'] in (parameters['target'], parameters['target_lac']):
        # Delete all other readings if there is a C* reading.
        for parameters['regexp'] in (r'C\\*', ):
            cursor.execute ("""
            DELETE FROM {t}
            WHERE (hsnr, anfadr, endadr) IN (
              SELECT hsnr, anfadr, endadr FROM (
                SELECT hsnr, anfadr, endadr
                FROM {t}
                WHERE suffix2 REGEXP '{regexp}'
              ) AS tmp
            )
            AND suffix2 NOT REGEXP '{regexp}'
            """.format (**parameters))

        cursor.execute ("""
        DELETE FROM {t}
        WHERE (lekt = 'L2' OR korr IN ('C', 'C1', 'C2', 'C3', 'A', 'K'))
          AND suffix2 NOT LIKE '%C*%'
        """.format (**parameters))

        fix (cursor, "Bogus Suffixes", """
        SELECT suffix2
        FROM {t}
        WHERE suffix2 REGEXP 'A|K|L2|T2'
        """, """
        DELETE FROM {t}
        WHERE suffix2 REGEXP 'A|K|L2|T2'
        """, parameters)

        dba.commit()


def step6b_single (dba, parameters):
    """Process Sigla

    Handschriften, die mit einem "V" für videtur gekennzeichnet sind, werden
    ebenso wie alle anderen behandelt. Das "V" kann also getilgt werden. Die
    Eintragungen für "ursprünglich (*)" und "C*" werden ebenfalls
    gelöscht. Schließlich auch die Zusätze zur Handschriftennummer wie
    „T1“. Diese Eintragungen werden (bisher) einfach an die
    Handschriftenbezeichnung angehängt.

    Der Eintrag 'videtur', gekennzeichnet durch ein 'V' hinter der
    Handschriftennummer, spielt fuer die CBGM keine Rolle. Ein eventuell
    vorhandenes 'V' muss getilgt werden. Gleiches gilt fuer die Eintraege '*'
    und 'C*'.

    """

    message (1, "Step  6b: Delete [CLTV*] from HS ...")

    cursor = dba.cursor()

    for parameters['t'] in (parameters['target'], parameters['target_lac']):
        parameters['regexp'] = '[CLTV*]+[0-9]*$'
        # FIXME: MariaDB specific function REGEXP_REPLACE
        execute (cursor, """
        UPDATE {t}
        SET hs = REGEXP_REPLACE (hs,'{regexp}', '')
        WHERE hs REGEXP '[0-9]+s?{regexp}'
        """, parameters)
        execute (cursor, """
        UPDATE {t}
        SET suffix2 = REGEXP_REPLACE (suffix2, '{regexp}', '')
        WHERE suffix2 REGEXP '{regexp}'
        """, parameters)

    fix (cursor, "Hs with more than one hsnr", """
    SELECT hs FROM (
      SELECT DISTINCT hs, hsnr FROM {target}
    ) AS tmp
    GROUP BY hs
    HAVING count(*) > 1
    """, None, parameters)

    # print some debug info
    cursor.execute ("""
    SELECT lekt, korr, suffix2, count (*) AS anz
    FROM {target}
    GROUP BY lekt, korr, suffix2
    ORDER BY lekt, korr, suffix2
    """.format (**parameters))
    tools.tabulate (cursor)

    # Debug hs where hs and suffix2 still mismatch
    fix (cursor, "hs and suffix2 mismatch", """
    SELECT hs, suffix2, anfadr, endadr, lemma
    FROM {target}
    WHERE hs NOT REGEXP suffix2
    ORDER BY hs, anfadr
    """, None, parameters)

    # cursor.execute ("""
    # UPDATE {t}
    # SET hs = CONCAT (hs, suffix2)
    # WHERE hs NOT LIKE CONCAT('%', suffix2)
    # """.format (**parameters))

    fix (cursor, "Hsnr with more than one hs", """
    SELECT hsnr FROM (
      SELECT DISTINCT hs, hsnr FROM {target}
    ) AS tmp
    GROUP BY hsnr
    HAVING count(*) > 1
    """, """
    UPDATE
        {target} t
    JOIN
      (SELECT min(hs) AS minhs, hsnr FROM {target} GROUP BY hsnr ORDER BY hs) AS g
    ON
      t.hsnr = g.hsnr
    SET t.hs = g.minhs
    """, parameters)

    fix (cursor, "Hs with lacunae but w/o text", """
    SELECT DISTINCT hsnr
    FROM {target_lac}
    WHERE hsnr NOT IN (
      SELECT DISTINCT hsnr FROM {target}
    )
    """, """
    DELETE
    FROM {target_lac}
    WHERE hsnr NOT IN (
      SELECT DISTINCT hsnr FROM {target}
    )
    """, parameters)

    dba.commit()


def step7_single (dba, parameters):
    message (1, "Step  7 : Fix 'zw' ...")

    cursor = dba.cursor()

    cursor.execute ("SELECT id, labezsuf FROM {target} WHERE labez = 'zw'"
                    .format (**parameters))

    updated = 0
    for row in cursor.fetchall ():
        id_ = row[0]
        labezsuf = row[1]
        unique_labez_suffixes = tuple (set ([suf[0] for suf in labezsuf.split ('/')]))
        if len (unique_labez_suffixes) == 1:
            cursor.execute ("UPDATE {target} SET labez = %(labez)s WHERE id = %(id)s".format (**parameters),
                            { 'labez': unique_labez_suffixes[0], 'id': id_ } )
            updated += 1

    dba.commit()
    message (2, "          %d zw labez updated" % updated)


def step9_single (dba, parameters):
    # Stellenbezogene Lückenliste füllen. Parallel zum Apparat wurde eine
    # systematische Lückenliste erstellt, die die Lücken aller griechischen
    # Handschriften enthält. Wir benötigen diese Information jedoch jeweils für
    # die variierten Stellen.

    # Step 9 (Krueger) builds a lacuna table containing an entry for each
    # manuscript and passage inside a lacuna. Then, in step 10, it adds 'zz'
    # readings to the Acts table for each passage inside a lacuna using the
    # lacuna table of step 9.  We short-circuit the lacuna table.


    message (1, "Step  9 : Create Lacunae Table ...")

    cursor = dba.cursor()

    # First clean up the lacunae table as any errors there will be multiplied by
    # this step.

    fix (cursor, "nested lacunae", """
    SELECT lac.id, lac.hs, lac.anfadr, lac.endadr
    FROM {target_lac} AS lac
    JOIN (
      SELECT MIN (a.id) as id, a.hs, a.anfadr, a.endadr
      FROM {target_lac} a
      JOIN {target_lac} b
      WHERE a.hs = b.hs AND a.anfadr <= b.anfadr AND a.endadr >= b.endadr
      GROUP BY a.hs, a.anfadr, a.endadr
      HAVING count(*) > 1
      ORDER BY hs, anfadr, endadr DESC
    ) AS t
    WHERE lac.hs = t.hs
      AND lac.anfadr >= t.anfadr
      AND lac.endadr <= t.endadr
    """, """
    DELETE lac
    FROM {target_lac} lac
    JOIN (
      SELECT MIN (a.id) as id, a.hs, a.anfadr, a.endadr
      FROM {target_lac} a
      JOIN {target_lac} b
      WHERE a.hs = b.hs AND a.anfadr <= b.anfadr AND a.endadr >= b.endadr
      GROUP BY a.hs, a.anfadr, a.endadr
      HAVING count(*) > 1
      ORDER BY hs, anfadr, endadr DESC
    ) AS t
    WHERE lac.hs = t.hs
      AND lac.anfadr >= t.anfadr
      AND lac.endadr <= t.endadr
      AND lac.id <> t.id
    """, parameters)

    dba.commit()

    # Delete all texts in lacunae.  This is a stopgap measure until Münster
    # cleans up the tables.
    fix (cursor, "text in lacunae", """
    SELECT t.hs, t.hsnr, t.anfadr, t.endadr, lac.anfadr as lacanfadr, lac.endadr as lacendadr, t.labez, t.lemma, t.lesart
    FROM {target} t
    JOIN {target_lac} lac
    ON t.hs = lac.hs AND t.anfadr > lac.anfadr AND t.endadr < lac.endadr
    ORDER BY t.hsnr, t.hs, t.anfadr
    """, """
    DELETE FROM {target}
    WHERE id IN (
      SELECT id FROM (
        SELECT t.id
        FROM {target} t
        JOIN {target_lac} lac
        ON t.hs = lac.hs AND t.anfadr > lac.anfadr AND t.endadr < lac.endadr
      ) AS tmp
    )
    """, parameters)

    # Create a `lacuna´ for each passage a manuscript does not contain

    message (2, "Step  9 : Add 'zz' readings for lacunae ...")

    execute (cursor, """
    INSERT INTO {target} (buch, kapanf, versanf, wortanf, kapend, versend, wortend,
                          anfadr, endadr, hs, hsnr, anfalt, endalt, labez, labezsuf,
                          lemma, lesart)
    SELECT t.buch, t.kapanf, t.versanf, t.wortanf, t.kapend, t.versend, t.wortend,
           t.anfadr, t.endadr, lac.hs, lac.hsnr, t.anfadr, t.endadr, 'zz', '',
           '', 'lac'
      FROM
        /* all passages */
        Passages t /* (SELECT DISTINCT buch, kapanf, versanf, wortanf, kapend, versend, wortend,
           anfadr, endadr FROM {target}) AS t */
      JOIN
        /* all lacunae */
        {target_lac} lac
      ON t.anfadr > lac.anfadr AND t.endadr < lac.endadr

    """, parameters)
    dba.commit()

    message (2, "Step  9 : Done")


def step10_single (dba, parameters):
    message (1, "Step 10: Add 'a' readings ...")

    # Ausgangspunkt ist der Apparat mit allen für die Druckfassung notwendigen
    # Informationen.  Diese Datenbasis muss für die CBGM bearbeitet werden.  Die
    # Ausgangsdaten stellen einen negativen Apparat dar, d.h. die griechischen
    # handschriftlichen Zeugen, die mit dem rekonstruierten Ausgangstext
    # übereinstimmen, werden nicht ausdrücklich aufgelistet.  Aufgelistet werden
    # alle Zeugen, die von diesem Text abweichen bzw. Korrekturen oder
    # Alternativlesarten haben.  Ziel ist es, einen positiven Apparat zu
    # erhalten.  Wir benötigen einen Datensatz pro griechischem
    # handschriftlichen Zeugen erster Hand und variierten Stelle (einschließlich
    # der Lücken).  D.h. für jede variierte Stelle liegt die explizite
    # Information vor, ob die Handschrift dem Ausgangstext folgt, einen anderen
    # Text oder gar keinen Text hat, weil z.B. die Seite beschädigt ist.
    # Korrekturen oder Alternativlesarten werden für die CBGM ignoriert.
    #
    # Bezeugung der a-Lesarten auffüllen (d.h. einen positiven Apparat
    # herstellen).  Sie setzt sich zusammen aus allen in der 'ActsMsList' für
    # das jeweilige Kapitel geführten Handschriften, die an der jeweils
    # bearbeiteten Stelle noch nicht bei einer Variante oder in der Lückenliste
    # stehen.

    # Insert the lesart of hs = 'A' for each passage that is not yet in the
    # table.  Lacunae are already accounted for.

    cursor = dba.cursor()

    execute (cursor, """
    INSERT INTO {target} (hsnr, hs, anfadr, endadr, buch, kapanf, versanf, wortanf,
                          kapend, versend, wortend, labez, labezsuf, anfalt, endalt,
                          lesart, base)
    SELECT hs.hsnr, hs.hs, a.anfadr, a.endadr, a.buch, a.kapanf, a.versanf, a.wortanf,
           a.kapend, a.versend, a.wortend, a.labez, a.labezsuf, a.anfalt, a.endalt,
           a.lesart, a.base
    FROM
      /* all passages from A */
      (SELECT * FROM {target} WHERE hs = 'A') AS a

    JOIN
      /* all manuscripts */
      (SELECT DISTINCT hs, hsnr FROM {target} WHERE hs <> 'A') AS hs

    LEFT JOIN
      /* negated join on all witnessed passages */
      {target} t

    ON t.hs = hs.hs AND t.anfadr = a.anfadr AND t.endadr = a.endadr

    WHERE t.id IS NULL

    """, parameters)
    dba.commit()

    fix (cursor, "Manuscripts with duplicated passages", """
    SELECT hs, anfadr, endadr FROM {target} GROUP BY hs, anfadr, endadr HAVING COUNT (*) > 1
    """, None, parameters)

    execute (cursor, """
    /* Set comp = 'x' on nested variants. */
    UPDATE {target} t
    JOIN (
      /* this subquery materializes the view: huge performance gain */
      SELECT ianfadr, iendadr FROM NestedPassages
    ) as n
    ON t.anfadr = n.ianfadr AND t.endadr = n.iendadr
    SET comp = 'x'
    """, parameters)

    parameters['fehlverse'] = fehlverse ()
    execute (cursor, """
    UPDATE {target}
    SET labez = 'zu', lesart = ''
    WHERE comp = 'x' AND base = 'a' AND {fehlverse}
    """, parameters)

    execute (cursor, """
    UPDATE {target}
    SET lesart = 'lac'
    WHERE labez = 'zz'
    """, parameters)

    dba.commit()
    message (2, "Step 10 : Done")


if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Prepare a new database for CBGM')

    parser.add_argument('source_db', metavar='SOURCE_DB', help='the source database (required)')
    parser.add_argument('target_db', metavar='TARGET_DB', help='the target database (required)')
    parser.add_argument('-r', '--range', default='',
                        help='range of steps (default: all)')
    parser.add_argument('-v', '--verbose', dest='verbose', action='count',
                        help='increase output verbosity')
    parser.add_argument('-c', '--chapter', dest='chapter', type=int, default=0,
                        help='the chapter number (optional, default=all chapters)')
    parser.add_argument('-p', '--profile', dest='profile',
                        choices=['local', 'remote'], default='remote',
                        metavar='PROFILE', help="the database profile ('local' or 'remote')")

    args = parser.parse_args ()

    if not re.match ('^[-0-9]*$', args.range):
        print ("Error in range option")
        parser.print_help ()
        sys.exit ()

    if '-' in args.range:
        args.range = args.range.split ('-')
    else:
        args.range = [args.range, args.range]

    args.range[0] = int (args.range[0] or  1)
    args.range[1] = int (args.range[1] or 99)

    dba = ntg_db.DBA (args.profile)
    # Make MySQL more compatible with other SQL databases
    dba.cursor ().execute ("SET sql_mode='ANSI'")

    args.start_time = datetime.datetime.now ()
    tools.args = args
    parameters = tools.init_parameters (DEFAULTS)

    try:
        for step in range(args.range[0], args.range[1] + 1):
            if step == 1:
                step1_single  (dba, parameters)
                step1b_single (dba, parameters)
                step1c_single (dba, parameters)
                continue
            if step == 2:
                step2_single  (dba, parameters)
                continue
            if step == 3:
                step3_single  (dba, parameters)
                continue
            if step == 4:
                step4_single  (dba, parameters)
                continue
            if step == 5:
                step5_single  (dba, parameters)
                step5b_single (dba, parameters)
                continue
            if step == 6:
                step6_single  (dba, parameters)
                step6b_single (dba, parameters)
                continue
            if step == 7:
                step5_single  (dba, parameters) # again
                step7_single  (dba, parameters)
                if args.verbose >= 1:
                    tools.print_stats(dba, parameters)
                continue
            if step == 9:
                step9_single  (dba, parameters)
                if args.verbose >= 1:
                    tools.print_stats(dba, parameters)
                continue
            if step == 10:
                step10_single (dba, parameters)
                if args.verbose >= 1:
                    tools.print_stats(dba, parameters)

    except KeyboardInterrupt:
        dba.rollback()

    dba.close()

    message (1, "          Done")
