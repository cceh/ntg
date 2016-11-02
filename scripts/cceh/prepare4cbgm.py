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

from __future__ import print_function
from __future__ import unicode_literals

import argparse
import collections
import datetime
import itertools
import logging
import math
import operator
import os
import re
import sys

import networkx as nx
import numpy as np
import six
import sqlalchemy

sys.path.append (os.path.dirname (os.path.abspath (__file__)) + "/../..")

from ntg_common import db
from ntg_common import tools
from ntg_common import plot
from ntg_common.db import execute, executemany, executemany_raw, debug, fix
from ntg_common.tools import message
from ntg_common.config import args

PLOT = 0 # plot pretty pictures

N_FIELDS = 'base comp comp1 komm kontrolle korr lekt over over1 suff suffix2 vid vl'.split ()
""" Field to look for 'N' and NULL """

NULL_FIELDS = 'lemma lesart'.split ()
""" Fields to look for NULL """

MAX_LABEZ = ord ('z') - ord ('a') + 1
""" Max. no. of different labez """

DB_INSERT_CHUNK_SIZE = 100000

def ord_labez (labez):
    return ord (labez[0]) - 96


def ord_labez_locstem (labez):
    if labez == '':
        return 0
    if labez == '*':
        return 0
    if labez == '?':
        return 1
    return 1 << ord (labez[0]) - 96


def step01 (dba, dbb, parameters):
    """Copy tables to new database

    Copy the (28 * 2) mysql tables to 2 tables in a new postgres database.  Do
    *not* copy versions and patristic manuscripts.  Create indices and some
    views.

    """

    message (1, "Step  1 : Creating tables ...")

    db.Base.metadata.drop_all (dbb.engine)
    db.Base.metadata.create_all (dbb.engine)
    with dbb.engine.begin () as dest:
        db.create_functions (dest, parameters)

    message (1, "Step  1 : Copying tables ...")

    att_model = sqlalchemy.Table (parameters['att'], db.Base.metadata)
    lac_model = sqlalchemy.Table (parameters['lac'], db.Base.metadata)

    target_columns_att = set ([c.name.lower () for c in att_model.columns])
    target_columns_lac = set ([c.name.lower () for c in lac_model.columns])

    # these columns get special treatment
    target_columns_att -= set (('id', 'created'))
    target_columns_lac -= set (('id', 'created'))

    dba_meta = sqlalchemy.schema.MetaData (bind = dba.engine)
    dba_meta.reflect ()

    with dba.engine.begin () as src:
        with dbb.engine.begin () as dest:

            # Get a list of tables (there are two tables per chapter)
            table_mask = re.compile (parameters['table_mask'])
            for table_name in sorted (dba_meta.tables.keys ()):
                if not table_mask.match (table_name):
                    continue

                is_lac_table = table_name.endswith ('lac')

                parameters['source_table'] = table_name

                parameters['t'] = parameters['lac'] if is_lac_table else parameters['att']
                target_columns = target_columns_lac if is_lac_table else target_columns_att

                source_model = sqlalchemy.Table (parameters['source_table'], dba_meta, autoload = True)
                source_columns = [column.name.lower() for column in source_model.columns]
                common_columns = [column for column in source_columns if column in target_columns]

                parameters['fields']              = ', '.join (common_columns)
                parameters['field_placeholders']  = ', '.join (['%s'] * len (common_columns))
                parameters['created'] = datetime.date.today().strftime ("%Y-%m-%d")

                message (2, 'Step  1 : Copying table {source_table}'.format (**parameters))

                rows = execute (src, """
                SELECT {fields}, anfadr, endadr + 1
                FROM {source_table}
                WHERE hsnr < 500000 AND endadr >= anfadr
                """, parameters)

                executemany_raw (dest, """
                INSERT INTO {t} ({fields}, irange, created)
                VALUES ({field_placeholders}, int4range (%s, %s), '{created}')
                ON CONFLICT DO NOTHING
                """, parameters, [r for r in rows])


