#!/usr/bin/python
# -*- encoding: utf-8 -*-

"""Prepare a database for CBGM

This script converts the tables used for the production of Nestle-Aland into
tables suitable for CBGM.  Basically it copies the tables, removes unwanted
readings, and converts the apparatus into a positive one.

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

See also: https://github.com/cceh/ntg

Author: Marcello Perathoner <marcello.perathoner@uni-koeln.de>

"""

from __future__ import unicode_literals

import argparse
import datetime
import itertools
import operator
import re
import sys

import six

import ntg_db as db
import ntg_tools as tools
from ntg_tools import message, execute, debug, fix


DEFAULTS = {
    #'att'    : 'ActsAtt_3',
    #'lac'    : 'ActsLac_3',
    #'attlac' : 'ActsAttLac_3',
    #'tmp'    : 'ActsTmp_3',

    'att'     : 'Att',
    'lac'     : 'Lac',
    'attlac'  : 'AttLac',
    'vp'      : 'VP',
    'rdg'     : 'Rdg',
    'witn'    : 'Witn',
    'listval' : 'MsListVal',
    'vg'      : 'VG',
    'tmp'     : 'Tmp',
}

N_FIELDS = 'base comp comp1 komm kontrolle korr lekt over over1 suff suffix2 vid vl'.split ()
""" Field to look for 'N' and NULL """

NULL_FIELDS = 'lemma lesart'.split ()
""" Fields to look for NULL """

def create_indices (cursor):
    message (2, "          Creating indices ...")

    cursor.execute ('CREATE INDEX Hs     ON {att} (hs)'.format (**parameters))
    cursor.execute ('CREATE INDEX Hsnr   ON {att} (hsnr)'.format (**parameters))
    cursor.execute ('CREATE INDEX Anfadr ON {att} (anfadr)'.format (**parameters))
    cursor.execute ('CREATE INDEX Endadr ON {att} (endadr)'.format (**parameters))

    cursor.execute ('CREATE INDEX HsAdr  ON {att} (hs, anfadr, endadr)'.format (**parameters))


def drop_indices (cursor):
    message (2, "          Dropping indices ...")

    cursor.execute ('DROP INDEX IF EXISTS Hs     ON {att}'.format (**parameters))
    cursor.execute ('DROP INDEX IF EXISTS Hsnr   ON {att}'.format (**parameters))
    cursor.execute ('DROP INDEX IF EXISTS Anfadr ON {att}'.format (**parameters))
    cursor.execute ('DROP INDEX IF EXISTS Endadr ON {att}'.format (**parameters))

    cursor.execute ('DROP INDEX IF EXISTS HsAdr  ON {att}'.format (**parameters))


