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
import types

import numpy as np
import six
import sqlalchemy

sys.path.append (os.path.dirname (os.path.abspath (__file__)) + "/../..")

from ntg_common import db
from ntg_common import tools
from ntg_common import plot
from ntg_common.db import execute, executemany, executemany_raw, debug, fix
from ntg_common.tools import log
from ntg_common.config import args

PLOT = 0 # plot pretty pictures

N_FIELDS = 'base comp comp1 komm kontrolle korr lekt over over1 suff suffix2 vid vl'.split ()
""" Field to look for 'N' and NULL """

NULL_FIELDS = 'lemma lesart'.split ()
""" Fields to look for NULL """

DB_INSERT_CHUNK_SIZE = 100000

def ord_labez (labez):
    return ord (labez[0]) - 96


def char_labez (labez):
    return chr (labez + 96)


def step01 (dba, dbb, parameters):
    """Copy tables to new database

    Copy the (28 * 2) mysql tables to 2 tables in a new postgres database.  Do
    *not* copy versions and patristic manuscripts.

    """

    log (logging.INFO, "Step  1 : Copying tables ...")

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

        # create two big tables for easier debugging
        rows = execute (src, """
        CREATE OR REPLACE TABLE {att} LIKE Acts01GVZ;
        """, parameters)
        rows = execute (src, """
        CREATE OR REPLACE TABLE {lac} LIKE Acts01GVZlac;
        """, parameters)

        with dbb.engine.begin () as dest:

            # Get a list of tables (there are two tables per chapter)
            table_mask = re.compile (r"^Acts\d\dGVZ")
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

                log (logging.INFO, '          Copying table {source_table}'.format (**parameters))

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

                # Copy the chapter tables into one big table
                rows = execute (src, """
                INSERT INTO {t} ({fields})
                SELECT {fields}
                FROM {source_table}
                WHERE hsnr < 500000 AND endadr >= anfadr
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

    log (logging.INFO, "Step  1c: Data entry fixes ...")

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

        fix (conn, "Wrong hsnr Ph3", """
        SELECT DISTINCT hs, hsnr, kapanf
        FROM {att}
        WHERE hs ~ '^L1188s2' AND hsnr = 411881
        """, """
        UPDATE {att} SET hsnr = 411881 WHERE hs ~ '^L1188s1';
        UPDATE {att} SET hsnr = 411882 WHERE hs ~ '^L1188s2';
        """, parameters)

        fix (conn, "Wrong hsnr Ph5", """
        SELECT DISTINCT hs, hsnr, kapanf
        FROM {att}
        WHERE hs = 'L1188' AND hsnr != 411880
        """, """
        UPDATE {att} SET hsnr = 411881 WHERE hs ~ '^L1188s';
        UPDATE {att} SET hsnr = 411880 WHERE hs = 'L1188';
        UPDATE {lac} SET hsnr = 411881, hs = REPLACE (hs, 's2', 's') WHERE hs ~ '^L1188s2';
        UPDATE {lac} SET hsnr = 411880, hs = REPLACE (hs, 's1', '')  WHERE hs ~ '^L1188s1';
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
        UPDATE {lac}
        SET endadr = 52831035
        WHERE endadr = 52831034;
        UPDATE {lac}
        SET endadr = 51130024
        WHERE hsnr = 202440 AND anfadr = 51101002;
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

    log (logging.INFO, "Step  2 : Cleanup korr and lekt ...")

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

    log (logging.INFO, "Step  5: Processing Duplicated Readings (T1, T2) ...")

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
          HAVING count (*) = 1
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

    log (logging.INFO, "Step  6 : Delete later hands ...")

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

    log (logging.INFO, "Step  6b: Delete [CLTV*] from HS ...")

    with dba.engine.begin () as conn:

        fix (conn, "Duplicate readings", """
        SELECT hsnr, anfadr, endadr
        FROM {att}
        GROUP BY hsnr, anfadr, endadr
        HAVING count (*) > 1
        """, """
        DELETE FROM {att}
        WHERE (hs, anfadr, endadr) = ('L156s*', 50405022, 50405034) OR
              (hs, anfadr, endadr) = ('1891*V', 52716012, 52716012) OR
              (hs, anfadr, endadr) = ('P74V',   51535022, 51535028) OR
              (hs, anfadr, endadr) = ('02*V',   52101008, 52101010)

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

    log (logging.INFO, "Step  7 : Fix 'zw' ...")

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

    log (logging.DEBUG, "          %d zw labez updated" % updated)


def delete_passages_without_variants (dba, parameters):
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

    with dba.engine.begin () as conn:

        execute (conn, """
        DELETE FROM {att}
        WHERE (anfadr, endadr) IN (
          SELECT anfadr, endadr
          FROM (
            SELECT DISTINCT anfadr, endadr, labez
            FROM {att}
            WHERE labez !~ '^z'
          ) AS i
          GROUP BY anfadr, endadr
          HAVING count (*) <= 1
        )
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
    varid_matrix = None    # mss x passages matrix of varnew
    affinity_matrix = None  # mss x mss matrix of similarity measure


def create_ms_pass_tables (dba, parameters):
    """ Create the Manuscripts, Chapters, Passages and Nested Passages tables. """

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

        # ms_id = 3, 4, 5, ...
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
        INSERT INTO {pass} (buch, kapanf, versanf, wortanf, kapend, versend, wortend, anfadr, endadr, irange, lemma)
        SELECT buch, kapanf, versanf, wortanf, kapend, versend, wortend,
               anfadr, endadr, int4range (anfadr, endadr + 1),
               MODE () WITHIN GROUP (ORDER BY lemma) AS lemma
        FROM {att}
        GROUP BY buch, kapanf, versanf, wortanf, kapend, versend, wortend, anfadr, endadr, int4range (anfadr, endadr + 1)
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

        execute (conn, """
        UPDATE {pass} p
        SET fehlvers = True
        WHERE {fehlverse}
        """, parameters)

        # The Readings Table

        execute (conn, """
        INSERT INTO {read} (pass_id, labez, labezsuf, lesart)
        SELECT p.id AS pass_id, labez, labezsuf,
               MODE () WITHIN GROUP (ORDER BY lesart) AS lesart
        FROM {att} a
        JOIN {pass} p
          ON (a.anfadr, a.endadr) = (p.anfadr, p.endadr)
        GROUP BY p.id, labez, labezsuf
        """, parameters)


def create_var_table (dba, parameters):
    """Tabelle 'var' erstellen

    Aus: prepare4cbgm_9.py

        Stellenbezogene Lückenliste füllen.  Parallel zum Apparat wurde eine
        systematische Lückenliste erstellt, die die Lücken aller griechischen
        Handschriften enthält.  Wir benötigen diese Information jedoch jeweils
        für die variierten Stellen.

    Build a table containing only the information we need for CBGM, that is:
    manuscript id, passage id, and varnew.

    """

    with dba.engine.begin () as conn:

        execute (conn, """
        TRUNCATE {var}
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

        # unroll lacunae.  All lacunae get a labez of 'zz'.
        execute (conn, """
        INSERT INTO {var} (ms_id, pass_id, labez, labezsuf)
        SELECT DISTINCT ms.id, p.id, 'zz', ''
        FROM {lac} l
        JOIN {pass} p
          ON p.irange <@ int4range (l.anfadr, l.endadr + 1)
        JOIN {ms} ms
          ON ms.hsnr = l.hsnr
        """, parameters)

        # copy labez from att eventually overwriting lacunae
        execute (conn, """
        INSERT INTO {var} (ms_id, pass_id, labez, labezsuf)
        SELECT ms.id as ms_id, p.id as pass_id, labez, labezsuf
          FROM {att} att
          JOIN {pass} p
            ON p.anfadr = att.anfadr AND p.endadr = att.endadr
          JOIN {ms} ms
            ON ms.hsnr = att.hsnr
        ON CONFLICT (ms_id, pass_id)
          DO UPDATE SET labez = EXCLUDED.labez, labezsuf = EXCLUDED.labezsuf
        """, parameters)

        #
        # Build a positive apparatus
        #

        # 1. Insert missing rows and set labez = ''
        execute (conn, """
        INSERT INTO {var} (ms_id, pass_id, labez, labezsuf)
        SELECT ms.id, p.id, '', ''
          FROM
            {pass} p
          CROSS JOIN
            {ms} ms
        ON CONFLICT DO NOTHING
        """, parameters)

        # Mark Fehlverse with 'zu'.
        execute (conn, """
        UPDATE {var}
        SET labez = 'zu'
        FROM {pass} p
        WHERE p.id = pass_id AND p.fehlvers AND labez = ''
        """, parameters)

        # Fill A with labez 'zz'.  No reading for A means that the original text
        # could not be established.
        #execute (conn, """
        #UPDATE {var}
        #SET labez = 'zz'
        #WHERE labez = '' AND ms_id = 1
        #""", parameters)

        # Fill with labez 'a'.
        execute (conn, """
        UPDATE {var}
        SET labez = 'a'
        WHERE labez = ''
        """, parameters)


def copy_genealogical_data (dbsrc, dbsrcvg, dbdest, parameters):
    """Copy / update genealogical data

    Aus: VGA/Att2CBGMPh3.pl

    "kopiert die Daten aus ECM_Acts_CBGM nach VarGenAtt_Act,
    zur weiteren Bearbeitung im Stemma-Editor"

    INSERT INTO LocStemEdAct (varid, begadr, endadr)
      SELECT DISTINCT labez, anfadr, endadr FROM Acts01";
    UPDATE LocStemEdAct SET varnew = varid;
    UPDATE LocStemEdAct SET s1 = '*' WHERE varid =  'a';
    UPDATE LocStemEdAct SET s1 = 'a' WHERE varid <> 'a';

    Same play with VarGenAttAct w/o DISTINCT.
    Same play with RdgAct w/o DISTINCT.


    Aus: VGA/PortCBGMInfoPh3.pl

    "Kopiert die genealogischen Informationen von einer Phase zur nächsten.

    Splitts müssen nur dort übertragen werden, wo sich der Apparat nicht
    geändert hat.  Hat sich der Apparat geändert, d.h. gibt es in der neuen
    Phase für eine Adresse keine Entsprechung in der vorhergehenden Phase, so
    werden die Defaultwerte eingetragen.  Zuerst muss festgestellt werden, wo
    Splitts oder Zusammenlegungen stattgefunden haben.  Dann werden diese
    Lesarten gelöscht und aus der vorhergehenden Phase kopiert.

    Stellen mit geänderter Leitzeile werden zunächst einfach übergangen.

    Defaultwerte eintragen, wenn eine variierte Stelle mit gleicher numerischer
    Adresse mehr Lesarten als in der vorhergehenden Phase hat, die nicht nur
    versionell bezeugt sind."

    VarGenAtt_ActPh2 -> VarGenAtt_ActPh3


    1. copy entries from att with default values (every other labez depends on
       a) (done in the last step)

    2. overwrite with values from locstemed (done in this step)

    FIXME: do we really need step 1? To provide the new passages if the
    apparatus changed? At least it doesn't do any damage because there should be
    no passages in att that are not in locstemed also.


    """

    dbsrc_meta = sqlalchemy.schema.MetaData (bind = dbsrc.engine)
    dbsrc_meta.reflect ()
    dbsrcvg_meta = sqlalchemy.schema.MetaData (bind = dbsrcvg.engine)
    dbsrcvg_meta.reflect ()

    with dbdest.engine.begin () as dest:

        execute (dest, """
        TRUNCATE {locstemed}
        """, parameters)

        with dbsrcvg.engine.begin () as src:

            # Create debug tables

            def create_debug_table (dest_table, source_tables):
                """Copy 28 tables into one for easier debugging."""

                execute (src, """
                CREATE OR REPLACE TABLE {dest_table} LIKE {source_table}
                """, dict (parameters, dest_table = dest_table, source_table = source_tables + '01'))

                table_mask = re.compile ('^' + source_tables + r'\d\d$')
                for source_table in sorted (dbsrcvg_meta.tables.keys ()):
                    if not table_mask.match (source_table):
                        continue
                    log (logging.INFO, "        : Copying table %s" % source_table)

                    source_model = sqlalchemy.Table (source_table, dbsrcvg_meta, autoload = True)
                    source_columns = ['`' + column.name.lower () + '`'
                                      for column in source_model.columns if column.name != 'id']

                    rows = execute (src, """
                    INSERT INTO {dest_table} ({columns})
                    SELECT {columns}
                    FROM {source_table}
                    """, dict (parameters, source_table = source_table, dest_table = dest_table,
                               columns = ', '.join (source_columns)))

            create_debug_table (parameters['locstemed'], 'LocStemEdAct')
            create_debug_table (parameters['read'],      'RdgAct')
            create_debug_table (parameters['var'],       'VarGenAttAct')

            # LocStemEd
            #
            # Generate LocStemEd from VarGenAtt.  This is the production
            # LocStemEd table.  We prefer to recreate it from VarGenAtt to
            # guarantee that those two tables will not be out of sync.

            params = []
            table_mask = re.compile (r'^VarGenAttAct\d\d$')
            for table_name in sorted (dbsrcvg_meta.tables.keys ()):
                if not table_mask.match (table_name):
                    continue
                log (logging.INFO, "        : Copying table %s" % table_name)

                parameters['source_table'] = table_name

                rows = execute (src, """
                SELECT varid, varnew, s1, s2, begadr, endadr
                FROM {source_table}
                GROUP BY begadr, endadr, varid, varnew, s1, s2
                """, parameters)

                params += [r for r in rows]

            executemany_raw (dest, """
            INSERT INTO {locstemed} (pass_id, varid, varnew, s1, s2)
            SELECT p.id, %s, %s, %s, %s
            FROM {pass} p
            WHERE (p.anfadr, p.endadr) = (%s, %s)
            ON CONFLICT (pass_id, varnew, s1)
              DO UPDATE SET s1 = EXCLUDED.s1, s2 = EXCLUDED.s2
            """, parameters, params)


            fix (dest, "Loop in local stemma", """
            SELECT *
            FROM {locstemed}
            WHERE varnew = s1 OR varnew = s2;
            """, """
            UPDATE {locstemed}
            SET s1 = '?'
            WHERE varnew = s1
            """, parameters)

            fix (dest, "Readings older than 'A'", """
            SELECT *
            FROM {var}_view v
            JOIN {locstemed} l USING (pass_id, varnew)
            WHERE v.ms_id = 1 AND l.s1 NOT IN ('*', '?')
            """, """
            /* harmonize it with other occurences but shoudn't it be '?' ? */
            UPDATE {locstemed} l
            SET s1 = 'a'
            FROM {var}_view v
            WHERE v.pass_id = l.pass_id AND v.varnew = l.varnew
              AND v.ms_id = 1 AND l.s1 NOT IN ('*', '?') AND v.varnew = 'zu';

            UPDATE {locstemed} l
            SET s1 = '*'
            FROM {pass} p
            WHERE l.pass_id = p.id AND (anfadr, endadr) = (50220027, 50220027)
              AND varnew = 'a';

            UPDATE {locstemed} l
            SET s1 = 'a'
            FROM {pass} p
            WHERE l.pass_id = p.id AND (anfadr, endadr) = (50220027, 50220027)
              AND varnew = 'b';

            """, parameters)

            # VarGenAtt

            params = []
            table_mask = re.compile (r'^VarGenAttAct\d\d$')
            for table_name in sorted (dbsrcvg_meta.tables.keys ()):
                if not table_mask.match (table_name):
                    continue
                log (logging.INFO, "        : Copying table %s" % table_name)

                parameters['source_table'] = table_name

                rows = execute (src, """
                SELECT begadr, endadr, varid, varnew, GROUP_CONCAT(ms) AS hsnr
                FROM {source_table}
                GROUP BY begadr, endadr, varid, varnew
                """, parameters)

                for r in rows:
                    params.append ({
                        'anfadr' : r[0],
                        'endadr' : r[1],
                        'varid'  : r[2],
                        'varnew' : r[3],
                        'hsnr'   : [int (hsnr) for hsnr in r[4].split (',')],
                    })

            executemany (dest, """
            UPDATE {var} v
            SET varid = :varid, varnew = :varnew
            FROM {ms} ms, {pass} pass
            WHERE v.ms_id   = ms.id   AND ARRAY[ms.hsnr] <@ ARRAY[:hsnr]
              AND v.pass_id = pass.id AND (pass.anfadr, pass.endadr) = (:anfadr, :endadr)
            """, parameters, params)

            # Because VarGenAttActXX does not contain manuscripts that are not
            # defined in chapter XX we must put in the 'zz' readings ourselves.
            execute (dest, """
            UPDATE {var}
            SET varid = 'zz', varnew = 'zz'
            WHERE labez = 'zz' AND varnew = ''
            """, parameters)

            fix (dest, "Bogus varnew", """
            SELECT *
            FROM {var}
            WHERE ord_labez (varid) != ord_labez (varnew)
            ORDER BY ms_id, pass_id, varnew
            """, """
            UPDATE {var}
            SET varnew = 'a'
            WHERE varid = 'a' AND varnew = 's';
            DELETE FROM {locstemed}
            WHERE ord_labez (varid) != ord_labez (varnew)
            """, parameters)


def build_byzantine_text (dba, parameters):
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

        execute (conn, """
        DELETE FROM {var} WHERE ms_id = 2
        """, parameters)

        execute (conn, """
        INSERT INTO {var} (ms_id, pass_id, labez, varid, varnew)
          SELECT 2, pass_id, varid, varid, varid
          FROM (
            SELECT pass_id,
                   (ARRAY_AGG (varid ORDER BY cnt DESC))[1] AS varid,
                   ARRAY_AGG (cnt ORDER BY cnt DESC) AS mask
            FROM (
              SELECT pass_id, varid, count (*) AS cnt
              FROM {var} v
              JOIN {ms} ms
                ON v.ms_id = ms.id
              WHERE hsnr IN {byzlist}
              GROUP BY pass_id, varid
            ) AS q1
            GROUP BY pass_id
          ) AS q2
          WHERE mask IN ('{{7}}', '{{6,1}}', '{{5,1,1}}')
        """, parameters)

        # Fill with labez 'zz' where MT is undefined
        execute (conn, """
        INSERT INTO {var} (ms_id, pass_id, labez, varid, varnew)
        SELECT 2, p.id, 'zz', 'zz', 'zz'
        FROM {pass} p
        ON CONFLICT DO NOTHING
        """, parameters)


def preprocess_local_stemmas (dba, parameters):
    """Preprocess local stemmas

    Preprocess the locstemed table to allow for faster retrieval of ancestors.

    """

    with dba.engine.begin () as conn:

        fix (conn, "Disconnected local stemma: s1 without corresponding varnew", """
        SELECT DISTINCT l1.pass_id, p.anfadr, p.endadr, l1.s1
        FROM {locstemed} l1
        JOIN {pass} p
          ON l1.pass_id = p.id
        WHERE l1.s1 NOT IN ('*', '?', '') AND l1.varnew !~ '^z' AND NOT EXISTS (
          SELECT * FROM {locstemed} l2
          WHERE l1.pass_id = l2.pass_id AND l1.s1 = l2.varnew
        )
        ORDER BY l1.pass_id, l1.s1
        """, "", parameters)

        # preprocess source readings
        #
        # We want to quickly test if a reading is older than another reading.
        # We don't want to traverse the graph back to the root every time this
        # question comes up.  So we add a field to the LocStemEd table that
        # contains an array of all ancestral readings for every reading.
        #
        # mask: 1 = '?'
        #       2, 3, ...  = 'a', 'a1', ...
        #
        # Note: the assignment differs at evey passage!

        maskgen = """
        WITH mask AS (
          SELECT pass_id, varnew,
                 1 << ((row_number () OVER (PARTITION BY pass_id ORDER BY varnew))::integer + 1) AS mask
          FROM {locstemed}
        )
        """

        execute (conn, maskgen + """
        UPDATE {locstemed} l
        SET varnewmask = m.mask
        FROM mask m
        WHERE (l.pass_id, l.varnew) = (m.pass_id, m.varnew);
        """, parameters)

        execute (conn, maskgen + """
        UPDATE {locstemed} l
        SET s1mask = m.mask
        FROM mask m
        WHERE (l.pass_id, l.s1) = (m.pass_id, m.varnew);
        """, parameters)

        execute (conn, maskgen + """
        UPDATE {locstemed} l
        SET s2mask = m.mask
        FROM mask m
        WHERE (l.pass_id, l.s2) = (m.pass_id, m.varnew);
        """, parameters)

        execute (conn, """
        UPDATE {locstemed} l
        SET parents = s1mask + s2mask
        """, parameters)

        # Build tree starting from '*' and '?'
        execute (conn, """
        WITH RECURSIVE tree AS (
          SELECT pass_id, varnew, CASE WHEN s1 = '?' THEN 1 ELSE 0 END AS ancestors
          FROM {locstemed}
          WHERE s1 IN ('*', '?')
        UNION
          SELECT l.pass_id, l.varnew,
            CASE WHEN l.s1 = t.varnew THEN s1mask + t.ancestors ELSE s2mask + t.ancestors END
          FROM {locstemed} l
          JOIN tree t
            ON l.pass_id = t.pass_id AND (l.s1 = t.varnew OR l.s2 = t.varnew)
        )

        UPDATE {locstemed} l
        SET ancestors = t.ancestors
        FROM tree t
        WHERE (l.pass_id, l.varnew) = (t.pass_id, t.varnew);
        """, parameters)

        # These are the passages where A could not be established.
        execute (conn, """
        DELETE FROM  {locstemed} l
        WHERE varnew = 'zz' and s1 = '?'
        """, parameters)


def create_varid_matrix (dba, parameters, val):
    """Create the varid matrix.

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

        # Matrix ms x pass

        # Initialize all manuscripts to the varnew 'a'
        varid_matrix  = np.broadcast_to (np.array ([1], np.uint32), (val.n_mss, val.n_passages)).copy ()

        # overwrite matrix where actual varnew is different from 'a'
        res = execute (conn, """
        SELECT ms_id - 1, pass_id - 1, ord_labez (varid) as varid
        FROM {var}
        WHERE varid != 'a'
        """, parameters)

        for row in res:
            varid_matrix [row[0], row[1]] = row[2]

        val.varid_matrix = varid_matrix

        # Boolean matrix ms x pass set where passage is defined
        val.def_matrix = np.greater (val.varid_matrix, 0)

        print (val.n_mss)
        print (val.n_passages)
        print (val.varid_matrix.shape)

        # debug plot the matrix
        if PLOT:
            ticks_labels_x = plot.passages_labels (val.passages)
            ticks_labels_y = plot.mss_labels (val.mss)

            plot.plt.figure (1)
            plot.heat_matrix (val.def_matrix, "Manuscript Definition Matrix",
                              ticks_labels_x, ticks_labels_y, plot.colormap_bw ())
            plot.plt.savefig ('output/mss-definition.png')
            plot.plt.close ()


def count_by_chapter (a, chapter_ends):
    """Count passages by chapter.

    Count the number of passages per chapter (that satisfy a certain condition).
    Also insert a chapter 0 for the sum over the whole book.  Input is an array
    of one boolean per passage.

    """
    cs = np.cumsum (a)   # cs[1] = a[0] + a[1], ...
    total = cs[-1]
    cs = cs[chapter_ends]
    cs = cs - np.insert (cs, 0, 0)[:-1]
    cs = np.insert (cs, 0, total)
    return cs


def calculate_mss_similarity_preco (dba, parameters, val):
    """Calculate pre-coherence mss similarity

    Aus: VGA/VG05_all3.pl

        Kapitelweise füllen auf Basis von Vergleichen einzelner
        Variantenspektren in ECM_Acts_Sp.  Vergleich von je zwei Handschriften:
        An wieviel Stellen haben sie gemeinsam Text, an wieviel Stellen stimmen
        sie überein bzw. unterscheiden sie sich (inklusive Quotient)?  Die
        Informationen werden sowohl auf Kapitel- wie auch Buchebene
        festgehalten.

    """

    # Matrix chapter x ms x ms with count of the passages that are defined in both mss
    val.and_matrix = np.zeros ((val.n_chapters, val.n_mss, val.n_mss), dtype = np.uint16)

    # Matrix chapter x ms x ms with count of the passages that are equal in both mss
    val.eq_matrix  = np.zeros ((val.n_chapters, val.n_mss, val.n_mss), dtype = np.uint16)

    # Matrix chapter x ms of chapter lengths
    val.chapter_len_matrix = np.zeros ((val.n_chapters, val.n_mss), dtype = np.uint16)

    # ch.end is the end of a range index, so it is actually one behind the
    # item we want to know
    val.chapter_ends = [ch.end - 1 for ch in val.chapters[1:]]

    # pre-genealogical coherence outputs symmetrical matrices
    # loop over all mss O(n_mss² * n_chapters * n_passages)

    for j in range (0, val.n_mss):
        varidj = val.varid_matrix[j]
        defj   = val.def_matrix[j]

        for k in range (j + 1, val.n_mss):
            varidk = val.varid_matrix[k]
            defk   = val.def_matrix[k]

            def_and  = np.logical_and (defj, defk)
            varid_eq = np.logical_and (def_and, np.equal (varidj, varidk))

            val.and_matrix[:,j,k] = val.and_matrix[:,k,j] = count_by_chapter (def_and, val.chapter_ends)
            val.eq_matrix[:,j,k]  = val.eq_matrix[:,k,j]  = count_by_chapter (varid_eq, val.chapter_ends)

    # calculate quotient
    with np.errstate (divide = 'ignore', invalid = 'ignore'):
        val.quotient_matrix = val.eq_matrix / val.and_matrix
        val.quotient_matrix[val.and_matrix == 0] = 0.0

    # calculate chapter lengths
    for j in range (0, val.n_mss):
        val.chapter_len_matrix[:,j] = count_by_chapter (val.def_matrix[j], val.chapter_ends)


def calculate_mss_similarity_postco (dba, parameters, val):
    """Calculate post-coherence mss similarity

    Genealogical coherence outputs asymmetrical matrices.
    Loop over all mss O(n_mss² * n_chapters * n_passages).

    """

    with dba.engine.begin () as conn:

        # load ancestors for each varnew
        res = execute (conn, """
        SELECT v.ms_id   - 1 AS ms_id,
               v.pass_id - 1 AS pass_id,
               l.varnewmask,
               l.parents,
               l.ancestors
        FROM {var} v
        JOIN {locstemed} l
          ON (v.pass_id, v.varnew) = (l.pass_id, l.varnew) AND l.varnew !~ '^z'
        """, parameters)

        LocStemEd = collections.namedtuple ('LocStemEd', 'ms_id pass_id varnewmask parents ancestors')
        rows = list (map (LocStemEd._make, res))

        # Matrix mss x passages containing the bitmask of the current reading
        mask_matrix     = np.zeros ((val.n_mss, val.n_passages), np.uint64)
        # Matrix mss x passages containing the bitmask of the parent readings
        parent_matrix   = np.zeros ((val.n_mss, val.n_passages), np.uint64)
        # Matrix mss x passages containing the bitmask of the ancestral readings
        ancestor_matrix = np.zeros ((val.n_mss, val.n_passages), np.uint64)
        # Matrix mss x passages containing True if source is unclear (s1 = '?')
        quest_matrix    = np.zeros ((val.n_mss, val.n_passages), np.bool_)

        # If ((current bitmask of ms j) and (ancestor bitmask of ms k) > 0) then
        # ms j is an ancestor of ms k.

        for row in rows:
            mask_matrix     [row.ms_id, row.pass_id] = row.varnewmask
            parent_matrix   [row.ms_id, row.pass_id] = row.parents
            ancestor_matrix [row.ms_id, row.pass_id] = row.ancestors
            quest_matrix    [row.ms_id, row.pass_id] = row.parents & 1

        print (mask_matrix)
        print (parent_matrix)
        print (ancestor_matrix)
        print (quest_matrix)

        def postco (mask_matrix, anc_matrix):

            local_stemmas_with_loops = set ()

            # Matrix chapter x ms x ms with count of the passages that are older in ms1 than in ms2
            ancestor_matrix = np.zeros ((val.n_chapters, val.n_mss, val.n_mss), dtype = np.uint16)

            # Matrix chapter x ms x ms with count of the passages whose relationship is unclear in ms1 and ms2
            unclear_matrix  = np.zeros ((val.n_chapters, val.n_mss, val.n_mss), dtype = np.uint16)

            for j in range (0, val.n_mss):
                for k in range (0, val.n_mss):
                    # See: VGA/VGActs_allGenTab3Ph3.pl

                    # set bit if the reading of j is ancestral to the reading of k
                    varidj_is_older = np.bitwise_and (mask_matrix[j], anc_matrix[k]) > 0
                    varidk_is_older = np.bitwise_and (mask_matrix[k], anc_matrix[j]) > 0

                    if j == 0 and k > 0 and varidk_is_older.any ():
                        log (logging.INFO, "Error: found varid older than A in msid: %d = %s"
                                 % (k, np.nonzero (varidk_is_older)))

                    # error check for loops
                    check = np.logical_and (varidj_is_older, varidk_is_older)
                    if np.any (check):
                        not_check       = np.logical_not (check)
                        varidj_is_older = np.logical_and (varidj_is_older, not_check)
                        varidk_is_older = np.logical_and (varidk_is_older, not_check)

                        local_stemmas_with_loops |= set (np.nonzero (check)[0])

                    # wenn die vergl. Hss. von einander abweichen u. eine von ihnen
                    # Q1 = '?' hat, UND KEINE VON IHNEN QUELLE DER ANDEREN IST, ist
                    # die Beziehung 'UNCLEAR'

                    unclear = np.logical_and (val.def_matrix[j], val.def_matrix[k])
                    unclear = np.logical_and (unclear, np.not_equal (val.varid_matrix[j], val.varid_matrix[k]))
                    unclear = np.logical_and (unclear, np.logical_or (quest_matrix[j], quest_matrix[k]))
                    unclear = np.logical_and (unclear, np.logical_not (np.logical_or (varidj_is_older, varidk_is_older)))

                    ancestor_matrix[:,j,k] = count_by_chapter (varidj_is_older, val.chapter_ends)
                    unclear_matrix[:,j,k]  = count_by_chapter (unclear, val.chapter_ends)

            if local_stemmas_with_loops:
                log (logging.INFO, "Error: found loops in local stemmata: %s" % sorted (local_stemmas_with_loops))

            return ancestor_matrix, unclear_matrix

        val.parent_matrix,   val.unclear_parent_matrix   = postco (mask_matrix, parent_matrix)
        val.ancestor_matrix, val.unclear_ancestor_matrix = postco (mask_matrix, ancestor_matrix)

        # sanity tests

        # varid older than ms A
        if val.ancestor_matrix[0,:,0].any ():
            log (logging.INFO, "Error: found varid older than A in msids: %s"
                     % (np.nonzero (val.ancestor_matrix[0,:,0])))

        # norel < 0
        norel_matrix = (val.and_matrix - val.eq_matrix - val.ancestor_matrix -
                        np.transpose (val.ancestor_matrix, (0, 2, 1)) - val.unclear_ancestor_matrix)
        if np.less (norel_matrix, 0).any ():
            log (logging.INFO, "Error: norel < 0 in mss. %s"
                     % (np.nonzero (np.less (norel_matrix, 0))))

        # debug
        if PLOT:
            ticks_labels = plot.mss_labels (val.mss)

            for i, chapter in enumerate (val.chapters):
                plot.plt.figure (dpi = 1200) # figsize = (15, 10), dpi = 300)
                log (logging.DEBUG, "          Plotting Affinity of Chapter %d ..." % i)
                plot.heat_matrix (val.quotient_matrix[i],
                                  "Similarity of Manuscripts - Chapter %d" % chapter.n,
                                  ticks_labels, ticks_labels, plot.colormap_affinity ())
                plot.plt.savefig ('output/affinity-%02d.png' % i) # , bbox_inches='tight')
                plot.plt.close ()

                plot.plt.figure (dpi = 1200) # figsize = (15, 10), dpi = 300)
                log (logging.DEBUG, "          Plotting Ancestry of Chapter %d ..." % i)
                tmp = val.quotient_matrix.copy ()
                tmp[mask] = 0
                plot.heat_matrix (tmp[i],
                                  "Ancestry of Manuscripts - Chapter %d" % chapter.n,
                                  ticks_labels, ticks_labels, plot.colormap_affinity ())
                plot.plt.savefig ('output/ancestry-%02d.png' % i) # , bbox_inches='tight')
                plot.plt.close ()

        # np.fill_diagonal (val.quotient_matrix, 0.0) # remove affinity to self


        log (logging.INFO, "          Updating length in Manuscripts and Chapters tables ...")

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


        log (logging.INFO, "          Filling Affinity table ...")
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

    log (logging.INFO, "        : Exporting to Gephi ...")

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
        log (logging.INFO, "hs       = {cnt}".format (cnt = hs))

        res = execute (conn, "SELECT count (*) FROM (SELECT DISTINCT anfadr, endadr FROM {att}) AS sq", parameters)
        passages = res.scalar ()
        log (logging.INFO, "passages = {cnt}".format (cnt = passages))

        log (logging.INFO, "hs * passages      = {cnt}".format (cnt = hs * passages))

        res = execute (conn, "SELECT count(*) FROM {att}", parameters)
        att = res.scalar ()
        res = execute (conn, "SELECT count(*) FROM {lac}", parameters)
        lac = res.scalar ()

        log (logging.INFO, "rows in att        = {cnt}".format (cnt = att))
        log (logging.INFO, "rows in lac        = {cnt}".format (cnt = lac))

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

        log (logging.INFO, "chap * ms * pas    = {cnt}".format (cnt = pas))


def config_from_pyfile (filename):
    """Mimic Flask config files.

    Emulate the Flask config file parser so we can use the same config files for both,
    the server and this script.

    """

    d = types.ModuleType ('config')
    d.__file__ = filename
    try:
        with open (filename) as config_file:
            exec (compile (config_file.read (), filename, 'exec'), d.__dict__)
    except IOError as e:
        e.strerror = 'Unable to load configuration file (%s)' % e.strerror
        raise

    conf = {}
    for key in dir (d):
        if key.isupper ():
            conf[key] = getattr (d, key)
    return conf


if __name__ == '__main__':

    logging.basicConfig ()

    parser = argparse.ArgumentParser (description='Prepare a database for CBGM')

    parser.add_argument ('profile', metavar='PROFILE', help="the database profile file (required)")

    parser.add_argument ('-v', '--verbose', dest='verbose', action='count',
                         help='increase output verbosity', default=0)
    parser.add_argument ('-r', '--range', default='',
                         help='range of steps (default: all)')

    parser.parse_args (namespace = args)

    config = config_from_pyfile (args.profile)

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
    parameters['target_db'] = tools.quote (config['PGDATABASE'])
    parameters['source_db'] = tools.quote (config['MYSQL_ECM_DB'])
    parameters['src_vg_db'] = tools.quote (config['MYSQL_VG_DB'])

    logging.basicConfig (format = '%(relativeCreated)d - %(levelname)s - %(message)s')
    logging.getLogger ('sqlalchemy.engine').setLevel (args.log_level)
    logging.getLogger ('server').setLevel (args.log_level)

    dbsrc1 = db.MySQLEngine      (config['MYSQL_GROUP'], config['MYSQL_ECM_DB'])
    dbsrc2 = db.MySQLEngine      (config['MYSQL_GROUP'], config['MYSQL_VG_DB'])
    dbdest = db.PostgreSQLEngine (**config)

    logging.getLogger ('sqlalchemy.engine').setLevel (logging.ERROR)

    v = Bag ()
    try:
        for step in range (args.range[0], args.range[1] + 1):
            if step == 1:
                log (logging.INFO, "Step  1 : Creating tables ...")

                db.Base.metadata.drop_all (dbdest.engine)
                db.Base.metadata.create_all (dbdest.engine)

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
                log (logging.INFO, "Step  8 : Deleting passages without variants ...")
                delete_passages_without_variants (dbdest, parameters)
                if args.verbose >= 1:
                    print_stats (dbdest, parameters)
                continue

            if step == 31:
                log (logging.INFO, "Step 31 : Dropping tables ...")
                db.Base2.metadata.drop_all   (dbdest.engine)
                log (logging.INFO, "        : Creating tables ...")
                db.Base2.metadata.create_all (dbdest.engine)
                log (logging.INFO, "        : Creating functions ...")
                with dbdest.engine.begin () as dest:
                    db.create_functions (dest, parameters)

                log (logging.INFO, "        : Filling the Manuscripts and Passages tables ...")
                create_ms_pass_tables (dbdest, parameters)

                log (logging.INFO, "        : Filling the Var table ...")
                create_var_table (dbdest, parameters)
                continue

            if step == 32:
                log (logging.INFO, "Step 32 : Copying genealogical data ...")
                copy_genealogical_data (dbsrc1, dbsrc2, dbdest, parameters)

                log (logging.INFO, "        : Building Byzantine text ...")
                build_byzantine_text (dbdest, parameters)

                log (logging.INFO, "        : Preprocessing local stemmas ...")
                preprocess_local_stemmas (dbdest, parameters)
                continue

            if step == 33:
                log (logging.INFO, "Step 33 : Creating the varid matrix ...")
                create_varid_matrix (dbdest, parameters, v)

                log (logging.INFO, "        : Calculating mss similarity pre-co ...")
                calculate_mss_similarity_preco (dbdest, parameters, v)

                log (logging.INFO, "        : Calculating mss similarity post-co ...")
                calculate_mss_similarity_postco (dbdest, parameters, v)

                log (logging.INFO, "        : Exporting Gephi Tables ...")
                affinity_to_gephi (dbdest, parameters, v)
                continue

    except KeyboardInterrupt:
        pass

    log (logging.INFO, "          Done")