def create_ms_pass_tables (dba, parameters):
    """ Create the Manuscripts, Chapters, Passages and Nested Passages tables. """

    db.Base2.metadata.drop_all   (dba.engine)
    db.Base2.metadata.create_all (dba.engine)

    with dba.engine.begin () as conn:

        # The Manuscripts Table

        # ms_id = 1
        execute (conn, """
        INSERT INTO {ms} (hs, hsnr) VALUES ('A', 0)
        """, parameters)

        # ms_id = 2
        execute (conn, """
        INSERT INTO {ms} (hs, hsnr) VALUES ('MT', 1)
        """, parameters)

        # ms_id = 3, ...
        execute (conn, """
        INSERT INTO {ms} (hs, hsnr)
        SELECT DISTINCT hs, hsnr
        FROM {att}
        WHERE hsnr >= 100000
        ORDER BY hsnr
        """, parameters)

        # The Chapters Table

        execute (conn, """
        INSERT INTO {chap} (ms_id, hs, hsnr, chapter)
        SELECT ms.id, ms.hs, ms.hsnr, c.chapter
        FROM {ms} ms
        CROSS JOIN (
          SELECT 0 AS chapter
          UNION
          SELECT DISTINCT kapanf AS chapter
          FROM {att}
        ) AS c
        """, parameters)

        # The Passages Table

        execute (conn, """
        DROP INDEX IF EXISTS {pass}_irange_gist_idx
        """, parameters)

        execute (conn, """
        INSERT INTO {pass} (buch, kapanf, versanf, wortanf, kapend, versend, wortend, anfadr, endadr, irange)
        SELECT DISTINCT buch, kapanf, versanf, wortanf, kapend, versend, wortend,
                        anfadr, endadr, int4range (anfadr, endadr + 1)
        FROM {att}
        ORDER BY anfadr, endadr DESC
        """, parameters)

        execute (conn, """
        CREATE INDEX {pass}_irange_gist_idx ON {pass} USING GIST (irange)
        """, parameters)

        # Mark Nested Passages

        execute (conn, """
        UPDATE {pass} p
        SET comp = True
        WHERE EXISTS (
          SELECT irange FROM {pass} p2
          WHERE p.irange && p2.irange AND p.id <> p2.id
        )
        """, parameters)

        # Fehlverse

        parameters['fehlverse'] = db.FEHLVERSE
        execute (conn, """
        UPDATE {pass} p
        SET fehlvers = True
        WHERE {fehlverse}
        """, parameters)


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

    with dba.engine.begin () as conn:

        fix (conn, "Wrong hs", """
        SELECT DISTINCT hs, hsnr, kapanf
        FROM {att}
        WHERE hs = 'L156s1'
        """, """
        UPDATE {att}
        SET hs = 'L156s',
            suffix2 = 's'
        WHERE hs = 'L156s1'
        """, parameters)

        fix (conn, "Wrong hsnr", """
        SELECT DISTINCT hs, hsnr, kapanf
        FROM {att}
        WHERE hs ~ 'L1188s2.*' AND hsnr = 411881
        """, """
        UPDATE {att}
        SET hsnr = 411882
        WHERE hs ~ 'L1188s2.*'
        """, parameters)

        fix (conn, "Attestation of A != 'a'", """
        SELECT hs, labez, labezsuf, anfadr, endadr
        FROM {att}
        WHERE hs = 'A' AND labez ~ '^[b-y]'
        """, """
        UPDATE {att}
        SET labez = 'a'
        WHERE (hs, anfadr, endadr) = ('A', 50240012, 50240018)
        """, parameters)

        # Passages not in A
        fix (conn, "Passages not in A", """
        SELECT DISTINCT anfadr, endadr
        FROM {att}
        WHERE (anfadr, endadr) NOT IN (
          SELECT anfadr, endadr
          FROM {att}
          WHERE hs = 'A'
        )
        """, """
        INSERT INTO {att} (buch, kapanf, versanf, wortanf, kapend, versend, wortend, hsnr, hs, anfadr, endadr, labez, irange)
        VALUES (5, 15, 28, 17, 15, 28, 17, 0, 'A', 51528017, 51528017, 'zu', int4range (51528017, 51528017))
        """, parameters)

        # Alle Fehlverse in A mit labez 'zu'?
        parameters['fehlverse'] = db.FEHLVERSE
        fix (conn, "Fehlverse in A with labez <> 'zu'", """
        SELECT anfadr, endadr, labez
        FROM {att}
        WHERE {fehlverse} AND hs = 'A' AND labez <> 'zu'
        """, "", parameters)

        # Some labez fields end with spaces
        fix (conn, "labez with spaces", """
        SELECT labez
        FROM {att}
        WHERE labez ~ ' '
        """, """
        UPDATE {att}
        SET labez = REPLACE (labez, ' ', '')
        WHERE labez ~ ' '
        """, parameters)

        # Some fields contain 'N' (only in chapter 5)
        # A typo for NULL? NULL will be replaced with '' later.
        for col in N_FIELDS:
            fix (conn, "{col} = N".format (col = col), """
            SELECT hs, anfadr, labez, labezsuf, lesart, {col}
            FROM {att}
            WHERE {col} IN ('N', 'NULL')
            LIMIT 10
            """, """
            UPDATE {att}
            SET {col} = NULL
            WHERE {col} IN ('N', 'NULL')
            """, dict (parameters, col = col))

        # Normalize NULL to ''
        # suffix2 sometimes contains a carriage return character
        for t in (parameters['att'], parameters['lac']):
            # Delete spurious '\r' characters in suffix2 field.
            execute (conn, """
            UPDATE {t}
            SET suffix2 = REGEXP_REPLACE (suffix2, '\r', '')
            WHERE suffix2 ~ '\r'
            """, dict (parameters, t = t))

            # replace NULL fields with ''
            for col in N_FIELDS + NULL_FIELDS:
                execute (conn, """
                UPDATE {t}
                SET {col} = ''
                WHERE {col} IS NULL
                """, dict (parameters, t = t, col = col))

        # Lac with anfadr > endadr
        fix (conn, "Lac with anfadr > endadr", """
        SELECT *
        FROM Lac
        WHERE anfadr > endadr
        """, """
        UPDATE Lac
        SET anfadr = endadr, endadr = anfadr
        WHERE anfadr > endadr
        """, parameters)

        # Fix inconsistencies in endadr between Att and Lac
        fix (conn, "Inconsistent chapter ends in Att and Lac", """
        SELECT kapanf, max (endadr) AS maxend
        FROM {att} AS a
        GROUP BY kapanf
        HAVING max (endadr) NOT IN (
          SELECT max (endadr)
          FROM {lac} GROUP
          BY kapanf
        )
        """, """
        UPDATE {lac}
        SET endadr = 50760037
        WHERE endadr = 50760036;
        UPDATE {lac}
        SET endadr = 50301004
        WHERE endadr IN (50247036, 50247042);
        UPDATE {lac}
        SET anfadr = 51201001
        WHERE anfadr = 51201002;
        """, parameters)

        # Check consistency between Att and Lac tables
        fix (conn, "Manuscript found in lac table but not in att table", """
        SELECT DISTINCT hsnr, kapanf
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

        # Set lesart 'lac' for lacunae
        execute (conn, """
        UPDATE {att}
        SET lesart = 'lac'
        WHERE labez = 'zz'
        """, parameters)


def step02 (dba, parameters):
    """Data cleanup

    Delete spurious carriage return characters in suffix2 field.  Replace NULL
    entries with empty strings.

        Korrekturen in den Acts-Tabellen: L-Notierungen nur im Feld LEKT, \\*-
        u. C-Notierungen nur im Feld KORR.

        Gelegentlich steht an Stellen, an denen mehrere Lektionen desselben
        Lektionars zu verzeichnen sind, in KORR ein überflüssiges 'L' ohne
        Nummer.  Es kommt auch vor, dass L1 und L2 in KORR stehen oder
        C-Notierungen in LEKT.

    """

    message (1, "Step  2 : Cleanup korr and lekt ...")

    with dba.engine.begin () as conn:

        execute (conn, """
        UPDATE {att}
        SET lekt = korr, korr = ''
        WHERE korr ~ '^L'
        """, parameters)

        execute (conn, """
        UPDATE {att}
        SET korr = lekt, lekt = ''
        WHERE lekt ~ '[C*]'
        """, parameters)

        execute (conn, """
        UPDATE {att}
        SET korr = '*'
        WHERE korr = '' AND suffix2 ~ '[*]'
        """, parameters)

        execute (conn, """
        UPDATE {att}
        SET suff = 'S'
        WHERE suff = '' AND suffix2 ~ 's'
        """, parameters)

        execute (conn, """
        UPDATE {att}
        SET lekt = SUBSTRING (suffix2, 'L[1-9]')
        WHERE lekt IN ('', 'L') AND suffix2 ~ 'L[1-9]'
        """, parameters)

        execute (conn, """
        UPDATE {att}
        SET korr = SUBSTRING (suffix2, 'C[1-9*]')
        WHERE korr IN ('', 'C') AND suffix2 ~ 'C[1-9*]'
        """, parameters)

        execute (conn, """
        UPDATE {att}
        SET vl = SUBSTRING (suffix2, 'T[1-9]')
        WHERE vl IN ('', 'T') AND suffix2 ~ 'T[1-9]'
        """, parameters)

        fix (conn, "Incompatible hs and suffix2 for T reading", """
        SELECT hs, anfadr, lekt, vl, suffix2
        FROM {att}
        WHERE hs ~ 'T[1-9]' AND hs !~ suffix2
        """, """
        UPDATE {att}
        SET lekt    = '',
            vl      = SUBSTRING (hs, 'T[1-9]'),
            suffix2 = SUBSTRING (hs, 'T[1-9]')
        WHERE hs ~ 'T[1-9]'
        """, parameters)

        fix (conn, "Wrong labez", """
        SELECT labez, labezsuf, kapanf, count (*) AS anzahl FROM {att}
        WHERE labez ~ '.[fo]'
        GROUP BY labez, labezsuf, kapanf
        ORDER BY labez, labezsuf, kapanf
        """, """
        UPDATE {att}
        SET labez = SUBSTRING (labez, 1, 1),
            labezsuf = SUBSTRING (labez, 2, 1)
        WHERE labez ~ '.[fo]'
        """, parameters)

        # Debug print domain of fields
        for col in N_FIELDS:
            debug (conn, "Domain of {col}".format (col = col), """
            SELECT {col}, count (*) as Anzahl
            FROM {att}
            GROUP BY {col}
            """, dict (parameters, col = col))


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

    with dba.engine.begin () as conn:

        # T1 or T2 but not both
        # promote to normal status by stripping T[1-9] from hs
        execute (conn, """
        UPDATE {att} u
        SET hs = REGEXP_REPLACE (hs, 'T[1-9]', ''),
            vl = '',
            suffix2 = REGEXP_REPLACE (suffix2, 'T[1-9]', '')
        FROM (
          SELECT hsnr, anfadr, endadr
          FROM {att}
          WHERE hs ~ 'T[1-9]'
          GROUP BY hsnr, anfadr, endadr
          HAVING COUNT (*) = 1
        ) AS t
        WHERE (u.hsnr, u.anfadr, u.endadr) = (t.hsnr, t.anfadr, t.endadr)

        """, parameters)

        # T1 and T2
        # Original hand wrote both readings.
        # Group both T readings into one and set labez = 'zw'.
        res = execute (conn, """
        SELECT id, labez, labezsuf, CONCAT (hsnr, anfadr, endadr) AS k
        FROM {att}
        WHERE (hsnr, anfadr, endadr) IN (
          SELECT DISTINCT hsnr, anfadr, endadr
          FROM {att}
          WHERE hs ~ 'T[1-9]'
        )
        ORDER BY k  /* key for itertools.groupby */
        """, parameters)

        rows = res.fetchall ()
        if len (rows):
            for k, group in itertools.groupby (rows, operator.itemgetter (3)):
                ids = []
                labez = set ()
                for row in group:
                    ids.append (six.text_type (row[0]))
                    labez.add (row[1] + ('_' + row[2] if row[2] else ''))

                assert len (ids) > 1, "Programming error in T1, T2 processing."

                execute (conn, """
                DELETE FROM {att}
                WHERE id IN ({ids})
                """, dict (parameters, ids = ', '.join (ids[1:])))

                execute (conn, """
                UPDATE {att}
                SET labez = 'zw',
                    labezsuf = '{labezsuf}',
                    hs = REGEXP_REPLACE (hs, 'T[1-9]', ''),
                    suffix2 = REGEXP_REPLACE (suffix2, 'T[1-9]', ''),
                    vl = ''
                WHERE id = {id}
                """, dict (parameters, id = ids[0], labezsuf = '/'.join (sorted (labez))))


def step06 (dba, parameters):
    """Delete later hands

    Aus: prepare4cbgm_6.py

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

    with dba.engine.begin () as conn:

        for t in (parameters['att'], parameters['lac']):
            # Delete all other readings if there is a C* reading.
            for regexp in ('C[*]', ):
                execute (conn, """
                DELETE FROM {t}
                WHERE (hsnr, anfadr, endadr) IN (
                  SELECT hsnr, anfadr, endadr FROM (
                    SELECT hsnr, anfadr, endadr
                    FROM {t}
                    WHERE suffix2 ~ '{regexp}'
                  ) AS tmp
                )
                AND suffix2 !~ '{regexp}'
                """, dict (parameters, t = t, regexp = regexp))

            execute (conn, """
            DELETE FROM {t}
            WHERE (lekt = 'L2' OR korr IN ('C', 'C1', 'C2', 'C3', 'A', 'K'))
              AND suffix2 !~ 'C[*]'
            """, dict (parameters, t = t))

            execute (conn, """
            DELETE FROM {t}
            WHERE suffix2 ~ 'A|K|L2'
            """, dict (parameters, t = t))


def step06b (dba, parameters):
    """Process Sigla

    Aus: prepare4cbgm_6b.py

        Handschriften, die mit einem "V" für videtur gekennzeichnet sind, werden
        ebenso wie alle anderen behandelt.  Das "V" kann also getilgt werden.
        Die Eintragungen für "ursprünglich (*)" und "C*" werden ebenfalls
        gelöscht.  Schließlich auch die Zusätze zur Handschriftennummer wie
        "T1".  Diese Eintragungen werden (bisher) einfach an die
        Handschriftenbezeichnung angehängt.

        Der Eintrag 'videtur', gekennzeichnet durch ein 'V' hinter der
        Handschriftennummer, spielt für die CBGM keine Rolle.  Ein eventuell
        vorhandenes 'V' muss getilgt werden.  Gleiches gilt für die Einträge '*'
        und 'C*'.

    """

    message (1, "Step  6b: Delete [CLTV*] from HS ...")

    with dba.engine.begin () as conn:

        fix (conn, "Duplicate readings", """
        SELECT hsnr, anfadr, endadr
        FROM {att}
        GROUP BY hsnr, anfadr, endadr
        HAVING count (*) > 1
        """, """
        DELETE FROM {att}
        WHERE (hs, anfadr, endadr) = ('L156s*', 50405022, 50405034) OR
              (hs, anfadr, endadr) = ('1891*V', 52716012, 52716012)
        """, parameters)

        for t in (parameters['att'], parameters['lac']):
            for regexp in ('C[1-9*]?', '[*]', '[LT][1-9]', 'V'):
                execute (conn, """
                UPDATE {t}
                SET hs = REGEXP_REPLACE (hs, '(?<=[0-9s]){regexp}', '')
                WHERE hs ~ '(?<=[0-9s]){regexp}'
                """, dict (parameters, t = t, regexp = regexp))

                execute (conn, """
                UPDATE {t}
                SET suffix2 = REGEXP_REPLACE (suffix2, '{regexp}', '')
                WHERE suffix2 ~ '{regexp}'
                """, dict (parameters, t = t, regexp = regexp))

        debug (conn, "Hs with more than one hsnr", """
        SELECT hs FROM (
          SELECT DISTINCT hs, hsnr FROM {att}
        ) AS tmp
        GROUP BY hs
        HAVING count (*) > 1
        """, parameters)

        # print some debug info
        debug (conn, "Suffix2 debug info", """
        SELECT lekt, korr, suffix2, count (*) AS anzahl
        FROM {att}
        GROUP BY lekt, korr, suffix2
        ORDER BY lekt, korr, suffix2
        """, parameters)

        # Debug hs where hs and suffix2 still mismatch
        debug (conn, "hs and suffix2 mismatch", """
        SELECT hs, suffix2, anfadr, endadr, lesart
        FROM {att}
        WHERE hs !~ suffix2
        ORDER BY hs, anfadr
        """, parameters)

        # execute (conn, """
        # UPDATE {t}
        # SET hs = CONCAT (hs, suffix2)
        # WHERE hs NOT !~ CONCAT(suffix2, '$')
        # """, parameters)

        fix (conn, "Hsnr with more than one hs", """
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


def step07 (dba, parameters):
    """zw Lesarten

    Aus: prepare4cbgm_7.py

        zw-Lesarten der übergeordneten Variante zuordnen, wenn ausschliesslich
        verschiedene Lesarten derselben Variante infrage kommen (z.B. zw a/ao
        oder b/bo_f).  In diesen Fällen tritt die Buchstabenkennung der
        übergeordneten Variante in labez an die Stelle von 'zw'.

    """

    message (1, "Step  7 : Fix 'zw' ...")

    with dba.engine.begin () as conn:

        res = execute (conn, "SELECT id, labezsuf FROM {att} WHERE labez = 'zw'", parameters)

        updated = 0
        for row in res:
            labezsuf = row[1]
            unique_labez_suffixes = tuple (set ([suf[0] for suf in labezsuf.split ('/')]))
            if len (unique_labez_suffixes) == 1:
                execute (conn, """
                UPDATE {att}
                SET labez = :labez, labezsuf = ''
                WHERE id = :id
                """, dict (parameters, id = row[0], labez = unique_labez_suffixes[0]), 4)
                updated += 1

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

    message (1, "Step  8 : Delete passages without variants ...")

    with dba.engine.begin () as conn:

        execute (conn, """
        DELETE FROM {att}
        WHERE (anfadr, endadr) IN (
          SELECT anfadr, endadr
          FROM {att}
          WHERE labez !~ '^z'
          GROUP BY anfadr, endadr
          HAVING count (*) <= 1
        )
        """, parameters)


def copy_genealogical_data (dbsrc, dbsrcvg, dbdest, parameters):
    """Copy / update genealogical data

    Aus: VGA/Att2CBGM.pl, VGA/PortCBGMInfo.pl

    """

    dbsrc_meta = sqlalchemy.schema.MetaData (bind = dbsrc.engine)
    dbsrc_meta.reflect ()
    dbsrcvg_meta = sqlalchemy.schema.MetaData (bind = dbsrcvg.engine)
    dbsrcvg_meta.reflect ()

    with dbdest.engine.begin () as dest:

        execute (dest, """
        TRUNCATE {locstemed}
        """, parameters)

        execute (dest, """
        TRUNCATE {locstemedtmp}
        """, parameters)

        with dbsrc.engine.begin () as src:

            table_mask = re.compile (r'^Acts\d\dGVZ$')
            for table_name in sorted (dbsrc_meta.tables.keys ()):
                if not table_mask.match (table_name):
                    continue
                message (1, "        : Copying table %s" % table_name)

                parameters['source_table'] = table_name

                rows = execute (src, """
                SELECT DISTINCT anfadr, endadr, labez, labez, IF (labez = 'a', '*', 'a')
                FROM {source_table}
                """, parameters)

                executemany_raw (dest, """
                INSERT INTO {locstemed} (begadr, endadr, varid, varnew, s1)
                VALUES (%s, %s, %s, %s, %s)
                """, parameters, [r for r in rows])


        with dbsrcvg.engine.begin () as src:

            table_mask = re.compile (r'^LocStemEdAct\d\d$')
            for table_name in sorted (dbsrcvg_meta.tables.keys ()):
                if not table_mask.match (table_name):
                    continue
                message (1, "        : Copying table %s" % table_name)

                parameters['source_table'] = table_name

                rows = execute (src, """
                SELECT begadr, endadr, varid, varnew, s1, s2, prs1, prs2, `check`, COALESCE (check2, ''), w
                FROM {source_table}
                """, parameters)

                executemany_raw (dest, """
                INSERT INTO {locstemedtmp} (begadr, endadr, varid, varnew, s1, s2, prs1, prs2, "check", check2, w)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, parameters, [r for r in rows])


def preprocess_genealogical_data (dba, parameters):
    """Preprocess genealogical data

    Aus: VGA/Att2CBGM.pl, VGA/PortCBGMInfo.pl

    """

    with dba.engine.begin () as conn:

        fix (conn, "Ambiguous Local Stemmata", """
        SELECT begadr, endadr, varnew
        FROM {locstemedtmp}
        GROUP BY begadr, endadr, varnew HAVING COUNT (*) > 1
        """, """
        DELETE FROM {locstemedtmp} WHERE (begadr, endadr, varnew, s1) = (51702028, 51702030, 'c2', 'b');
        DELETE FROM {locstemedtmp} WHERE (begadr, endadr, varnew, s1) = (52830006, 52830014, 'd', 'a1')
        """, parameters)

        # delete all passages which do not exist anymore
        execute (conn, """
        DELETE FROM {locstemedtmp} d
        WHERE NOT EXISTS (
          SELECT anfadr, endadr
          FROM {pass} p
          WHERE (d.begadr, d.endadr) = (p.anfadr, p.endadr)
        )
        """, parameters)

        # overwrite with changed passages
        execute (conn, """
        INSERT INTO {locstemed} (begadr, endadr, varid, varnew, s1, s2, prs1, prs2, "check", check2, w)
          SELECT begadr, endadr, varid, varnew, s1, s2, prs1, prs2, "check", check2, w
          FROM {locstemedtmp}
        ON CONFLICT DO NOTHING
        """, parameters)

    with dba.engine.begin () as conn:

        # preprocess source readings
        #
        # We want to quickly test if a reading is older than another reading.
        # We don't want to traverse the graph back to the root every time this
        # question comes up.  So we add a field to the LocStemEd table that
        # contains an array of all ancestral readings for every reading.

        res = execute (conn, """
        WITH RECURSIVE tree AS (
          SELECT begadr, endadr, varnew, ARRAY[s1::TEXT::VARCHAR] AS ancestors
          FROM {locstemed}
          WHERE s1 IN ('*', '?') AND varnew !~ '^z'
        UNION
          SELECT l.begadr, l.endadr, l.varnew,
            CASE WHEN l.s1 = t.varnew THEN l.s1 || t.ancestors ELSE l.s2 || t.ancestors END
          FROM {locstemed} l, tree t
          WHERE l.begadr = t.begadr AND l.endadr = t.endadr
            AND (l.s1 = t.varnew OR l.s2 = t.varnew) AND l.varnew !~ '^z'
        )
        UPDATE {locstemed} l
        SET ancestors = t.ancestors
        FROM tree t
        WHERE t.begadr = l.begadr AND t.endadr = l.endadr AND t.varnew = l.varnew
        """, parameters)



Manuscript = collections.namedtuple ('Manuscript', 'hs hsnr')
Chapter    = collections.namedtuple ('Chapter',    'n start end')

class Bag (object):
    """ Holds some values for us. """

    n_mss = 0               # No. of manuscripts
    n_passages = 0          # No. of passages
    n_chapters = 0          # No. of chapters
    mss = None              # list of named tuple Manuscript
    passages = None         # list of passages
    chapters = None         # list of named tuple Chapter
    labez_matrix = None     # hs x passages matrix of labez
    affinity_matrix = None  # hs x hs matrix of similarity measure


def create_labez_table (dba, parameters):
    """Labez-Tabelle erstellen

    Aus: prepare4cbgm_9.py

        Stellenbezogene Lückenliste füllen.  Parallel zum Apparat wurde eine
        systematische Lückenliste erstellt, die die Lücken aller griechischen
        Handschriften enthält.  Wir benötigen diese Information jedoch jeweils
        für die variierten Stellen.

    Build a table containing only the information we need for CBGM, that is:
    manuscript id, passage id, and labez.

    """

    with dba.engine.begin () as conn:

        execute (conn, """
        TRUNCATE {labez}
        """, parameters)

        # First clean up the lacunae table as any errors there will be
        # multiplied by this step.
        debug (conn, "nested lacunae", """
        SELECT l.id, l.hs, l.anfadr, l.endadr
        FROM {lac} l
        JOIN {lac} l2
          ON l.hs = l2.hs AND l.anfadr != l2.anfadr AND l.endadr != l2.endadr
            AND int4range (l.anfadr, l.endadr + 1) <@ int4range (l2.anfadr, l2.endadr + 1)
        """, parameters)

        # unroll lacunae.  All lacunae get a labez of 0.
        execute (conn, """
        INSERT INTO {labez} (ms_id, pass_id, labez, labezsuf)
        SELECT DISTINCT ms.id, p.id, 0, ''
        FROM {lac} l
        JOIN {pass} p
          ON p.irange <@ int4range (l.anfadr, l.endadr + 1)
        JOIN {ms} ms
          ON ms.hsnr = l.hsnr
        """, parameters)

        # copy labez eventually overwriting lacunae
        execute (conn, """
        INSERT INTO {labez} (ms_id, pass_id, labez, labezsuf)
        SELECT ms.id as ms_id, p.id as pass_id, ord_labez (att.labez) as labez, labezsuf
          FROM {att} att
          JOIN {pass} p
            ON p.anfadr = att.anfadr AND p.endadr = att.endadr
          JOIN {ms} ms
            ON ms.hsnr = att.hsnr
        ON CONFLICT (ms_id, pass_id)
          DO UPDATE SET labez = EXCLUDED.labez, labezsuf = EXCLUDED.labezsuf
        """, parameters)

        # fill with labez 'a'
        execute (conn, """
        INSERT INTO {labez} (ms_id, pass_id, labez, labezsuf)
        SELECT ms.id, p.id, 1, ''
          FROM
            {pass} p
          CROSS JOIN
            {ms} ms
        ON CONFLICT DO NOTHING
        """, parameters)

        # finally fix the 'Fehlverse'
        #
        # As of here all Fehlverse are marked with the labez 'a' which may be
        # incorrect.  Actually all Fehlverse are correctly marked 'zu' in 'A',
        # so we might get away with doing nothing.

        # FIXME: I don't really understand what is wanted here.

        # execute (conn, """
        # UPDATE {labez} lab
        # JOIN
        #   {att} att
        # JOIN
        #   (SELECT * FROM {pass} WHERE comp AND fehlvers)
        #   AS p
        # JOIN
        #   {ms} ms
        # ON lab.ms_id = ms.id AND
        #    lab.pass_id = p.id AND
        #    p.anfadr = att.anfadr AND p.endadr = att.endadr
        #    AND ms.hsnr = att.hsnr
        #    AND att.base = 'a'
        # SET lab.labez = 0
        # """, parameters)


def create_labez_matrix (dba, parameters, val):
    """Create the labez matrix.

    Create a matrix of manuscripts x passages.  Each entry represents one
    reading: 0 = lacuna, 1 = 'a', 2 = 'b', ...

    """

    with dba.engine.begin () as conn:

        np.set_printoptions (threshold = 30)

        # get passages and chapters
        res = execute (conn, """
        SELECT anfadr, endadr, kapanf
        FROM {pass}
        ORDER BY anfadr, endadr DESC
        """, parameters)

        res = list (res)
        val.n_passages = len (res)
        val.passages   = ["%s-%s" % (x[0], x[1]) for x in res]

        # get manuscript names and numbers
        res = execute (conn, "SELECT hs, hsnr FROM {ms} ORDER BY id", parameters)
        res = list (res)
        val.n_mss = len (res)
        val.mss = list (map (Manuscript._make, res))

        # get no. of chapters
        res = execute (conn, """
        SELECT kapanf, MIN (id) - 1 AS first_id, MAX (id) AS last_id
        FROM {pass}
        GROUP BY kapanf
        ORDER BY kapanf
        """, parameters)
        val.n_chapters = res.rowcount
        val.chapters = list (map (Chapter._make, res))
        # add a virtual 'whole book' chapter
        val.chapters.insert (0, Chapter (0, val.chapters[0].start, val.chapters[-1].end))
        val.n_chapters += 1

        # DEBUG FIXME
        #val.chapters = val.chapters[:5]
        #val.n_chapters = 5

        # Matrix ms x pass

        # Initialize all manuscripts to the labez 'a'
        labez_matrix = np.broadcast_to (np.array ([1], np.uint32), (val.n_mss, val.n_passages)).copy ()

        # overwrite where actual labez is different from 'a'
        res = execute (conn, """
        SELECT ms_id - 1, pass_id - 1, labez
        FROM {labez} a
        WHERE labez != 1
        """, parameters)

        for row in res:
            labez_matrix [row[0], row[1]] = row[2]

        val.labez_matrix = labez_matrix

        print (val.n_mss)
        print (val.n_passages)
        print (val.labez_matrix.shape)


def build_byzantine_text (dba, parameters, val):
    """ Create the byzantine pseudo-text

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

    """

    with dba.engine.begin () as conn:

        # Get the labez of some typical Byzantine texts
        parameters['byzlist'] = db.BYZ_HSNR
        res = execute (conn, """
        SELECT id - 1 AS id
        FROM {ms}
        WHERE hsnr IN {byzlist}
        """, parameters)
        assert res.rowcount == 7, "The list of Byzantine texts must contain exactly 7 manuscripts."
        byz_ids = np.fromiter ((row[0] for row in res), np.int)
        print ("Byz Ids: ", byz_ids)
        byz_labez_matrix = val.labez_matrix.take (byz_ids, 0)

        # Group the labez at each passage
        byz_bincount = np.apply_along_axis (np.bincount, 0, byz_labez_matrix, minlength = 27)
        print (byz_bincount)

        # Calculate the Byzantine labez for each passage
        byz_text = np.zeros (val.n_passages, dtype = int)

        for i, bc in enumerate (byz_bincount.T):
            for j, b in enumerate (bc):
                if b >= 6:
                    # must be 7+0 or 6+1 or 6+0
                    byz_text[i] = j
                    continue
                if b == 5 and 2 not in bc[1:]: # bc[0] is lacuna
                    # must be 5+1+1 or 5+1 or 5+0
                    byz_text[i] = j
                    continue

        # print ("Byz: ", byz_text)

        # Replace the Byz text into the matrix
        val.labez_matrix[1] = byz_text

        # Write the labez table
        message (1, "        : Writing Labez table ...")
        # execute (conn, 'TRUNCATE {labez}'    , parameters)

        values = []
        # for i in range (val.n_mss):
        for j in range (val.n_passages):
            values.append ((2, j + 1, int (val.labez_matrix[1, j])))

        executemany_raw (conn, """
        INSERT INTO {labez} (ms_id, pass_id, labez)
        VALUES (%s, %s, %s)
        ON CONFLICT (ms_id, pass_id)
          DO UPDATE SET labez = EXCLUDED.labez
        """, parameters, values)

        # Boolean matrix ms x pass set where passage is defined
        val.def_matrix = np.greater (val.labez_matrix, 0)

        # debug plot the matrix
        if PLOT:
            ticks_labels_x = plot.passages_labels (val.passages)
            ticks_labels_y = plot.mss_labels (val.mss)

            plot.plt.figure (1)
            plot.heat_matrix (val.def_matrix, "Manuscript Definition Matrix",
                              ticks_labels_x, ticks_labels_y, plot.colormap_bw ())
            plot.plt.savefig ('output/mss-definition.png')
            plot.plt.close ()


def calculate_mss_similarity (dba, parameters, val):
    """Calculate mss similarity

    Aus: VGA/VG05_all3.pl

        Kapitelweise füllen auf Basis von Vergleichen einzelner
        Variantenspektren in ECM_Acts_Sp.  Vergleich von je zwei Handschriften:
        An wieviel Stellen haben sie gemeinsam Text, an wieviel Stellen stimmen
        sie überein bzw. unterscheiden sie sich (inklusive Quotient)?  Die
        Informationen werden sowohl auf Kapitel- wie auch Buchebene
        festgehalten.

    """

    with dba.engine.begin () as conn:

        # Matrix passage x labez containing bitmask of ancestral readings, '?' = 1, 'a' = 2, ...
        local_stemma_ancestor_matrix = np.zeros ((val.n_passages, MAX_LABEZ), dtype = np.uint32)
        local_stemma_parent_matrix   = np.zeros ((val.n_passages, MAX_LABEZ), dtype = np.uint32)

        # load matrix from database, load local stem for each passage
        res = execute (conn, """
        SELECT p.id - 1 as pass_id, ord_labez (varnew) as varnew, ancestors, s1, s2
        FROM {locstemed} l
        JOIN {pass} p
          ON (l.begadr, l.endadr) = (p.anfadr, p.endadr)
        WHERE ancestors != ARRAY[]::VARCHAR[]
        """, parameters)

        LocStemEd = collections.namedtuple ('LocStemEd', 'pass_id varnew ancestors s1 s2')
        rows = list (map (LocStemEd._make, res))

        for row in rows:
            local_stemma_parent_matrix[row.pass_id, row.varnew] = ord_labez_locstem (row.s1) | ord_labez_locstem (row.s2)
            for ancestor in row.ancestors:
                local_stemma_ancestor_matrix[row.pass_id, row.varnew] |= ord_labez_locstem (ancestor)

        # Matrix chapter x ms x ms with count of the passages that are defined in both mss
        val.and_matrix = np.zeros ((val.n_chapters, val.n_mss, val.n_mss), dtype = np.uint16)

        # Matrix chapter x ms x ms with count of the passages that are equal in both mss
        val.eq_matrix  = np.zeros ((val.n_chapters, val.n_mss, val.n_mss), dtype = np.uint16)

        # Matrix chapter x ms of chapter lengths
        val.chapter_len_matrix = np.zeros ((val.n_chapters, val.n_mss), dtype = np.uint16)

        # pre-genealogical coherence (outputs symmetrical matrices)
        # loop over all mss O(n_mss² * n_chapters * n_passages)

        # ch.end is the end of a range index, so it is actually one behind the
        # item we want to know
        chapter_ends = [ch.end - 1 for ch in val.chapters[1:]]

        def count_by_chapter (a):
            """Count passages by chapter.

            Count the number of passages per chapter (that satisfy a certain
            condition).  Also insert a chapter 0 for the sum over the whole
            book.  Input is an array of one boolean per passage.

            Uses chapter_ends.

            """
            cs = np.cumsum (a)   # cs[1] = a[0] + a[1], ...
            total = cs[-1]
            cs = cs[chapter_ends]
            cs = cs - np.insert (cs, 0, 0)[:-1]
            cs = np.insert (cs, 0, total)
            return cs

        message (1, "          Calculating mss similarity pre-co ...")
        for j in range (0, val.n_mss):
            labezj = val.labez_matrix[j]
            defj   = val.def_matrix[j]

            for k in range (j + 1, val.n_mss):
                labezk = val.labez_matrix[k]
                defk   = val.def_matrix[k]

                def_and  = np.logical_and (defj, defk)
                labez_eq = np.logical_and (def_and, np.equal (labezj, labezk))

                val.and_matrix[:,j,k] = val.and_matrix[:,k,j] = count_by_chapter (def_and)
                val.eq_matrix[:,j,k]  = val.eq_matrix[:,k,j]  = count_by_chapter (labez_eq)

        # calculate quotient
        with np.errstate (divide = 'ignore', invalid = 'ignore'):
            val.quotient_matrix = val.eq_matrix / val.and_matrix
            val.quotient_matrix[val.and_matrix == 0] = 0.0

        # np.fill_diagonal (val.quotient_matrix, 0.0) # remove affinity to self

        # calculate chapter lengths
        for j in range (0, val.n_mss):
            val.chapter_len_matrix[:,j] = count_by_chapter (val.def_matrix[j])

        #
        # genealogical coherence (outputs asymmetrical matrices)
        # loop over all mss O(n_mss² * n_chapters * n_passages)
        #

        message (1, "          Calculating mss similarity post-co ...")

        # For integer array indexing of the local_stemma_ancestor_matrix.
        # See: https://docs.scipy.org/doc/numpy/reference/arrays.indexing.html#advanced-indexing
        p = np.arange (0, val.n_passages)
        # m = np.arange (0, val.n_mss)

        # some time-saving preparations
        labez_mask_matrix = np.left_shift (1, val.labez_matrix)
        labez_mask_matrix[labez_mask_matrix == 1] = 0 # set lacunae to 0

        def postco (local_stemma_matrix):
            labez_ancestor_matrix = np.zeros_like (val.labez_matrix)
            for j in range (0, val.n_mss):
                labez_ancestor_matrix[j] = local_stemma_matrix[p, val.labez_matrix[j]]

            labez_matrix_source_is_unclear = np.equal (labez_ancestor_matrix, 1)
            labez_ancestor_matrix[labez_ancestor_matrix == 1] = 0 # set '?' (unclear) to 0

            local_stemmas_with_loops = set ()

            # Matrix chapter x ms x ms with count of the passages that are older in ms1 than in ms2
            ancestor_matrix = np.zeros ((val.n_chapters, val.n_mss, val.n_mss), dtype = np.uint16)

            # Matrix chapter x ms x ms with count of the passages whose relationship is unclear in ms1 and ms2
            unclear_matrix  = np.zeros ((val.n_chapters, val.n_mss, val.n_mss), dtype = np.uint16)

            for j in range (0, val.n_mss):
                for k in range (0, val.n_mss):
                    # See: VGA/VGActs_allGenTab3Ph3.pl

                    # set bit if the reading of j is ancestral to the reading of k
                    labezj_is_older = np.bitwise_and (labez_mask_matrix[j], labez_ancestor_matrix[k]) > 0
                    labezk_is_older = np.bitwise_and (labez_mask_matrix[k], labez_ancestor_matrix[j]) > 0

                    check = np.logical_and (labezj_is_older, labezk_is_older)
                    if np.any (check):
                        not_check       = np.logical_not (check)
                        labezj_is_older = np.logical_and (labezj_is_older, not_check)
                        labezk_is_older = np.logical_and (labezk_is_older, not_check)

                        local_stemmas_with_loops |= set (np.nonzero (check)[0])

                    # wenn die vergl. Hss. von einander abweichen u. eine von ihnen
                    # Q1 = '?' hat, UND KEINE VON IHNEN QUELLE DER ANDEREN IST, ist
                    # die Beziehung 'UNCLEAR'

                    unclear = np.logical_and (val.labez_matrix[j], val.labez_matrix[k])
                    unclear = np.logical_and (unclear, np.not_equal (val.labez_matrix[j], val.labez_matrix[k]))
                    unclear = np.logical_and (unclear, np.logical_or (
                        labez_matrix_source_is_unclear[j], labez_matrix_source_is_unclear[k]))
                    unclear = np.logical_and (unclear, np.logical_not (np.logical_or (labezj_is_older, labezk_is_older)))

                    # if k == 0 and np.any (labezj_is_older):
                    #    message (1, "Error labez older than A in msid %d in passages: %s"
                    #             % (j, np.nonzero (labezj_is_older)))

                    ancestor_matrix[:,j,k] = count_by_chapter (labezj_is_older)
                    unclear_matrix[:,j,k]  = count_by_chapter (unclear)

            if local_stemmas_with_loops:
                message (1, "Error: found loops in local stemmata: %s" % sorted (local_stemmas_with_loops))

            return ancestor_matrix, unclear_matrix

        val.ancestor_matrix, val.unclear_ancestor_matrix = postco (local_stemma_ancestor_matrix)
        val.parent_matrix,   val.unclear_parent_matrix   = postco (local_stemma_parent_matrix)

        # sanity tests

        # labez older than ms A

        if val.ancestor_matrix[0,:,0].any ():
            message (1, "Error: found labez older than A in msids: %s"
                     % (np.nonzero (val.ancestor_matrix[0,:,0])))

        # norel < 0
        norel_matrix = (val.and_matrix - val.eq_matrix - val.ancestor_matrix -
                        np.transpose (val.ancestor_matrix, (0, 2, 1)) - val.unclear_ancestor_matrix)
        if np.less (norel_matrix, 0).any ():
            message (1, "Error: norel < 0 in mss. %s"
                     % (np.nonzero (np.less (norel_matrix, 0))))

        # debug
        if PLOT:
            ticks_labels = plot.mss_labels (val.mss)

            for i, chapter in enumerate (val.chapters):
                plot.plt.figure (dpi = 1200) # figsize = (15, 10), dpi = 300)
                message (2, "          Plotting Affinity of Chapter %d ..." % i)
                plot.heat_matrix (val.quotient_matrix[i],
                                  "Similarity of Manuscripts - Chapter %d" % chapter.n,
                                  ticks_labels, ticks_labels, plot.colormap_affinity ())
                plot.plt.savefig ('output/affinity-%02d.png' % i) # , bbox_inches='tight')
                plot.plt.close ()

                plot.plt.figure (dpi = 1200) # figsize = (15, 10), dpi = 300)
                message (2, "          Plotting Ancestry of Chapter %d ..." % i)
                tmp = val.quotient_matrix.copy ()
                tmp[mask] = 0
                plot.heat_matrix (tmp[i],
                                  "Ancestry of Manuscripts - Chapter %d" % chapter.n,
                                  ticks_labels, ticks_labels, plot.colormap_affinity ())
                plot.plt.savefig ('output/ancestry-%02d.png' % i) # , bbox_inches='tight')
                plot.plt.close ()

        # np.fill_diagonal (val.quotient_matrix, 0.0) # remove affinity to self


        message (2, "          Updating length in Manuscripts and Chapters tables ...")

        values_mss = []
        values_chapters = []

        for i, ms in enumerate (val.mss):
            for j, chapter in enumerate (val.chapters):
                length = int (np.sum (val.def_matrix[i, chapter.start:chapter.end]))
                values_chapters.append ( { 'ms_id': i + 1, 'chapter': j, 'length': length } )
                if j == 0:
                    values_mss.append ( { 'ms_id': i + 1, 'length': length } )

        executemany (conn, """
        UPDATE {ms}
        SET length = :length
        WHERE id = :ms_id
        """, parameters, values_mss)

        executemany (conn, """
        UPDATE {chap}
        SET length = :length
        WHERE ms_id = :ms_id AND chapter = :chapter
        """, parameters, values_chapters)


        message (2, "          Filling Affinity table ...")
        execute (conn, "TRUNCATE {aff}", parameters)

        for i, chapter in enumerate (val.chapters):
            values = []
            for j in range (0, val.n_mss):
                for k in range (0, val.n_mss):
                    common = int (val.and_matrix[i,j,k])
                    if common > 0 and j != k:
                        values.append ( (
                            j + 1,
                            k + 1,
                            chapter.n,
                            common,
                            int (val.eq_matrix[i,j,k]),
                            int (val.ancestor_matrix[i,j,k]),
                            int (val.ancestor_matrix[i,k,j]),
                            int (val.unclear_ancestor_matrix[i,j,k]),
                            int (val.parent_matrix[i,j,k]),
                            int (val.parent_matrix[i,k,j]),
                            int (val.unclear_parent_matrix[i,j,k]),
                            float (val.quotient_matrix[i,j,k]),
                        ) )

            # speed gain for using executemany_raw: 65s to 55s :-(
            # probably the bottleneck here is string formatting with %s
            executemany_raw (conn, """
            INSERT INTO {aff} (id1, id2, chapter, common, equal, older, newer, unclear,
                               p_older, p_newer, p_unclear, affinity)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, parameters, values)

        print ("eq\n",       val.eq_matrix)
        print ("ancestor\n", val.ancestor_matrix)
        print ("unclear\n",  val.unclear_ancestor_matrix)
        print ("and\n",      val.and_matrix)
        print ("quot\n",     val.quotient_matrix)


def affinity_clustering (dba, parameters, val):
    import sklearn.cluster

    labels = sklearn.cluster.spectral_clustering (
        val.quotient_matrix, n_clusters = 20, eigen_solver = 'arpack', random_state = 123)

    data = zip (labels, val.hss)

    data = sorted (data, key = operator.itemgetter (0))
    for label, group in itertools.groupby (data, operator.itemgetter (0)):
        for g in group:
            print (g[1], end = ' ')
        print ("\n")


def affinity_to_gephi (dba, parameters, val):
    """Export the affinity matrix to Gephi.

    Gephi wants 2 tables: a table of nodes and a table of edges.

    """

    message (1, "        : Exporting to Gephi ...")

    with dba.engine.begin () as conn:

        execute (conn, "TRUNCATE {g_nodes}", parameters)
        execute (conn, "TRUNCATE {g_edges}", parameters)

        # Length of manuscripts (no. of defined passages)
        val.ms_length = np.asmatrix (val.def_matrix) * np.ones ((val.n_passages, 1), dtype = int)
        val.ms_length = val.ms_length.A[:, 0]
        print ("Manuscript Length Array: ", val.ms_length)

        # Build Gephi nodes table.  Every ms gets to be a node.  Simple.
        values = []
        for i in range (0, val.n_mss):
            hs = val.mss[i].hs
            hsnr = val.mss[i].hsnr
            size = int (val.ms_length[i])
            color = '128,128,128'
            if hsnr < 400000:
                color = '0,255,0'
            if hsnr < 300000:
                color = '128,128,255'
            if hsnr < 200000:
                color = '255,255,128'
            if hsnr < 100000:
                color = '255,0,0'
            values.append ( {
                'id'        : hsnr,
                'label'     : hs,
                'color'     : color,
                'nodecolor' : color,
                'nodesize'  : size
            } )

        executemany (conn, """
        INSERT INTO {g_nodes} (id, label, color, nodecolor, nodesize)
        VALUES (:id, :label, :color, :nodecolor, :nodesize)
        """, parameters, values)

        # Build Gephi edges table.  Needs brains.  Creating an edge between every 2
        # mss will not give a very meaningful graph.  We have to keep only the most
        # significant edges.  But what is significant?

        # We rank the neighbors of each ms by similarity and keep only the X most
        # similar ones.
        keep = 20
        rank_matrix = np.argsort (val.quotient_matrix[0], axis = 1)
        rank_matrix = rank_matrix[0:, -keep:]  # keep the most similar entries
        # Now we have the indices of the X most similar mss.

        values = []
        qq = math.log (val.n_passages)
        for i in range (2, val.n_mss): # do not include 'A' and 'MT'
            hs_src = val.mss[i].hsnr
            for j in range (0, keep):
                k = rank_matrix[i, j]
                hs_dest = val.mss[k].hsnr
                q = val.quotient_matrix[0, i, k] * math.log (max (1.0, val.and_matrix[0, i, k])) / qq
                values.append ( {
                    'id'     : "%s-%s" % (hs_src, hs_dest),
                    'source' : hs_src,
                    'target' : hs_dest,
                    'weight' : float (q)
                } )

        executemany (conn, """
        INSERT INTO {g_edges} (id, source, target, weight)
        VALUES (:id, :source, :target, :weight)
        """, parameters, values)

        # np.savetxt ('affinity.csv', val.quotient_matrix)


def print_stats (dba, parameters):

    with dba.engine.begin () as conn:

        res = execute (conn, "SELECT count (distinct hs) FROM {att}", parameters)
        hs = res.scalar ()
        message (1, "hs       = {cnt}".format (cnt = hs))

        res = execute (conn, "SELECT count (*) FROM (SELECT DISTINCT anfadr, endadr FROM {att}) AS sq", parameters)
        passages = res.scalar ()
        message (1, "passages = {cnt}".format (cnt = passages))

        message (1, "hs * passages      = {cnt}".format (cnt = hs * passages))

        res = execute (conn, "SELECT count(*) FROM {att}", parameters)
        att = res.scalar ()
        res = execute (conn, "SELECT count(*) FROM {lac}", parameters)
        lac = res.scalar ()
        res = execute (conn, "SELECT count(*) FROM {labez}", parameters)
        lab = res.scalar ()

        message (1, "rows in att        = {cnt}".format (cnt = att))
        message (1, "rows in lac        = {cnt}".format (cnt = lac))
        message (1, "rows in labez      = {cnt}".format (cnt = lab))
        message (1, "delta              = {cnt}".format (cnt = lab - (hs * passages)))

        # sum (passages in chapter * mss with chapter)

        res = execute (conn, """
        SELECT sum (pas_cnt * ch.ms_cnt)

        FROM
          (SELECT kapanf, count (*) AS pas_cnt FROM (SELECT DISTINCT kapanf, anfadr, endadr FROM {att}) AS sq GROUP BY kapanf) AS pas

        JOIN
          (SELECT kapanf, count (distinct hs) AS ms_cnt FROM {att} GROUP BY kapanf) AS ch

        ON ch.kapanf = pas.kapanf

        """, parameters)
        pas = res.scalar ()

        message (1, "chap * ms * pas    = {cnt}".format (cnt = pas))


if __name__ == '__main__':

    logging.basicConfig ()

    parser = argparse.ArgumentParser (description='Prepare a new database for CBGM')

    parser.add_argument ('source_db', metavar='SOURCE_DB', help='the source ECM database (required)')
    parser.add_argument ('target_db', metavar='TARGET_DB', help='the target ECM database (required)')
    parser.add_argument ('src_vg_db', metavar='SRC_VG_DB', help='the source VarGenAtt database (required)')

    parser.add_argument ('-r', '--range', default='',
                         help='range of steps (default: all)')
    parser.add_argument ('-v', '--verbose', dest='verbose', action='count',
                         help='increase output verbosity', default=0)
    parser.add_argument ('-c', '--chapter', dest='chapter', type=int, default=0,
                         help='the chapter number (optional, default=all chapters)')
    parser.add_argument ('-p', '--profile', dest='profile', default='ntg-local',
                         metavar='PROFILE', help="the database profile (default='ntg-local')")

    parser.parse_args (namespace = args)

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

    args.start_time = datetime.datetime.now ()
    parameters = tools.init_parameters (tools.DEFAULTS)

    dbsrc1 = db.MySQLEngine      (args.profile, args.source_db)
    dbsrc2 = db.MySQLEngine      (args.profile, args.src_vg_db)
    dbdest = db.PostgreSQLEngine (database = args.target_db)

    logging.getLogger ('sqlalchemy.engine').setLevel (logging.ERROR)

    v = Bag ()
    try:
        for step in range (args.range[0], args.range[1] + 1):
            if step == 1:
                step01  (dbsrc1, dbdest, parameters)
                step01b (dbdest, parameters)
                step01c (dbdest, parameters)
                continue
            if step == 2:
                step02 (dbdest, parameters)
                continue
            if step == 3:
                step03 (dbdest, parameters)
                continue
            if step == 4:
                step04 (dbdest, parameters)
                continue
            if step == 5:
                step05 (dbdest, parameters)
                continue
            if step == 6:
                step06 (dbdest, parameters)
                step06b (dbdest, parameters)
                continue
            if step == 7:
                step07 (dbdest, parameters)
                if args.verbose >= 1:
                    print_stats (dbdest, parameters)
                continue
            if step == 8:
                step08 (dbdest, parameters)
                if args.verbose >= 1:
                    print_stats (dbdest, parameters)
                continue


            if step == 31:
                message (1, "Step 31 : Filling the Manuscripts and Passages tables ...")
                create_ms_pass_tables (dbdest, parameters)
                message (1, "Step 31 : Create Labez Table ...")
                create_labez_table (dbdest, parameters)
                if args.verbose >= 1:
                    print_stats (dbdest, parameters)
                continue
            if step == 32:
                message (1, "Step 32 : Copying genealogical data ...")
                copy_genealogical_data (dbsrc1, dbsrc2, dbdest, parameters)
                message (1, "        : Preprocessing genealogical data ...")
                preprocess_genealogical_data (dbdest, parameters)
                continue
            if step == 33:
                message (1, "Step 33 : Creating the labez matrix ...")
                create_labez_matrix (dbdest, parameters, v)
                message (1, "Step 33 : Building Byzantine text ...")
                build_byzantine_text (dbdest, parameters, v)
                continue
            if step == 34:
                message (1, "Step 34 : Calculating mss similarity ...")
                calculate_mss_similarity (dbdest, parameters, v)
                message (1, "        : Exporting Gephi Tables ...")
                affinity_to_gephi (dbdest, parameters, v)
                continue

    except KeyboardInterrupt:
        pass

    message (1, "          Done")