def step01(dba, parameters):
    """Copy tables to new database

    Copy the (28 * 2) tables to 2 tables in a new database.  Do *not* copy
    versions and patristic manuscripts.  Create indices and some views.

    """

    cursor = dba.cursor()

    # Eventually create the database and table
    cursor.execute ('DROP DATABASE IF EXISTS {target_db}'.format (**parameters))
    cursor.execute ('CREATE DATABASE IF NOT EXISTS {target_db}'.format (**parameters))
    # drop_indices (cursor)

    cursor.execute ('CREATE OR REPLACE TABLE {att} '    .format (**parameters) + db.CREATE_TABLE_ATT)
    cursor.execute ('CREATE OR REPLACE TABLE {lac} '    .format (**parameters) + db.CREATE_TABLE_LAC)
    cursor.execute ('CREATE OR REPLACE TABLE {attlac} ' .format (**parameters) + db.CREATE_TABLE_ATT)
    cursor.execute ('CREATE OR REPLACE TABLE {vp} '     .format (**parameters) + db.CREATE_TABLE_VP)
    cursor.execute ('CREATE OR REPLACE TABLE {rdg} '    .format (**parameters) + db.CREATE_TABLE_RDG)
    cursor.execute ('CREATE OR REPLACE TABLE {witn} '   .format (**parameters) + db.CREATE_TABLE_WITN)
    cursor.execute ('CREATE OR REPLACE TABLE {listval} '.format (**parameters) + db.CREATE_TABLE_MSLISTVAL)
    cursor.execute ('CREATE OR REPLACE TABLE {vg} '     .format (**parameters) + db.CREATE_TABLE_VG)

    cursor.execute ('SHOW COLUMNS IN {att}'.format (**parameters))
    target_columns_att = set ([row[0].lower() for row in cursor.fetchall()])
    cursor.execute ('SHOW COLUMNS IN {lac}'.format (**parameters))
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
        parameters['t'] = parameters['lac'] if is_lac_table else parameters['att']
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
    FROM {att}
    """, parameters)

    execute (cursor, """
    CREATE OR REPLACE VIEW {target_db}.NestedPassages AS
    SELECT a.anfadr AS ianfadr, a.endadr AS iendadr, b.anfadr AS oanfadr, b.endadr AS oendadr
    FROM {target_db}.Passages a
    JOIN {target_db}.Passages b
    WHERE a.anfadr >= b.anfadr AND a.endadr <= b.endadr AND
      NOT (a.anfadr = b.anfadr AND a.endadr = b.endadr)
    ORDER BY a.anfadr, a.endadr DESC
    """, parameters)

    dba.commit()


def step01b (dba, parameters):
    """Delete Versions

    No need to delete translations because we didn't copy them in the first
    place.

    """


def step01c (dba, parameters):
    """ Fix data entry errors.

    Fix a bogus hsnr.

    These errors should be fixed in the original database.

    """

    message (1, "Step  1c: Data entry fixes ...")
    cursor = dba.cursor()

    fix (cursor, "Wrong hs", """
    SELECT DISTINCT hs, hsnr, kapanf
    FROM {att}
    WHERE hs = 'L156s1'
    """, """
    UPDATE {att}
    SET hs = 'L156s',
        suffix2 = 's'
    WHERE hs = 'L156s1'
    """, parameters)

    fix (cursor, "Wrong hsnr", """
    SELECT DISTINCT hs, hsnr, kapanf
    FROM {att}
    WHERE hs REGEXP 'L1188s2.*' AND hsnr = 411881
    """, """
    UPDATE {att}
    SET hsnr = 411882
    WHERE hs REGEXP 'L1188s2.*'
    """, parameters)

    # Some fields contain 'N' (only in chapter 5)
    # A typo for NULL? NULL will be replaced with '' later.
    for parameters['col'] in N_FIELDS:
        fix (cursor, "{col} = N".format (**parameters), """
        SELECT hs, anfadr, labez, labezsuf, lesart, {col}
        FROM {att}
        WHERE {col} IN ('N', 'NULL')
        LIMIT 10
        """, """
        UPDATE {att}
        SET {col} = NULL
        WHERE {col} IN ('N', 'NULL')
        """, parameters)

    # Normalize NULL to ''
    # suffix2 sometimes contains a carriage return character
    for parameters['t'] in (parameters['att'], parameters['lac']):
        # Delete spurious '\r' characters in suffix2 field.
        execute (cursor, """
        UPDATE {t}
        SET suffix2 = REGEXP_REPLACE (suffix2, '\r', '')
        WHERE suffix2 REGEXP '\r'
        """, parameters)

        # replace NULL fields with ''
        for parameters['col'] in N_FIELDS + NULL_FIELDS:
            execute (cursor, """
            UPDATE {t}
            SET {col} = ''
            WHERE {col} IS NULL
            """, parameters)

    # Check consistency between Att and Lac tables
    fix (cursor, "Manuscript found in lac table but not in att table", """
    SELECT DISTINCT hsnr
    FROM {lac}
    WHERE hsnr NOT IN (
      SELECT DISTINCT hsnr FROM {att}
    )
    """, """
    DELETE
    FROM {lac}
    WHERE hsnr NOT IN (
      SELECT DISTINCT hsnr FROM {att}
    )
    """, parameters)

    dba.commit()


def step02 (dba, parameters):
    """Data cleanup

    Delete spurious carriage return characters in suffix2 field.  Replace NULL
    entries with empty strings.

        Korrekturen in den Acts-Tabellen: L-Notierungen nur im Feld LEKT, \*-
        u. C-Notierungen nur im Feld KORR.

        Gelegentlich steht an Stellen, an denen mehrere Lektionen desselben
        Lektionars zu verzeichnen sind, in KORR ein überflüssiges 'L' ohne
        Nummer.  Es kommt auch vor, dass L1 und L2 in KORR stehen oder
        C-Notierungen in LEKT.

    """

    message (1, "Step  2 : Cleanup korr and lekt ...")

    cursor = dba.cursor()

    execute (cursor, """
    UPDATE {att}
    SET lekt = korr, korr = ''
    WHERE korr REGEXP '^L'
    """, parameters)

    execute (cursor, """
    UPDATE {att}
    SET korr = lekt, lekt = ''
    WHERE lekt REGEXP '[C*]'
    """, parameters)

    execute (cursor, """
    UPDATE {att}
    SET korr = '*'
    WHERE korr = '' AND suffix2 REGEXP '[*]'
    """, parameters)

    execute (cursor, """
    UPDATE {att}
    SET suff = 'S'
    WHERE suff = '' AND suffix2 REGEXP 's'
    """, parameters)

    execute (cursor, """
    UPDATE {att}
    SET lekt = REGEXP_SUBSTR (suffix2, 'L[1-9]')
    WHERE lekt IN ('', 'L') AND suffix2 REGEXP 'L[1-9]'
    """, parameters)

    execute (cursor, """
    UPDATE {att}
    SET korr = REGEXP_SUBSTR (suffix2, 'C[1-9*]')
    WHERE korr IN ('', 'C') AND suffix2 REGEXP 'C[1-9*]'
    """, parameters)

    execute (cursor, """
    UPDATE {att}
    SET vl = REGEXP_SUBSTR (suffix2, 'T[1-9]')
    WHERE vl IN ('', 'T') AND suffix2 REGEXP 'T[1-9]'
    """, parameters)

    fix (cursor, "Incompatible hs and suffix2 for T reading", """
    SELECT hs, anfadr, lekt, vl, suffix2
    FROM {att}
    WHERE hs REGEXP 'T[1-9]' AND hs NOT REGEXP suffix2
    """, """
    UPDATE {att}
    SET lekt    = '',
        vl      = REGEXP_SUBSTR (hs, 'T[1-9]'),
        suffix2 = REGEXP_SUBSTR (hs, 'T[1-9]')
    WHERE hs REGEXP 'T[1-9]'
    """, parameters)

    fix (cursor, "Wrong labez", """
    SELECT labez, labezsuf, kapanf, count (*) AS anzahl FROM {att}
    WHERE labez REGEXP '.[fo]'
    GROUP BY labez, labezsuf, kapanf
    ORDER BY labez, labezsuf, kapanf
    """, """
    UPDATE {att}
    SET labez = SUBSTRING (labez, 1, 1),
        labezsuf = SUBSTRING (labez, 2, 1)
    WHERE labez REGEXP '.[fo]'
    """, parameters)

    dba.commit()

    # Debug print domain of fields
    for parameters['col'] in N_FIELDS:
        debug (cursor, "Domain of {col}".format (**parameters), """
        SELECT {col}, count (*) as Anzahl
        FROM {att}
        GROUP BY {col}
        """, parameters)


def step03 (dba, parameters):
    """Drop fields

    No need to drop fields because we didn't copy them in the first place.

    """
    pass


def step04 (dba, parameters):
    """Copy tables

    No need to copy the table because we already created it in the right place.

    """
    pass


def step05 (dba, parameters):
    """Process Duplicated Readings (T1, T2)

    Aus: prepare4cbgm_5b.py

        Wenn bei Wiederholung des Lemmatextes in Kommentarhandschriften
        Varianten entstanden sind, wird mit zw (=zweifelhaft) verzeichnet.

        20. Mai 2015.  Commentary manuscripts like 307 cannot be treated like
        lectionaries where we choose the first text.  If a T1 or T2 reading is
        found they have to be deleted.  A new zw reading is created containing
        the old readings as suffix.

        This has to be done as long as both witnesses are present.

        If the counterpart of one entry belongs to the list of lacunae the
        witness will be treated as normal witness. The T notation can be
        deleted.

    DIVINATIO: If there is only one T1 or T2 reading for that passage and
    manuscript, unset the 'T' suffix.  If there are both T1 and T2 readings, merge
    them into one 'zw' reading.

    """

    message (1, "Step  5: Processing Duplicated Readings (T1, T2) ...")

    cursor = dba.cursor()

    # T1 or T2 but not both
    # promote to normal status by stripping T[1-9] from hs
    execute (cursor, """
    UPDATE {att} u
    JOIN (
      SELECT id
      FROM {att}
      WHERE hs REGEXP 'T[1-9]'
      GROUP BY hsnr, anfadr, endadr
      HAVING COUNT (*) = 1
    ) AS t
    ON u.id = t.id
    SET hs = REGEXP_REPLACE (hs, 'T[1-9]', ''),
        vl = '',
        suffix2 = REGEXP_REPLACE (suffix2, 'T[1-9]', '')
    """, parameters)

    # T1 and T2
    # Original hand wrote both readings.
    # Group both T readings into one and set labez = 'zw'.
    execute (cursor, """
    SELECT id, labez, labezsuf, CONCAT (hsnr, anfadr, endadr) AS k
    FROM {att}
    WHERE (hsnr, anfadr, endadr) IN (
      SELECT DISTINCT hsnr, anfadr, endadr
      FROM {att}
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

            assert len (ids) > 1, "Programming error in T1, T2 processing."

            parameters['ids'] = ', '.join (ids[1:])
            execute (cursor, """
            DELETE FROM {att}
            WHERE id IN ({ids})
            """, parameters)

            parameters['id'] = ids[0]
            parameters['labezsuf'] = '/'.join (sorted (labez))
            execute (cursor, """
            UPDATE {att}
            SET labez = 'zw',
                labezsuf = '{labezsuf}',
                hs = REGEXP_REPLACE (hs, 'T[1-9]', ''),
                suffix2 = REGEXP_REPLACE (suffix2, 'T[1-9]', ''),
                vl = ''
            WHERE id = {id}
            """, parameters)

    dba.commit()


def step06 (dba, parameters):
    """Delete later hands

        Lesarten löschen, die nicht von der ersten Hand stammen.  Bei mehreren
        Lektionslesarten gilt die L1-Lesart.  Ausnahme: Bei Selbstkorrekturen
        wird die *-Lesart gelöscht und die C*-Lesart beibehalten.

        Erweiterung vom 15.02.2013: Wenn die einzige Variante an einer Stelle
        nur von einem oder mehreren Korrektoren bezeugt ist (z.B. 26:8/17),
        gehört die Stelle nicht in die Tabelle.  Es muss also noch eine Prüfung
        stattfinden, ob nach diesem Vorgang eine Stelle noch immer eine
        variierte Stelle ist. Wenn nicht, kann der Datensatz gelöscht werden.

    """
    message (1, "Step  6 : Delete later hands ...")

    cursor = dba.cursor()

    for parameters['t'] in (parameters['att'], parameters['lac']):
        # Delete all other readings if there is a C* reading.
        for parameters['regexp'] in ('C[*]', ):
            execute (cursor, """
            DELETE FROM {t}
            WHERE (hsnr, anfadr, endadr) IN (
              SELECT hsnr, anfadr, endadr FROM (
                SELECT hsnr, anfadr, endadr
                FROM {t}
                WHERE suffix2 REGEXP '{regexp}'
              ) AS tmp
            )
            AND suffix2 NOT REGEXP '{regexp}'
            """, parameters)

        execute (cursor, """
        DELETE FROM {t}
        WHERE (lekt = 'L2' OR korr IN ('C', 'C1', 'C2', 'C3', 'A', 'K'))
          AND suffix2 NOT REGEXP 'C[*]'
        """, parameters)

        execute (cursor, """
        DELETE FROM {t}
        WHERE suffix2 REGEXP 'A|K|L2'
        """, parameters)

        dba.commit()


def step06b (dba, parameters):
    """Process Sigla

        Handschriften, die mit einem "V" für videtur gekennzeichnet sind, werden
        ebenso wie alle anderen behandelt.  Das "V" kann also getilgt werden.
        Die Eintragungen für "ursprünglich (*)" und "C*" werden ebenfalls
        gelöscht.  Schließlich auch die Zusätze zur Handschriftennummer wie
        „T1“.  Diese Eintragungen werden (bisher) einfach an die
        Handschriftenbezeichnung angehängt.

        Der Eintrag 'videtur', gekennzeichnet durch ein 'V' hinter der
        Handschriftennummer, spielt für die CBGM keine Rolle.  Ein eventuell
        vorhandenes 'V' muss getilgt werden.  Gleiches gilt für die Einträge '*'
        und 'C*'.

    """

    message (1, "Step  6b: Delete [CLTV*] from HS ...")

    cursor = dba.cursor()

    for parameters['t'] in (parameters['att'], parameters['lac']):
        for parameters['regexp'] in ('C[1-9*]?', '[*]', '[LT][1-9]', 'V'):
            # FIXME: MariaDB specific function REGEXP_REPLACE
            execute (cursor, """
            UPDATE {t}
            SET hs = REGEXP_REPLACE (hs, '(?<=[0-9s]){regexp}', '')
            WHERE hs REGEXP '(?<=[0-9s]){regexp}'
            """, parameters)
            execute (cursor, """
            UPDATE {t}
            SET suffix2 = REGEXP_REPLACE (suffix2, '{regexp}', '')
            WHERE suffix2 REGEXP '{regexp}'
            """, parameters)

    debug (cursor, "Hs with more than one hsnr", """
    SELECT hs FROM (
      SELECT DISTINCT hs, hsnr FROM {att}
    ) AS tmp
    GROUP BY hs
    HAVING count (*) > 1
    """, parameters)

    # print some debug info
    debug (cursor, "Suffix2 debug info", """
    SELECT lekt, korr, suffix2, count (*) AS anzahl
    FROM {att}
    GROUP BY lekt, korr, suffix2
    ORDER BY lekt, korr, suffix2
    """, parameters)

    # Debug hs where hs and suffix2 still mismatch
    debug (cursor, "hs and suffix2 mismatch", """
    SELECT hs, suffix2, anfadr, endadr, lesart
    FROM {att}
    WHERE hs NOT REGEXP suffix2
    ORDER BY hs, anfadr
    """, parameters)

    # execute (cursor, """
    # UPDATE {t}
    # SET hs = CONCAT (hs, suffix2)
    # WHERE hs NOT REGEXP CONCAT(suffix2, '$')
    # """, parameters)

    fix (cursor, "Hsnr with more than one hs", """
    SELECT hsnr FROM (
      SELECT DISTINCT hs, hsnr FROM {att}
    ) AS tmp
    GROUP BY hsnr
    HAVING count (*) > 1
    """, """
    UPDATE
        {att} t
    JOIN
      (SELECT min(hs) AS minhs, hsnr FROM {att} GROUP BY hsnr ORDER BY hs) AS g
    ON
      t.hsnr = g.hsnr
    SET t.hs = g.minhs
    """, parameters)

    dba.commit()


def step07 (dba, parameters):
    """zw Lesarten

        zw-Lesarten der übergeordneten Variante zuordnen, wenn ausschliesslich
        verschiedene Lesarten derselben Variante infrage kommen (z.B. zw a/ao
        oder b/bo_f).  In diesen Fällen tritt die Buchstabenkennung der
        übergeordneten Variante in labez an die Stelle von 'zw'.

    """

    message (1, "Step  7 : Fix 'zw' ...")

    cursor = dba.cursor()

    execute (cursor, "SELECT id, labezsuf FROM {att} WHERE labez = 'zw'", parameters)

    updated = 0
    for row in cursor.fetchall ():
        labezsuf = row[1]
        unique_labez_suffixes = tuple (set ([suf[0] for suf in labezsuf.split ('/')]))
        if len (unique_labez_suffixes) == 1:
            parameters['id'] = row[0]
            parameters['labez'] = unique_labez_suffixes[0]
            execute (cursor, """
            UPDATE {att}
            SET labez = %(labez)s, labezsuf = ''
            WHERE id = %(id)s
            """, parameters, 4)
            updated += 1

    dba.commit()
    message (2, "          %d zw labez updated" % updated)


def step08 (dba, parameters):
    """Delete passages without variants

    Aus: prepare4cbgm_5.py

    An diese Stelle versetzt damit sie nur einmal aufgerufen werden muß.

        Stellen löschen, an denen nur eine oder mehrere f- oder o-Lesarten vom
        A-Text abweichen. Hier gibt es also keine Variante.

        Nicht löschen, wenn an dieser variierten Stelle eine Variante 'b' - 'y'
        erscheint.

        Änderung 2014-12-16: Act 28,29/22 gehört zu einem Fehlvers.  Dort gibt
        es u.U. keine Variante neben b, sondern nur ein Orthographicum.  Wir
        suchen also nicht mehr nach einer Variante 'b' bis 'y', sondern zählen
        die Varianten.  Liefert getReadings nur 1 zurück, gibt es keine
        Varianten.

    Stellen ohne Varianten sind für die CBGM irrelevant.  Stellen mit
    ausschließlich 'z[u-z]' Lesearten ebenso.

    """

    message (1, "Step  5 : Delete passages without variants ...")

    cursor = dba.cursor()
    # We need a nested subquery to avoid MySQL limitations. See:
    # https://dev.mysql.com/doc/refman/5.7/en/subquery-restrictions.html
    execute (cursor, """
    DELETE FROM {att} WHERE (anfadr, endadr) IN (
      SELECT anfadr, endadr FROM (
        SELECT anfadr, endadr FROM {att}
        WHERE labez NOT REGEXP '^z' OR labezsuf NOT REGEXP 'f|o'
        GROUP BY anfadr, endadr, labez
        HAVING count (*) = 1
      ) AS tmp
    )
    """, parameters)
    dba.commit()


def step09 (dba, parameters):
    """Lacunae auffüllen

        Stellenbezogene Lückenliste füllen.  Parallel zum Apparat wurde eine
        systematische Lückenliste erstellt, die die Lücken aller griechischen
        Handschriften enthält.  Wir benötigen diese Information jedoch jeweils
        für die variierten Stellen.

    In Step 9 Mr. Krüger builds a lacuna table containing an entry for each
    manuscript and passage inside a lacuna.  Then, in step 10, he adds 'zz'
    readings to the Acts table for each passage inside a lacuna using the lacuna
    table of step 9.  We short-circuit the creation of the lacuna table.

    """

    message (1, "Step  9 : Create Lacunae Table ...")

    cursor = dba.cursor()

    # First clean up the lacunae table as any errors there will be multiplied by
    # this step.  Delete inner lacunae from nested lacunae.

    fix (cursor, "nested lacunae", """
    SELECT lac.id, lac.hs, lac.anfadr, lac.endadr
    FROM {lac} AS lac
    JOIN (
      SELECT MIN (a.id) as id, a.hs, a.anfadr, a.endadr
      FROM {lac} a
      JOIN {lac} b
      WHERE a.hs = b.hs AND a.anfadr <= b.anfadr AND a.endadr >= b.endadr
      GROUP BY a.hs, a.anfadr, a.endadr
      HAVING count (*) > 1
      ORDER BY hs, anfadr, endadr DESC
    ) AS t
    WHERE lac.hs = t.hs
      AND lac.anfadr >= t.anfadr
      AND lac.endadr <= t.endadr
    """, """
    DELETE lac
    FROM {lac} lac
    JOIN (
      SELECT MIN (a.id) as id, a.hs, a.anfadr, a.endadr
      FROM {lac} a
      JOIN {lac} b
      WHERE a.hs = b.hs AND a.anfadr <= b.anfadr AND a.endadr >= b.endadr
      GROUP BY a.hs, a.anfadr, a.endadr
      HAVING count (*) > 1
      ORDER BY hs, anfadr, endadr DESC
    ) AS t
    WHERE lac.hs = t.hs
      AND lac.anfadr >= t.anfadr
      AND lac.endadr <= t.endadr
      AND lac.id <> t.id
    """, parameters)

    dba.commit()

    # FIXME: Bei Text in lacuna muß der Text stehen bleiben. Allerdings dürfen
    # wir dann nicht mit zz auffüllen.

    # Delete all texts in lacunae.
    fix (cursor, "text in lacunae", """
    SELECT t.hs, t.hsnr, t.anfadr, t.endadr, lac.anfadr as lacanfadr, lac.endadr as lacendadr, t.labez, t.lemma, t.lesart
    FROM {att} t
    JOIN {lac} lac
    ON t.hs = lac.hs AND t.anfadr > lac.anfadr AND t.endadr < lac.endadr
    ORDER BY t.hsnr, t.hs, t.anfadr
    """, """
    DELETE FROM {att}
    WHERE id IN (
      SELECT id FROM (
        SELECT t.id
        FROM {att} t
        JOIN {lac} lac
        ON t.hs = lac.hs AND t.anfadr > lac.anfadr AND t.endadr < lac.endadr
      ) AS tmp
    )
    """, parameters)

    # Create a lacuna entry for each passage in a lacuna.

    message (2, "Step  9 : Add 'zz' readings for lacunae ...")

    execute (cursor, """
    INSERT INTO {att} (buch, kapanf, versanf, wortanf, kapend, versend, wortend,
                          anfadr, endadr, hs, hsnr, anfalt, endalt, labez, labezsuf,
                          lemma, lesart)
    SELECT t.buch, t.kapanf, t.versanf, t.wortanf, t.kapend, t.versend, t.wortend,
           t.anfadr, t.endadr, lac.hs, lac.hsnr, t.anfadr, t.endadr, 'zz', '',
           '', 'lac'
      FROM
        /* all passages */
        {target_db}.Passages t
      JOIN
        /* all lacunae */
        {lac} lac
      ON t.anfadr > lac.anfadr AND t.endadr < lac.endadr

    """, parameters)
    dba.commit()


def step10 (dba, parameters):
    """Create positive apparatus

        Bezeugung der a-Lesarten auffüllen (d.h. einen positiven Apparat
        herstellen).  Sie setzt sich zusammen aus allen in der 'ActsMsList' für
        das jeweilige Kapitel geführten Handschriften, die an der jeweils
        bearbeiteten Stelle noch nicht bei einer Variante oder in der
        Lückenliste stehen.

        Besondere Aufmerksamkeit ist bei den Fehlversen notwendig: Im Bereich
        der Fehlverse darf nicht einfach die a-Bezeugung aufgefüllt werden.
        Stattdessen muss, wenn die variierte Stelle zu einer umfassten Einheit
        gehört und das Feld 'base' den Inhalt 'a' hat, die neue
        Lesartenbezeichnung 'zu' eingetragen werden.  base = 'b' steht für eine
        alternative Subvariante (dem Textus receptus).

        Eine variierte Stelle ist eine umfasste Stelle, wenn comp = 'x' ist.

    Insert the lesart of hs = 'A' for each passage that is not yet in the
    table.  Lacunae are already accounted for.

    """

    message (1, "Step 10: Add 'a' readings ...")

    cursor = dba.cursor()

    execute (cursor, """
    INSERT INTO {att} (hsnr, hs, anfadr, endadr, buch, kapanf, versanf, wortanf,
                          kapend, versend, wortend, labez, labezsuf, anfalt, endalt,
                          lesart, base)
    SELECT hs.hsnr, hs.hs, a.anfadr, a.endadr, a.buch, a.kapanf, a.versanf, a.wortanf,
           a.kapend, a.versend, a.wortend, a.labez, a.labezsuf, a.anfalt, a.endalt,
           a.lesart, a.base
    FROM
      /* all passages from A */
      (SELECT * FROM {att} WHERE hs = 'A') AS a

    JOIN
      /* all manuscripts */
      (SELECT DISTINCT hs, hsnr FROM {att} WHERE hs <> 'A') AS hs

    LEFT JOIN
      /* negated join on all witnessed passages */
      {att} t

    ON t.hs = hs.hs AND t.anfadr = a.anfadr AND t.endadr = a.endadr

    WHERE t.id IS NULL

    """, parameters)
    dba.commit()

    debug (cursor, "Manuscripts with duplicated passages", """
    SELECT hs, anfadr, endadr FROM {att} GROUP BY hs, anfadr, endadr HAVING COUNT (*) > 1
    """, parameters)

    execute (cursor, """
    /* Set comp = 'x' on nested variants. */
    UPDATE {att} t
    JOIN (
      /* this subquery materializes the view: huge performance gain */
      SELECT ianfadr, iendadr FROM {target_db}.NestedPassages
    ) as n
    ON t.anfadr = n.ianfadr AND t.endadr = n.iendadr
    SET comp = 'x'
    """, parameters)

    parameters['fehlverse'] = db.FEHLVERSE
    execute (cursor, """
    UPDATE {att}
    SET labez = 'zu', lesart = ''
    WHERE comp = 'x' AND base = 'a' AND {fehlverse}
    """, parameters)

    execute (cursor, """
    UPDATE {att}
    SET lesart = 'lac'
    WHERE labez = 'zz'
    """, parameters)

    dba.commit()


def step11 (dba, parameters):
    """Create ActsMsList

        Handschriftenliste 'ActsMsList' anlegen. Die Handschrift bekommt in dem
        entsprechenden Kapitel eine 1, wenn sie dort Text enthält. Mit anderen
        Worten: Sie bekommt eine 0, wenn das ganze Kapitel fehlt. Es wird hier
        auf die systematische Lückenliste zurückgegriffen. Kapitel, die keine
        echte Variante enthalten, müssen ebenfalls eine 0 erhalten.

        Die Handschriftenliste darf erst NACH dem Auffüllen der a-Bezeugung
        gerechnet werden, daher gehört das Skript hier an den Schluss der
        Vorbereitungen!

    """

    message (1, "Step 11 : Create ActsMsList ...")

    cursor = dba.cursor ()
    dba.commit ()


def step20 (dba, parameters):
    """Kopiert Daten in die erzeugten Tabellen.

    Aus: PreCo/PreCoActs/Acts_Base.pl

        Die VP-Tabellen (Variant Passages) enthalten alle variierten Stellen.

        Die Rdg-Tabellen (Readings) enthalten die Lesarten.  Eine variierte
        Stelle hat mindestens zwei Lesarten.  Eine Lesart hat eine eindeutige
        Adresse, eine Lesartenbezeichnung (Labez), das Suffix einer
        Lesartenbezeichnung (Labezsuf) und natürlich den Text der Lesart selbst.
        Das Suffix kennzeichnet z.B. eine Fehlerlesart oder ein Orthographicum.

        Die Witn-Tabellen ordnen die einzelnen Handschriften jeweils den
        Lesarten zu.

        In den WitGen-Tabellen werden jetzt noch die genealogischen
        Informationen hinzugefügt.  D.h. für eine Lesart wird eingetragen, ob
        sie als ursprünglich gilt (*) oder ob sie aus einer anderen Lesart
        entstanden ist.  Mit einem Fragezeichen kann man diese Entscheidung auch
        offen lassen.  In der Spalte Labneu kann festgehalten werden, ob eine
        Lesart aus verschiedenen Quellen gleich entstanden ist.

    """

    message (1, "Step 20 : Fill PreCo Tables ...")

    cursor = dba.cursor ()

    execute (cursor, """
    TRUNCATE {vp}
    """, parameters)

    execute (cursor, """
    INSERT INTO {vp} (anfadr, endadr)
    SELECT DISTINCT anfadr, endadr
    FROM {att}
    """, parameters)

    dba.commit ()

    execute (cursor, """
    TRUNCATE {rdg}
    """, parameters)

    execute (cursor, """
    INSERT INTO {rdg} (anfadr, endadr, labez, labezsuf, lesart)
    SELECT DISTINCT anfadr, endadr, labez, labezsuf, lesart
    FROM {att}
    WHERE labez NOT REGEXP '^z[u-z]'
    """, parameters)

    dba.commit ()

    # delete all readings with labezsuf if there is an equivalent reading
    # without labezsuf

    execute (cursor, """
    DELETE FROM {rdg}
    WHERE (anfadr, endadr, labez) IN (
      SELECT anfadr, endadr, labez FROM (
        SELECT DISTINCT anfadr, endadr, labez
        FROM {rdg}
        WHERE labezsuf = ''
      ) AS tmp
    ) AND labezsuf <> ''
    """, parameters)

    dba.commit ()

    # FIXME: why are there multiple 'a' readings for some passages?
    #
    # According to Münster these are legitimate entries.  They still have to
    # figure out how to handle these.  For the time being we keep only one
    # reading and delete the rest.
    #
    # Delete duplicate readings.
    # Examples:
    # | anfadr   | endadr   | labez | labezsuf | lesart
    # +----------+----------+-------+----------+-------------
    # | 52333010 | 52333010 | a     |          | καισαρειαν
    # | 52333010 | 52333010 | a     |          | om
    # | 52621002 | 52621002 | a     |          | ενεκα
    # | 52621002 | 52621002 | a     |          | om
    # | 52816006 | 52816006 | a     |          | εισηλθομεν
    # | 52816006 | 52816006 | a     |          | εισηλ[θομεν]
    # | 52816006 | 52816006 | a     |          | εισ̣[ηλθομεν]

    execute (cursor, """
    DELETE d
    FROM {rdg} d
    JOIN (
      SELECT id, anfadr, endadr, labez FROM (
        /* min makes sure we keep the entry with the lowest id */
        SELECT min (id) as id, anfadr, endadr, labez
        FROM {rdg}
        GROUP BY anfadr, endadr, labez
        HAVING count (*) > 1
      ) AS tmp
    ) t
    ON d.anfadr = t.anfadr
      AND d.endadr = t.endadr
      AND d.labez = t.labez
      AND d.id <> t.id
    """, parameters)

    dba.commit ()

    # FIXME: the witn table is superfluous as it contains the same rows as att

    execute (cursor, """
    TRUNCATE {witn}
    """, parameters)

    execute (cursor, """
    INSERT INTO {witn} (anfadr, endadr, labez, labezsuf, hsnr, hs)
    SELECT DISTINCT anfadr, endadr, labez, labezsuf, hsnr, hs
    FROM {att}
    """, parameters)

    dba.commit ()


def step21 (dba, parameters):
    """Errechnet den Mehrheitstext

    Aus: PreCo/PreCoActs/ActsMT2.pl

        Update der Tabellen, byzantinische Handschriften werden markiert und
        gezählt.

        Im Laufe der Textgeschichte hat sich eine Textform durchgesetzt, der
        sogenannte Mehrheitstext, der auch Byzantinischer Text genannt wird.
        Diese Textform wird exemplarisch durch die sieben Handschriften 1, 18,
        35, 330, 398, 424 und 1241 repräsentiert.  Für jede variierte Stelle
        wird nun gezählt und festgehalten, wieviele dieser sieben Handschriften
        bei einer Lesart vertreten sind.  Eine Lesart gilt als Mehrheitslesart,
        wenn sie

        a) von mindestens sechs der oben genannten repräsentativen Handschriften
           bezeugt wird und höchstens eine Handschrift abweicht, oder

        b) von fünf Repräsentanten bezeugt wird und zwei mit unterschiedlichen
           Lesarten abweichen.

    Diese Funktion

    - schreibt die Anzahl der Byz-Hss., die an einer variierten Stelle einer
      Variante eindeutig zugeordnet werden können, in ein Feld bzdef in vp

    - schreibt die Anzahl der Byz-Repräsentanten in das Feld bz in rdg

    - ermittelt an jeder variierten Stelle die Byz-Lesart und markiert sie mit
      byz = 'B' in der Rdg-Tabelle, wenn sie nach den og. Kriterien bestimmt
      werden kann.

    - Fügt schließlich ein Manuskript 'MT' mit dem errechneten Mehrheitstext in
      die Att-Tabelle ein.

    Felder:

    bzdef in vp
      Anzahl der Byz-Hss, die an der jeweiligen variierten Stelle eindeutig
      einer Lesart zugeordnet werden können.  vp enthält genau eine Zeile pro
      variierter Stelle.

    bzdef in rdg
      Anzahl der Byz-Hss, die an der jeweiligen variierten Stelle eindeutig
      einer Lesart zugeordnet werden können.  rdg kann mehrere Zeilen pro
      variierter Stelle enthalten, mit jeweils unterschiedlichen Lesarten.

    bz in rdg
      Anzahl der Byz-Hss, die die jeweilige Variante (= variierte Stelle *
      Lesart) bezeugen.

    byz in rdg
      Markiert die nach unseren Regeln identifizierte Mehrheitslesart.

    """

    message (1, "Step 21 : Find Byzantine Text ...")

    cursor = dba.cursor ()

    parameters['byzlist'] = db.BYZ_HSNR

    # FIXME: we don't really need this table
    execute (cursor, """
    UPDATE {vp} AS u
    JOIN (
      SELECT anfadr, endadr, count (*) as anzahl
      FROM {witn}
      WHERE hsnr IN {byzlist}
        AND labez NOT REGEXP '^z[u-z]'
      GROUP BY anfadr, endadr
    ) AS s
    ON (u.anfadr, u.endadr) = (s.anfadr, s.endadr)
    SET u.bzdef = s.anzahl
    """, parameters)

    dba.commit ()

    execute (cursor, """
    UPDATE {rdg} AS u
    JOIN (
      SELECT anfadr, endadr, count (*) as anzahl
      FROM {witn}
      WHERE hsnr IN {byzlist}
        AND labez NOT REGEXP '^z[u-z]'
      GROUP BY anfadr, endadr
    ) AS s
    ON (u.anfadr, u.endadr) = (s.anfadr, s.endadr)
    SET u.bzdef = s.anzahl
    """, parameters)

    execute (cursor, """
    UPDATE {rdg} AS u
    JOIN (
      SELECT anfadr, endadr, labez, count (*) as anzahl
      FROM {witn}
      WHERE hsnr IN {byzlist}
        AND labez NOT REGEXP '^z[u-z]'
      GROUP BY anfadr, endadr, labez
    ) AS s
    ON (u.anfadr, u.endadr, u.labez) = (s.anfadr, s.endadr, s.labez)
    SET u.bz = s.anzahl
    """, parameters)

    dba.commit ()

    # debug info

    debug (cursor, "Byzantine Variant Passages", """
    SELECT bzdef, count (*) AS anzahl FROM {vp} GROUP BY bzdef
    """, parameters)

    debug (cursor, "Byzantine Readings", """
    SELECT bz, count (*) AS anzahl FROM {rdg} GROUP BY bz
    """, parameters)

    # mindestens 6
    execute (cursor, """
    UPDATE {rdg}
    SET byz = 'B'
    WHERE bzdef = 7 AND bz >= 6
    """, parameters)

    # 5 und 2 unterschiedliche
    execute (cursor, """
    UPDATE {rdg}
    SET byz = 'B'
    WHERE (anfadr, endadr, bz) IN (
      SELECT anfadr, endadr, 5 FROM (
        SELECT anfadr, endadr
        FROM {rdg}
        WHERE bzdef = 7 AND bz IN (5, 1)
        GROUP BY anfadr, endadr
        HAVING count (*) = 3
      ) AS t
    )
    """, parameters)

    dba.commit ()

    # build the fake manuscript 'MT'

    execute (cursor, """
    DELETE FROM {att} WHERE hs = 'MT'
    """, parameters)

    execute (cursor, """
    INSERT INTO {att} (hsnr, hs, anfadr, endadr, buch, kapanf, versanf, wortanf,
                       kapend, versend, wortend, labez, labezsuf, lesart)
    SELECT 1, 'MT', a.anfadr, a.endadr, a.buch, a.kapanf, a.versanf, a.wortanf,
           a.kapend, a.versend, a.wortend, r.labez, r.labezsuf, r.lesart
    FROM {target_db}.Passages a
    JOIN {rdg} r
    ON (a.anfadr, a.endadr, 'B') = (r.anfadr, r.endadr, r.byz)
    """, parameters)

    execute (cursor, """
    INSERT INTO {att} (hsnr, hs, anfadr, endadr, buch, kapanf, versanf, wortanf,
                       kapend, versend, wortend, labez, labezsuf, lesart)
    SELECT 1, 'MT', a.anfadr, a.endadr, a.buch, a.kapanf, a.versanf, a.wortanf,
           a.kapend, a.versend, a.wortend, 'zz', '', 'lac'
    FROM {target_db}.Passages a
    LEFT JOIN {rdg} r
    ON (a.anfadr, a.endadr, 'B') = (r.anfadr, r.endadr, r.byz)
    WHERE r.byz IS NULL
    """, parameters)

    dba.commit()


def step22 (dba, parameters):
    """Füllt die MsListVal Tabelle.

    Aus: PreCo/PreCoActs/ActsMsListVal.pl

        Es wurden bereits die byzantinischen Lesarten markiert.  In diesem
        Arbeitsschritt wird für jede Handschrift die Übereinstimmung mit dem
        byzantinischen Mehrheitstext ermittelt.  Dies geschieht sowohl auf der
        Basis der ganzen Apostelgeschichte als auch für jedes einzelne Kapitel.

    sumtxt
      Count of passages in which the ms has any text.

    uemt
      Count of passages in which the ms has the byzantine text.

    summt
      Count of passages in which we could establish a byzantine text.

    """

    message (1, "Step 22 : Filling MsListVal ...")

    cursor = dba.cursor ()

    # fill with hs, hsnr, chapter

    execute (cursor, """
    TRUNCATE {listval}
    """, parameters)

    execute (cursor, """
    INSERT INTO {listval} (hs, hsnr, chapter)
    SELECT DISTINCT hs, hsnr, 0
    FROM {att}
    WHERE labez NOT REGEXP '^z[u-z]'
    """, parameters)

    execute (cursor, """
    INSERT INTO {listval} (hs, hsnr, chapter)
    SELECT DISTINCT hs, hsnr, kapanf
    FROM {att}
    WHERE labez NOT REGEXP '^z[u-z]'
    """, parameters)

    dba.commit ()

    # sumtxt

    execute (cursor, """
    UPDATE {listval} u
    JOIN (
      SELECT hsnr, count (*) as sumtxt
      FROM {att}
      WHERE labez NOT REGEXP '^z[u-z]'
      GROUP BY hsnr
    ) AS t
    ON (u.hsnr, u.chapter) = (t.hsnr, 0)
    SET u.sumtxt = t.sumtxt
    """, parameters)

    execute (cursor, """
    UPDATE {listval} u
    JOIN (
      SELECT hsnr, kapanf, count (*) as sumtxt
      FROM {att}
      WHERE labez NOT REGEXP '^z[u-z]'
      GROUP BY hsnr, kapanf
    ) AS t
    ON (u.hsnr, u.chapter) = (t.hsnr, t.kapanf)
    SET u.sumtxt = t.sumtxt
    """, parameters)

    # summt

    execute (cursor, """
    UPDATE {listval} u
    JOIN (
      SELECT hsnr, count (*) as summt
      FROM {att} a
      JOIN {rdg} r
      ON (a.anfadr, a.endadr, a.labez) = (r.anfadr, r.endadr, r.labez)
      WHERE (a.anfadr, a.endadr) IN (
        SELECT anfadr, endadr
        FROM {rdg}
        WHERE byz = 'B'
      )
      GROUP BY a.hsnr
    ) AS t
    ON (u.hsnr, u.chapter) = (t.hsnr, 0)
    SET u.summt = t.summt
    """, parameters)

    execute (cursor, """
    UPDATE {listval} u
    JOIN (
      SELECT hsnr, kapanf, count (*) as summt
      FROM {att} a
      JOIN {rdg} r
      ON (a.anfadr, a.endadr, a.labez) = (r.anfadr, r.endadr, r.labez)
      WHERE (a.anfadr, a.endadr) IN (
        SELECT anfadr, endadr
        FROM {rdg}
        WHERE byz = 'B'
      )
      GROUP BY a.hsnr, a.kapanf
    ) AS t
    ON (u.hsnr, u.chapter) = (t.hsnr, t.kapanf)
    SET u.summt = t.summt
    """, parameters)

    # uemt

    execute (cursor, """
    UPDATE {listval} u
    JOIN (
      SELECT hsnr, count (*) as uemt
      FROM {att} a
      JOIN {rdg} r
      ON (a.anfadr, a.endadr, a.labez, 'B') = (r.anfadr, r.endadr, r.labez, r.byz)
      GROUP BY a.hsnr
    ) AS t
    ON (u.hsnr, u.chapter) = (t.hsnr, 0)
    SET u.uemt = t.uemt
    """, parameters)

    execute (cursor, """
    UPDATE {listval} u
    JOIN (
      SELECT hsnr, kapanf, count (*) as uemt
      FROM {att} a
      JOIN {rdg} r
      ON (a.anfadr, a.endadr, a.labez, 'B') = (r.anfadr, r.endadr, r.labez, r.byz)
      GROUP BY a.hsnr, a.kapanf
    ) AS t
    ON (u.hsnr, u.chapter) = (t.hsnr, t.kapanf)
    SET u.uemt = t.uemt
    """, parameters)

    # qmt

    execute (cursor, """
    UPDATE {listval}
    SET qmt = (uemt * 100.0) / sumtxt
    WHERE sumtxt > 0
    """, parameters)

    dba.commit ()


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

    dba = db.DBA (args.profile)
    # Make MySQL more compatible with other SQL databases
    dba.cursor ().execute ("SET sql_mode='ANSI'")

    args.start_time = datetime.datetime.now ()
    tools.args = args
    parameters = tools.init_parameters (DEFAULTS)

    try:
        for step in range(args.range[0], args.range[1] + 1):
            if step == 1:
                step01 (dba, parameters)
                step01b (dba, parameters)
                step01c (dba, parameters)
                continue
            if step == 2:
                step02 (dba, parameters)
                continue
            if step == 3:
                step03 (dba, parameters)
                continue
            if step == 4:
                step04 (dba, parameters)
                continue
            if step == 5:
                step05 (dba, parameters)
                continue
            if step == 6:
                step06 (dba, parameters)
                step06b (dba, parameters)
                continue
            if step == 7:
                step07 (dba, parameters)
                if args.verbose >= 1:
                    tools.print_stats(dba, parameters)
                continue
            if step == 8:
                step08 (dba, parameters)
                continue
            if step == 9:
                step09 (dba, parameters)
                if args.verbose >= 1:
                    tools.print_stats(dba, parameters)
                continue
            if step == 10:
                step10 (dba, parameters)
                if args.verbose >= 1:
                    tools.print_stats(dba, parameters)
                continue
            if step == 11:
                step11 (dba, parameters)
                continue
            if step == 20:
                step20 (dba, parameters)
                continue
            if step == 21:
                step21 (dba, parameters)
                continue
            if step == 22:
                step22 (dba, parameters)
                continue

    except KeyboardInterrupt:
        dba.rollback()

    dba.close()

    message (1, "          Done")
