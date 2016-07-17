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
import math
import operator
import os
import re
import sys

import networkx as nx
import numpy as np
import six

sys.path.append (os.path.dirname (os.path.abspath (__file__)) + "/../..")

from ntg_common import db
from ntg_common import tools
from ntg_common import plot
from ntg_common.db import execute, executemany, debug, fix
from ntg_common.tools import message
from ntg_common.config import args


N_FIELDS = 'base comp comp1 komm kontrolle korr lekt over over1 suff suffix2 vid vl'.split ()
""" Field to look for 'N' and NULL """

NULL_FIELDS = 'lemma lesart'.split ()
""" Fields to look for NULL """

MAX_LABEZ = ord ('z') - ord ('a') + 1
""" Max. no. of different labez """

def create_indices (conn):
    message (2, "          Creating indices ...")

    execute (conn, 'CREATE INDEX Hs     ON {att} (hs)', parameters)
    execute (conn, 'CREATE INDEX Hsnr   ON {att} (hsnr)', parameters)
    execute (conn, 'CREATE INDEX Anfadr ON {att} (anfadr)', parameters)
    execute (conn, 'CREATE INDEX Endadr ON {att} (endadr)', parameters)

    execute (conn, 'CREATE INDEX HsAdr  ON {att} (hs, anfadr, endadr)', parameters)

    execute (conn, 'CREATE UNIQUE INDEX Labez ON {labez} (ms_id, pass_id)', parameters)


def step01 (dba, parameters):
    """Copy tables to new database

    Copy the (28 * 2) tables to 2 tables in a new database.  Do *not* copy
    versions and patristic manuscripts.  Create indices and some views.

    """

    message (1, "Step  1 : Creating tables ...")

    with dba.engine.begin () as conn:

        # Eventually create the database and table
        execute (conn, 'DROP DATABASE IF EXISTS {target_db}', parameters)
        execute (conn, 'CREATE DATABASE IF NOT EXISTS {target_db}', parameters)

        execute (conn, 'USE {target_db}', parameters)

        parameters['fields'] = db.CREATE_TABLE_ATT
        execute (conn, 'CREATE OR REPLACE TABLE {att} {fields}'      , parameters)
        parameters['fields'] = db.CREATE_TABLE_LAC
        execute (conn, 'CREATE OR REPLACE TABLE {lac} {fields}'      , parameters)
        parameters['fields'] = db.CREATE_TABLE_LABEZ
        execute (conn, 'CREATE OR REPLACE TABLE {labez} {fields}'    , parameters)
        parameters['fields'] = db.CREATE_TABLE_VP
        execute (conn, 'CREATE OR REPLACE TABLE {vp} {fields}'       , parameters)
        parameters['fields'] = db.CREATE_TABLE_RDG
        execute (conn, 'CREATE OR REPLACE TABLE {rdg} {fields}'      , parameters)
        parameters['fields'] = db.CREATE_TABLE_WITN
        execute (conn, 'CREATE OR REPLACE TABLE {witn} {fields}'     , parameters)
        parameters['fields'] = db.CREATE_TABLE_MSLISTVAL
        execute (conn, 'CREATE OR REPLACE TABLE {listval} {fields}'  , parameters)
        parameters['fields'] = db.CREATE_TABLE_VG
        execute (conn, 'CREATE OR REPLACE TABLE {vg} {fields}'       , parameters)
        parameters['fields'] = db.CREATE_TABLE_MANUSCRIPTS
        execute (conn, 'CREATE OR REPLACE TABLE {ms} {fields}'       , parameters)
        parameters['fields'] = db.CREATE_TABLE_AFFINITY
        execute (conn, 'CREATE OR REPLACE TABLE {aff} {fields}'      , parameters)
        parameters['fields'] = db.CREATE_TABLE_GEPHI_NODES
        execute (conn, 'CREATE OR REPLACE TABLE {g_nodes} {fields}'  , parameters)
        parameters['fields'] = db.CREATE_TABLE_GEPHI_EDGES
        execute (conn, 'CREATE OR REPLACE TABLE {g_edges} {fields}'  , parameters)

        res = execute (conn, 'SHOW COLUMNS IN {att}', parameters)
        target_columns_att = set ([row[0].lower () for row in res])
        res = execute (conn, 'SHOW COLUMNS IN {lac}', parameters)
        target_columns_lac = set ([row[0].lower () for row in res])

        # these columns get special treatment
        target_columns_att -= set (('id', 'created'))
        target_columns_lac -= set (('id', 'created'))

        # Get a list of tables (there are two tables per chapter)
        res = execute (conn, 'SHOW TABLES FROM {source_db} LIKE :table_mask', parameters)

        message (1, "Step  1 : Copying tables ...")

        for row in res:
            parameters['source_table'] = row[0]
            parameters['source'] = '{source_db}."{source_table}"'.format (**parameters)

            is_lac_table = parameters['source_table'].endswith('lac')
            parameters['t'] = parameters['lac'] if is_lac_table else parameters['att']
            target_columns = target_columns_lac if is_lac_table else target_columns_att

            res = execute (conn, 'SHOW COLUMNS IN {source}', parameters)
            source_columns = [row[0].lower() for row in res]
            common_columns = [column for column in source_columns if column in target_columns]

            parameters['fields']  = ', '.join (common_columns)
            parameters['created'] = datetime.date.today().strftime ("%Y-%m-%d")

            message (2, 'Step  1 : Copying table {source_table}'.format (**parameters))

            execute (conn, """
            INSERT INTO {t} ({fields}, created)
            SELECT {fields}, '{created}'
            FROM {source}
            WHERE hsnr < 500000
            """, parameters)

        message (1, "Step  1 : Creating indices ...")
        create_indices (conn)

        execute (conn, """
        DROP FUNCTION IF EXISTS char_labez
        """, parameters)

        execute (conn, """
        CREATE FUNCTION char_labez (l INTEGER)
        RETURNS CHAR(3) DETERMINISTIC
        RETURN IF (l, CHAR (l + 96 using utf8), 'lac')
        """, parameters)

        execute (conn, """
        DROP FUNCTION IF EXISTS ord_labez
        """, parameters)

        execute (conn, """
        CREATE FUNCTION ord_labez (l CHAR(2))
        RETURNS INTEGER DETERMINISTIC
        RETURN ORD (l) - 96
        """, parameters)


def create_ms_pass_tables (dba, parameters):
    """ Create the Manuscripts, Passages and Nested Passages tables. """

    with dba.engine.begin () as conn:

        # The Manuscripts Table

        execute (conn, """
        TRUNCATE {ms}
        """, parameters)

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

        # The Passages Table

        execute (conn, """
        CREATE OR REPLACE TABLE {pass} (id INTEGER AUTO_INCREMENT PRIMARY KEY)
        SELECT DISTINCT buch, kapanf, versanf, wortanf, kapend, versend, wortend, anfadr, endadr
        FROM {att}
        ORDER BY anfadr, endadr DESC
        """, parameters)

        execute (conn, """
        CREATE INDEX Pass ON {pass} (anfadr, endadr)
        """, parameters)

        # The Nested Passages Table

        execute (conn, """
        CREATE OR REPLACE TABLE {npass}
        SELECT a.anfadr AS ianfadr, a.endadr AS iendadr, b.anfadr AS oanfadr, b.endadr AS oendadr
        FROM {pass} a
        JOIN {pass} b
        WHERE a.anfadr >= b.anfadr AND a.endadr <= b.endadr AND
          NOT (a.anfadr = b.anfadr AND a.endadr = b.endadr)
        """, parameters)

        # Set comp on nested variants.
        # We need this later when we insert the 'Fehlverse'.
        execute (conn, """
        ALTER TABLE {pass}
        ADD COLUMN comp BOOLEAN DEFAULT False,
        ADD COLUMN fehlvers BOOLEAN DEFAULT False
        """, parameters)

        execute (conn, """
        UPDATE {pass} p
        JOIN {npass} n
        ON p.anfadr = n.ianfadr AND p.endadr = n.iendadr
        SET comp = True
        """, parameters)

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
        WHERE hs REGEXP 'L1188s2.*' AND hsnr = 411881
        """, """
        UPDATE {att}
        SET hsnr = 411882
        WHERE hs REGEXP 'L1188s2.*'
        """, parameters)

        fix (conn, "Attestation of A != 'a'", """
        SELECT hs, labez, labezsuf, anfadr, endadr
        FROM {att}
        WHERE hs = 'A' AND labez REGEXP '^[b-y]'
        """, """
        UPDATE {att}
        SET labez = 'a'
        WHERE (hs, anfadr, endadr) = ('A', 50240012, 50240018)
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
            WHERE suffix2 REGEXP '\r'
            """, dict (parameters, t = t))

            # replace NULL fields with ''
            for col in N_FIELDS + NULL_FIELDS:
                execute (conn, """
                UPDATE {t}
                SET {col} = ''
                WHERE {col} IS NULL
                """, dict (parameters, t = t, col = col))

        # Fix inconsistencies in endadr between Att and Lac
        fix (conn, "Inconsistent chapter ends in Att and Lac", """
        SELECT kapanf, max (endadr) AS maxend
        FROM {att} AS a
        GROUP BY kapanf
        HAVING maxend NOT IN (
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
        WHERE korr REGEXP '^L'
        """, parameters)

        execute (conn, """
        UPDATE {att}
        SET korr = lekt, lekt = ''
        WHERE lekt REGEXP '[C*]'
        """, parameters)

        execute (conn, """
        UPDATE {att}
        SET korr = '*'
        WHERE korr = '' AND suffix2 REGEXP '[*]'
        """, parameters)

        execute (conn, """
        UPDATE {att}
        SET suff = 'S'
        WHERE suff = '' AND suffix2 REGEXP 's'
        """, parameters)

        execute (conn, """
        UPDATE {att}
        SET lekt = REGEXP_SUBSTR (suffix2, 'L[1-9]')
        WHERE lekt IN ('', 'L') AND suffix2 REGEXP 'L[1-9]'
        """, parameters)

        execute (conn, """
        UPDATE {att}
        SET korr = REGEXP_SUBSTR (suffix2, 'C[1-9*]')
        WHERE korr IN ('', 'C') AND suffix2 REGEXP 'C[1-9*]'
        """, parameters)

        execute (conn, """
        UPDATE {att}
        SET vl = REGEXP_SUBSTR (suffix2, 'T[1-9]')
        WHERE vl IN ('', 'T') AND suffix2 REGEXP 'T[1-9]'
        """, parameters)

        fix (conn, "Incompatible hs and suffix2 for T reading", """
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

        fix (conn, "Wrong labez", """
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
        res = execute (conn, """
        SELECT id, labez, labezsuf, CONCAT (hsnr, anfadr, endadr) AS k
        FROM {att}
        WHERE (hsnr, anfadr, endadr) IN (
          SELECT DISTINCT hsnr, anfadr, endadr
          FROM {att}
          WHERE hs REGEXP 'T[1-9]'
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
                    WHERE suffix2 REGEXP '{regexp}'
                  ) AS tmp
                )
                AND suffix2 NOT REGEXP '{regexp}'
                """, dict (parameters, t = t, regexp = regexp))

            execute (conn, """
            DELETE FROM {t}
            WHERE (lekt = 'L2' OR korr IN ('C', 'C1', 'C2', 'C3', 'A', 'K'))
              AND suffix2 NOT REGEXP 'C[*]'
            """, dict (parameters, t = t))

            execute (conn, """
            DELETE FROM {t}
            WHERE suffix2 REGEXP 'A|K|L2'
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

        for t in (parameters['att'], parameters['lac']):
            for regexp in ('C[1-9*]?', '[*]', '[LT][1-9]', 'V'):
                # FIXME: MariaDB specific function REGEXP_REPLACE
                execute (conn, """
                UPDATE {t}
                SET hs = REGEXP_REPLACE (hs, '(?<=[0-9s]){regexp}', '')
                WHERE hs REGEXP '(?<=[0-9s]){regexp}'
                """, dict (parameters, t = t, regexp = regexp))

                execute (conn, """
                UPDATE {t}
                SET suffix2 = REGEXP_REPLACE (suffix2, '{regexp}', '')
                WHERE suffix2 REGEXP '{regexp}'
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
        WHERE hs NOT REGEXP suffix2
        ORDER BY hs, anfadr
        """, parameters)

        # execute (conn, """
        # UPDATE {t}
        # SET hs = CONCAT (hs, suffix2)
        # WHERE hs NOT REGEXP CONCAT(suffix2, '$')
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

        # Save number of invariants per manuscript
        # execute (conn, """
        # INSERT INTO {inv} (hs, hsnr, n)
        #   SELECT hs, hsnr, count (*) as n
        #   FROM {att}
        #   WHERE (anfadr, endadr) IN (
        #     SELECT anfadr, endadr
        #     FROM {att}
        #     WHERE labez NOT REGEXP '^z' OR labezsuf NOT REGEXP 'f|o'
        #     GROUP BY anfadr, endadr, labez
        #     HAVING count (*) = 1
        #   )
        #   GROUP BY hs, hsnr
        # """, parameters)


        # We need a nested subquery to avoid MySQL limitations. See:
        # https://dev.mysql.com/doc/refman/5.7/en/subquery-restrictions.html
        execute (conn, """
        DELETE a
        FROM {att} a
        WHERE (anfadr, endadr) IN (
          SELECT anfadr, endadr FROM (
            SELECT DISTINCT anfadr, endadr, labez
            FROM {att}
            WHERE labez NOT REGEXP '^z' AND NOT (labez = 'a' AND labezsuf REGEXP 'f|o')
          ) AS b
          GROUP BY anfadr, endadr
          HAVING count (*) <= 1
        )
        """, parameters)


def step09 (dba, parameters):
    """Lacunae auffüllen

    Aus: prepare4cbgm_9.py

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

    with dba.engine.begin () as conn:

        # First clean up the lacunae table as any errors there will be multiplied by
        # this step.  Delete inner lacunae from nested lacunae.

        fix (conn, "nested lacunae", """
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

        # Create a 'zz' reading in att for each passage in a lacuna that doesn't
        # alrady have a text reading in att.

        message (2, "Step  9 : Add 'zz' readings for lacunae ...")

        execute (conn, """
        INSERT INTO {att} (buch, kapanf, versanf, wortanf, kapend, versend, wortend,
                              anfadr, endadr, hs, hsnr, anfalt, endalt, labez, labezsuf,
                              lemma, lesart)
        SELECT p.buch, p.kapanf, p.versanf, p.wortanf, p.kapend, p.versend, p.wortend,
               p.anfadr, p.endadr, lac.hs, lac.hsnr, p.anfadr, p.endadr, 'zz', 'lac',
               '', 'lac'
          FROM
            /* all passages */
            {pass} p

          JOIN
            /* all lacunae */
            {lac} lac

          ON p.anfadr >= lac.anfadr AND p.endadr <= lac.endadr

          LEFT JOIN
            /* negated join on all witnessed passages */
            {att} t

          ON lac.hs = t.hs AND p.anfadr = t.anfadr AND p.endadr = t.endadr

          WHERE t.id IS NULL

        """, parameters)


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

    message (1, "Step  9 : Create Labez Table ...")

    with dba.engine.begin () as conn:

        # First clean up the lacunae table as any errors there will be multiplied by
        # this step.  Delete inner lacunae from nested lacunae.

        fix (conn, "nested lacunae", """
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

        execute (conn, """
        TRUNCATE {labez}
        """, parameters)

        # unroll lacunae.  All lacunae get a labez of 0.
        execute (conn, """
        INSERT INTO {labez} (ms_id, pass_id, labez, labezsuf)
        SELECT ms.id, p.id, 0, ''
          FROM
            {lac} lac
          JOIN
            {pass} p
          JOIN
            {ms} ms

          ON p.anfadr >= lac.anfadr AND p.endadr <= lac.endadr
             AND ms.hsnr = lac.hsnr
        """, parameters)

        # copy labez eventually overwriting lacunae
        execute (conn, """
        REPLACE INTO {labez} (ms_id, pass_id, labez, labezsuf)
        SELECT ms.id, p.id, ord_labez (att.labez), labezsuf
          FROM
            {att} att
          JOIN
            {pass} p
          JOIN
            {ms} ms

          ON p.anfadr = att.anfadr AND p.endadr = att.endadr
             AND ms.hsnr = att.hsnr
        """, parameters)


        # fill with the labez of A
        execute (conn, """
        INSERT IGNORE INTO {labez} (ms_id, pass_id, labez, labezsuf)
        SELECT ms.id, p.id, ord_labez (att.labez), labezsuf
          FROM
            {att} att
          JOIN
            {pass} p
          JOIN
            {ms} ms

          ON p.anfadr = att.anfadr AND p.endadr = att.endadr
             AND att.hsnr = 0
        """, parameters)

        # finally fix the 'Fehlverse'
        #
        # As of here all Fehlverse are marked with the labez of manuscript 'A' which
        # may be incorrect.  Actually all Fehlverse are correctly marked 'zu' in
        # 'A', so we might get away with doing nothing.

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

        # fix 'z' readings
        execute (conn, """
        UPDATE {labez}
        SET labez = 0
        WHERE labez = 26
        """, parameters)


def step10 (dba, parameters):
    """Create positive apparatus

    Aus: prepare4cbgm_10.py

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

    with dba.engine.begin () as conn:

        execute (conn, """
        INSERT INTO {att} (hsnr, hs, anfadr, endadr, buch, kapanf, versanf, wortanf,
                              kapend, versend, wortend, labez, labezsuf, anfalt, endalt,
                              lesart, base, comp)
        SELECT hs.hsnr, hs.hs, a.anfadr, a.endadr, a.buch, a.kapanf, a.versanf, a.wortanf,
               a.kapend, a.versend, a.wortend, a.labez, a.labezsuf, a.anfalt, a.endalt,
               a.lesart, a.base, a.comp
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

        debug (conn, "Manuscripts with duplicated passages", """
        SELECT hs, anfadr, endadr FROM {att} GROUP BY hs, anfadr, endadr HAVING COUNT (*) > 1
        """, parameters)

        parameters['fehlverse'] = db.FEHLVERSE
        execute (conn, """
        UPDATE {att}
        SET labez = 'zu', lesart = ''
        WHERE comp = 'x' AND base = 'a' AND {fehlverse}
        """, parameters)


def step11 (dba, parameters):
    """Create ActsMsList

    Aus: prepare4cbgm_11.py

        Handschriftenliste 'ActsMsList' anlegen.  Die Handschrift bekommt in dem
        entsprechenden Kapitel eine 1, wenn sie dort Text enthält.  Mit anderen
        Worten: Sie bekommt eine 0, wenn das ganze Kapitel fehlt.  Es wird hier
        auf die systematische Lückenliste zurückgegriffen.  Kapitel, die keine
        echte Variante enthalten, müssen ebenfalls eine 0 erhalten.

        Die Handschriftenliste darf erst *nach* dem Auffüllen der a-Bezeugung
        gerechnet werden, daher gehört das Skript hier an den Schluss der
        Vorbereitungen!

    """

    message (1, "Step 11 : Create ActsMsList ...")



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

    with dba.engine.begin () as conn:

        execute (conn, """
        TRUNCATE {vp}
        """, parameters)

        execute (conn, """
        INSERT INTO {vp} (anfadr, endadr)
        SELECT DISTINCT anfadr, endadr
        FROM {att}
        """, parameters)

        execute (conn, """
        TRUNCATE {rdg}
        """, parameters)

        execute (conn, """
        INSERT INTO {rdg} (anfadr, endadr, labez, labezsuf, lesart)
        SELECT DISTINCT anfadr, endadr, labez, labezsuf, lesart
        FROM {att}
        WHERE labez NOT REGEXP '^z[u-z]'
        """, parameters)

        # delete all readings with labezsuf if there is an equivalent reading
        # without labezsuf

        execute (conn, """
        DELETE FROM {rdg}
        WHERE (anfadr, endadr, labez) IN (
          SELECT anfadr, endadr, labez FROM (
            SELECT DISTINCT anfadr, endadr, labez
            FROM {rdg}
            WHERE labezsuf = ''
          ) AS tmp
        ) AND labezsuf <> ''
        """, parameters)

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

        execute (conn, """
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

        # FIXME: the witn table is superfluous as it contains the same rows as att

        execute (conn, """
        TRUNCATE {witn}
        """, parameters)

        execute (conn, """
        INSERT INTO {witn} (anfadr, endadr, labez, labezsuf, hsnr, hs)
        SELECT DISTINCT anfadr, endadr, labez, labezsuf, hsnr, hs
        FROM {att}
        """, parameters)



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

    with dba.engine.begin () as conn:

        parameters['byzlist'] = db.BYZ_HSNR

        # FIXME: we don't really need this table
        execute (conn, """
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

        execute (conn, """
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

        execute (conn, """
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

        # debug info

        debug (conn, "Byzantine Variant Passages", """
        SELECT bzdef, count (*) AS anzahl FROM {vp} GROUP BY bzdef
        """, parameters)

        debug (conn, "Byzantine Readings", """
        SELECT bz, count (*) AS anzahl FROM {rdg} GROUP BY bz
        """, parameters)

        # mindestens 6
        execute (conn, """
        UPDATE {rdg}
        SET byz = 'B'
        WHERE bzdef = 7 AND bz >= 6
        """, parameters)

        # 5 und 2 unterschiedliche
        execute (conn, """
        UPDATE {rdg}
        SET byz = 'B'
        WHERE (anfadr, endadr, bz) IN (
          SELECT anfadr, endadr, 5 FROM (
            SELECT anfadr, endadr
            FROM {rdg}
            WHERE bzdef = 7 AND bz IN (5, 1)
            GROUP BY anfadr, endadr
            HAVING count (*) <= 3
          ) AS t
        )
        """, parameters)

        # Build the fake manuscript 'MT' that contains our reconstructed Byzantine
        # text

        execute (conn, """
        DELETE FROM {att} WHERE hs = 'MT'
        """, parameters)

        execute (conn, """
        INSERT INTO {att} (hsnr, hs, anfadr, endadr, buch, kapanf, versanf, wortanf,
                           kapend, versend, wortend, labez, labezsuf, lesart)
        SELECT 1, 'MT', a.anfadr, a.endadr, a.buch, a.kapanf, a.versanf, a.wortanf,
               a.kapend, a.versend, a.wortend, r.labez, r.labezsuf, r.lesart
        FROM {target_db}.Passages a
        JOIN {rdg} r
        ON (a.anfadr, a.endadr, 'B') = (r.anfadr, r.endadr, r.byz)
        """, parameters)

        execute (conn, """
        INSERT INTO {att} (hsnr, hs, anfadr, endadr, buch, kapanf, versanf, wortanf,
                           kapend, versend, wortend, labez, labezsuf, lesart)
        SELECT 1, 'MT', a.anfadr, a.endadr, a.buch, a.kapanf, a.versanf, a.wortanf,
               a.kapend, a.versend, a.wortend, 'zz', '', 'lac'
        FROM {target_db}.Passages a
        LEFT JOIN {rdg} r
        ON (a.anfadr, a.endadr, 'B') = (r.anfadr, r.endadr, r.byz)
        WHERE r.byz IS NULL
        """, parameters)



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

    with dba.engine.begin () as conn:

        # fill with hs, hsnr, chapter

        execute (conn, """
        TRUNCATE {listval}
        """, parameters)

        execute (conn, """
        INSERT INTO {listval} (hs, hsnr, chapter)
        SELECT DISTINCT hs, hsnr, 0
        FROM {att}
        WHERE labez NOT REGEXP '^z[u-z]'
        """, parameters)

        execute (conn, """
        INSERT INTO {listval} (hs, hsnr, chapter)
        SELECT DISTINCT hs, hsnr, kapanf
        FROM {att}
        WHERE labez NOT REGEXP '^z[u-z]'
        """, parameters)

        # sumtxt

        execute (conn, """
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

        execute (conn, """
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

        execute (conn, """
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

        execute (conn, """
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

        execute (conn, """
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

        execute (conn, """
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

        execute (conn, """
        UPDATE {listval}
        SET qmt = (uemt * 100.0) / sumtxt
        WHERE sumtxt > 0
        """, parameters)


def copy_genealogical_data (dba, parameters):
    """Copy / update genealogical data

    Aus: VGA/Att2CBGM.pl, VGA/PortCBGMInfo.pl

    """

    message (1, "Step 31 : Copying genealogical data ...")

    with dba.engine.begin () as conn:
        parameters['fields'] = db.CREATE_TABLE_LOCSTEMED
        execute (conn, 'CREATE OR REPLACE TABLE {locstemed} {fields}', parameters)
        execute (conn, 'CREATE OR REPLACE TABLE {locstemedtmp} {fields}', parameters)

        res = execute (conn, """SHOW TABLES FROM {source_db} LIKE 'Acts__GVZ'""", parameters)
        for row in res:
            parameters['source_table'] = row[0]
            parameters['source'] = '{source_db}."{source_table}"'.format (**parameters)

            execute (conn, """
            INSERT INTO {locstemed} (begadr, endadr, varid, varnew, s1)
	    SELECT DISTINCT anfadr, endadr, labez, labez, IF (labez = 'a', '*', 'a')
	    FROM {source}
            """, parameters)

        res = execute (conn, """SHOW TABLES FROM {src_vg_db} LIKE 'LocStemEdAct__'""", parameters)
        for row in res:
            parameters['source_table'] = row[0]
            parameters['source'] = '{src_vg_db}."{source_table}"'.format (**parameters)

            execute (conn, """
            INSERT INTO {locstemedtmp} (begadr, endadr, varid, varnew, s1, s2, prs1, prs2, "check", check2, w)
            SELECT begadr, endadr, varid, varnew, s1, s2, prs1, prs2, "check", check2, w
            FROM {source}
            """, parameters)

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
        DELETE d FROM {locstemedtmp} d
        WHERE NOT EXISTS (
          SELECT anfadr, endadr FROM Passages p WHERE (d.begadr, d.endadr) = (p.anfadr, p.endadr)
        )
        """, parameters)

        # overwrite with changed passages
        execute (conn, """
        CREATE UNIQUE INDEX locstemed_varnew ON {locstemed} (begadr, endadr, varnew)
        """, parameters)

        execute (conn, """
        INSERT IGNORE INTO {locstemed} (begadr, endadr, varid, varnew, s1, s2, prs1, prs2, "check", check2, w)
        SELECT begadr, endadr, varid, varnew, s1, s2, prs1, prs2, "check", check2, w FROM {locstemedtmp}
        """, parameters)

        # preprocess source readings
        #
        # We want to quickly retrieve all source readings, ie. to traverse the
        # graph of readings from any reading back to the 'a' reading.  Since mysql
        # is the only database that does not implement WITH RECURSIVE we have to
        # preprocess the data in order to do this:
        #
        # We add a 'prior' field to the LocStemEd table, which is a bitmask that
        # has one bit set for each prior reading, eg. 'lac' => 1, 'a' => 2, 'b'
        # => 4, ...  If 'd' had a prior reading of 'c' and 'c' had a prior reading
        # of 'a' then the bitmask for 'd' would be 10 ('c' + 'a').

        res = execute (conn, """
        SELECT begadr, endadr, varid, varnew, s1, s2 FROM {locstemed}
        WHERE s1 != '*' AND s1 != '?' AND varnew NOT REGEXP '^z'
        ORDER BY begadr, endadr DESC, varnew
        """, parameters)

        Variant = collections.namedtuple ('Variant', 'begadr, endadr, varid, varnew, s1, s2')

        update = []
        for key, group in itertools.groupby (res, operator.itemgetter (0, 1)):
            G = nx.DiGraph ()
            rows = list (map (Variant._make, group))

            for row in rows:
                G.add_edge (row.varnew, row.s1)
                if row.s2:
                    G.add_edge (row.varnew, row.s2)

            if not nx.is_directed_acyclic_graph (G):
                message (1, "Error: Not a DAG at variant {begadr}/{endadr}".format (row))
                continue

            for row in rows:
                prior_mask = 0
                for (s, d) in nx.bfs_edges (G, row.varnew):
                    if s[0] != d: # exclude self-loops, which may happen if 'a' reading is prior to 'af'.
                        prior_mask |= 1 << (ord (d[0]) - 96) # 'a' => 2, 'b' => 4, ...
                if prior_mask > 0:
                    update.append (
                        {
                            'begadr' : row.begadr,
                            'endadr' : row.endadr,
                            'varnew' : row.varnew,
                            'prior'  : prior_mask
                        }
                    )

        message (3, "Updating rows {upd}".format (upd = update[:100]))

        # do not use row syntax (a, b) = (:a, :b) here, it is awfully slow
        res = executemany (conn, """
        UPDATE {locstemed}
        SET prior = :prior
        WHERE begadr = :begadr AND endadr = :endadr AND varnew = :varnew
        """, parameters, update)



Manuscript = collections.namedtuple ('Manuscript', 'hs hsnr')
Chapter    = collections.namedtuple ('Chapter',    'n start end')

class Bag (object):
    """ Holds some values for us. """

    n_mss = 0               # No. of manuscripts
    n_passages = 0          # No. of passages
    n_var_passages = 0      # No. of variant passages
    n_chapters = 0          # No. of chapters
    mss = None              # list of named tuple Manuscript
    passages = None         # list of passages
    chapters = None         # list of named tuple Chapter
    var_passages = None     # list of indices of variant passages only
    labez_matrix = None     # hs x passages matrix of labez
    var_labez_matrix = None # hs x variant passages matrix of labez
    affinity_matrix = None  # hs x hs matrix of similarity measure


def create_labez_matrix (dba, parameters, val):
    """Create the labez matrix.

    Create a matrix of manuscripts x passages.  Each entry represents one
    reading: 0 = lacuna, 1 = 'a', 2 = 'b', ...

    """

    message (1, "Step 32 : Loading labez matrix ...")

    with dba.engine.begin () as conn:

        np.set_printoptions (threshold = 30)

        # get no. of passages
        res = execute (conn, "SELECT anfadr, endadr FROM {pass} ORDER BY anfadr, endadr DESC", parameters)
        val.n_passages = res.rowcount
        val.passages   = ["%s-%s" % (x[0], x[1]) for x in res]

        # get manuscript names and numbers
        res = execute (conn, "SELECT hs, hsnr FROM {ms} ORDER BY id", parameters)
        val.n_mss = res.rowcount
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

        # First initialize all manuscripts in the matrix to the labezs of Manuscript
        # A ...
        labez_matrix = np.ones ((val.n_mss, val.n_passages), dtype = int)

        res = execute (conn, """
        SELECT pass_id - 1 as pass, labez
        FROM {labez}
        WHERE ms_id = 1 AND labez <> 1
        """, parameters)

        for row in res:
            labez_matrix[:, row[0]] = row[1]

        # ... then overwrite the matrix with the labezs from actual manuscripts
        res = execute (conn, """
        SELECT ms_id - 1 as ms, pass_id - 1 as pass, labez
        FROM {labez}
        """, parameters)

        for row in res:
            labez_matrix[row[0], row[1]] = row[2]

        # Get ids of variant passages
        res = execute (conn, """
        SELECT a.id - 1
        FROM (
          SELECT DISTINCT p.id, labez
          FROM {att} AS att
          JOIN {pass} AS p
          ON p.anfadr = att.anfadr AND p.endadr = att.endadr
          WHERE labez NOT REGEXP '^z' AND labezsuf NOT REGEXP 'f|o'
        ) AS a
        GROUP BY a.id
        HAVING count (*) > 1
        """, parameters)

        val.var_pass = np.fromiter ((row[0] for row in res), np.int)
        val.n_var_passages = len (val.var_pass)
        val.var_labez_matrix = labez_matrix.take (val.var_pass, 1)
        val.labez_matrix = labez_matrix

        print (val.n_mss)
        print (val.n_passages)
        print (val.labez_matrix.shape)
        print (val.n_var_passages)
        print (val.var_labez_matrix.shape)

        message (1, "Step 32 : Building Byzantine text ...")

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
        byz_labez_matrix = labez_matrix.take (byz_ids, 0)
        # np.set_printoptions (threshold = 100000)
        # print (byz_labez_matrix)
        # np.set_printoptions (threshold = 1000)

        # Group the labez at each passage
        byz_bincount = np.apply_along_axis (np.bincount, 0, byz_labez_matrix, minlength = 27)
        print (byz_bincount)

        # Calculate the Byzantine labez for each passage
        byz_text = np.zeros (val.n_passages, dtype = int)

        for i, bc in enumerate (byz_bincount.T):
            for j, b in enumerate (bc):
                if b >= 6:
                    # must be 7 or 6+1
                    byz_text[i] = j
                    continue
                if b == 5 and 2 not in bc[1:]:
                    # must be 5+1+1 or 5+1
                    byz_text[i] = j
                    continue

        # print ("Byz: ", byz_text)

        # Insert the Byz text into the matrix
        val.labez_matrix[1] = byz_text

        # Insert the Byz text into labez table
        execute (conn, """
        DELETE FROM {labez}
        WHERE ms_id = 2
        """, parameters)
        param_array = []
        for i, labez in enumerate (byz_text):
            param_array.append ({ 'pass_id' : i + 1, 'labez' : labez })
        executemany (conn, """
        INSERT INTO {labez} (ms_id, pass_id, labez, labezsuf)
        VALUES (2, :pass_id, :labez, '')
        """, parameters, param_array)


        # Boolean matrix ms x pass set where passage is defined
        val.def_matrix = np.asmatrix (np.zeros_like (val.labez_matrix, dtype = int))
        val.def_matrix[val.labez_matrix != 0] = 1

        # Length of manuscripts (no. of defined passages)
        val.ms_length = val.def_matrix * np.ones ((val.n_passages, 1), dtype = int)
        val.ms_length = val.ms_length.A[:, 0]
        print ("Manuscript Length Array: ", val.ms_length)

        # debug plot the matrix
        ticks_labels_x = plot.passages_labels (val.passages)
        ticks_labels_y = plot.mss_labels (val.mss)

        plot.plt.figure (1)
        plot.heat_matrix (val.def_matrix, "Manuscript Definition Matrix",
                          ticks_labels_x, ticks_labels_y, plot.colormap_bw ())


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

    message (1, "Step 33 : Calculating mss similarity ...")

    with dba.engine.begin () as conn:

        # load local stem for each passage
        res = execute (conn, """
        SELECT p.id - 1 as pass_id, ord_labez (varid) as varid, prior
        FROM {locstemed} l
        JOIN {pass} p
          ON (l.begadr, l.endadr) = (p.anfadr, p.endadr)
        WHERE prior > 0
        """, parameters)

        # Matrix passage x labez containing bitmask of prior readings, 'a' = 2
        prior_matrix = np.zeros ((val.n_passages, MAX_LABEZ), dtype = np.uint32)
        for row in res:
            prior_matrix[row[0], row[1]] = row[2]

        # Matrix chapter x ms x ms with count of the passages that are defined in both mss
        val.and_matrix = np.zeros ((val.n_chapters, val.n_mss, val.n_mss), dtype = np.uint16)

        # Matrix chapter x ms x ms with count of the passages that are defined in either ms
        val.or_matrix  = np.zeros ((val.n_chapters, val.n_mss, val.n_mss), dtype = np.uint16)

        # Matrix chapter x ms x ms with count of the passages that are equal in both mss
        val.eq_matrix  = np.zeros ((val.n_chapters, val.n_mss, val.n_mss), dtype = np.uint16)

        # Matrix chapter x ms x ms with count of the passages that are older in ms1 than in ms2
        val.older_matrix  = np.zeros ((val.n_chapters, val.n_mss, val.n_mss), dtype = np.uint16)

        # pre-genealogical coherence (outputs symmetrical matrices)
        # loop over all mss O(n_mss² * n_chapters * n_passages)

        message (1, "          Calculating mss similarity pre-co ...")
        for j in range (0, val.n_mss):
            labezj = val.labez_matrix[j]
            defj   = val.def_matrix[j]

            for k in range (j + 1, val.n_mss):
                labezk = val.labez_matrix[k]
                defk   = val.def_matrix[k]

                def_and     = np.logical_and (defj, defk)
                def_or      = np.logical_or  (defj, defk)
                labez_eq    = np.logical_and (def_and, np.equal (labezj, labezk))

                for i, chapter in enumerate (val.chapters):
                    val.and_matrix[i,j,k] = val.and_matrix[i,k,j] = np.sum (def_and[0, chapter.start:chapter.end])
                    val.or_matrix[i,j,k]  = val.or_matrix[i,k,j]  = np.sum (def_or[0, chapter.start:chapter.end])
                    val.eq_matrix[i,j,k]  = val.eq_matrix[i,k,j]  = np.sum (labez_eq[0, chapter.start:chapter.end])

        # Matrix ms x ms with count of the passages that are different in both mss
        message (2, "          Calculating diff and quotient matrices ...")
        val.diff_matrix = val.and_matrix - val.eq_matrix

        # calculate
        with np.errstate (divide = 'ignore', invalid = 'ignore'):
            val.quotient_matrix = val.eq_matrix / val.and_matrix
            val.quotient_matrix[val.and_matrix == 0] = 0.0

        # genealogical coherence (outputs asymmetrical matrices)
        # loop over all mss O(n_mss² * n_chapters * n_passages)

        message (1, "          Calculating mss similarity post-co ...")
        r = np.arange (0, val.n_passages) # for fancy indexing
        for j in range (0, val.n_mss):
            labezj = np.left_shift (1, val.labez_matrix[j]) # 'a' => 2
            for k in range (0, val.n_mss):
                labezk = val.labez_matrix[k] # b

                # prior_matrix['b'] == 2
                # and == 2

                # set bit if the reading of j is prior to the reading of k
                labez_is_older = np.bitwise_and (labezj, prior_matrix[r, labezk]) > 0

                if k == 0 and np.any (labez_is_older):
                    message (1, "Error labez older than A in msid %d in passages: %s"
                             % (j, np.nonzero (labez_is_older)))

                for i, chapter in enumerate (val.chapters):
                    val.older_matrix[i,j,k] = np.sum (labez_is_older[chapter.start:chapter.end])

        # debug
        if 0:
            #plot.heat_matrix (eq_matrix,  "No. of Equal Passages", )
            #plot.heat_matrix (and_matrix, "No. of Passages Defined in Both Manuscripts", )
            ticks_labels = plot.mss_labels (val.mss)

            for i, chapter in enumerate (val.chapters):
                plot.plt.figure (figsize = (15, 10), dpi = 300)
                message (2, "          Plotting Chapter %d ..." % i)
                plot.heat_matrix (val.quotient_matrix[i],
                                  "Similarity of Manuscripts - Chapter %d" % chapter.n,
                                  ticks_labels, ticks_labels, plot.colormap_affinity ())
                plot.plt.savefig ('output/affinity-%02d.svg' % i, bbox_inches='tight')
                plot.plt.close ()

        # np.fill_diagonal (val.quotient_matrix, 0.0) # remove affinity to self

        message (2, "          Updating Manuscripts table ...")
        param_array = []
        for i, length in enumerate (val.ms_length):
            param_array.append ( { 'id' : i + 1, 'length' : length } )
        executemany (conn, """
        UPDATE {ms} SET length = :length
        WHERE id = :id
        """, parameters, param_array)

        message (2, "          Filling Affinity table ...")
        execute (conn, "TRUNCATE {aff}", parameters)

        for i, chapter in enumerate (val.chapters):
            param_array = []
            for j, ms1 in enumerate (val.mss):
                for k, ms2 in enumerate (val.mss):
                    param_array.append (
                        {
                            'id1' :      j + 1,
                            'id2' :      k + 1,
                            'chapter' :  chapter.n,
                            'common' :   val.and_matrix[i,j,k],
                            'equal' :    val.eq_matrix[i,j,k],
                            'older' :    val.older_matrix[i,j,k],
                            'newer' :    val.older_matrix[i,k,j],
                            'affinity' : val.quotient_matrix[i,j,k]
                        }
                    )

            executemany (conn, """
            INSERT INTO {aff} (id1, id2, chapter, common, equal, older, newer, affinity)
            VALUES (:id1, :id2, :chapter, :common, :equal, :older, :newer, :affinity)
            """, parameters, param_array)

        print ("eq\n",    val.eq_matrix)
        print ("older\n", val.older_matrix)
        print ("diff\n",  val.diff_matrix)
        print ("and\n",   val.and_matrix)
        print ("or\n",    val.or_matrix)
        print ("quot\n",  val.quotient_matrix)


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

        # Build Gephi nodes table.  Every ms gets to be a node.  Simple.
        param_array = []
        for i in range (0, val.n_mss):
            hs = val.mss[i].hs
            hsnr = val.mss[i].hsnr
            size = val.ms_length[i]
            color = '128,128,128'
            if hsnr < 400000:
                color = '0,255,0'
            if hsnr < 300000:
                color = '128,128,255'
            if hsnr < 200000:
                color = '255,255,128'
            if hsnr < 100000:
                color = '255,0,0'
            param_array.append ( {
                'id'        : hsnr,
                'label'     : hs,
                'color'     : color,
                'nodecolor' : color,
                'nodesize'  : size
            } )

        executemany (conn, """
        INSERT INTO {g_nodes} (id, label, color, nodecolor, nodesize)
        VALUES (:id, :label, :color, :nodecolor, :nodesize)
        """, parameters, param_array)

        # Build Gephi edges table.  Needs brains.  Creating an edge between every 2
        # mss will not give a very meaningful graph.  We have to keep only the most
        # significant edges.  But what is significant?

        # We rank the neighbors of each ms by similarity and keep only the X most
        # similar ones.
        keep = 20
        rank_matrix = np.argsort (val.quotient_matrix[0], axis = 1)
        rank_matrix = rank_matrix[0:, -keep:]  # keep the most similar entries
        # Now we have the indices of the X most similar mss.

        param_array = []
        qq = math.log (val.n_passages)
        for i in range (2, val.n_mss): # do not include 'A' and 'MT'
            hs_src = val.mss[i].hsnr
            for j in range (0, keep):
                k = rank_matrix[i, j]
                hs_dest = val.mss[k].hsnr
                q = val.quotient_matrix[0, i, k] * math.log (max (1.0, val.and_matrix[0, i, k])) / qq
                param_array.append ( {
                    'id'     : "%s-%s" % (hs_src, hs_dest),
                    'source' : hs_src,
                    'target' : hs_dest,
                    'weight' :q
                } )

        executemany (conn, """
        INSERT INTO {g_edges} (id, source, target, weight)
        VALUES (:id, :source, :target, :weight)
        """, parameters, param_array)

        # np.savetxt ('affinity.csv', val.quotient_matrix)


def print_stats (dba, parameters):

    with dba.engine.begin () as conn:

        res = execute (conn, "SELECT count(distinct hs) FROM {att}", parameters)
        hs = res.scalar ()
        message (1, "hs       = {cnt}".format (cnt = hs))

        res = execute (conn, "SELECT count(distinct anfadr, endadr) FROM {att}", parameters)
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
        SELECT sum(pas_cnt * ch.ms_cnt)

        FROM
          (select kapanf, count(distinct anfadr, endadr) as pas_cnt FROM {att} GROUP BY kapanf) AS pas

        JOIN
          (select kapanf, count(distinct hs) as ms_cnt FROM {att} GROUP BY kapanf) AS ch

        ON ch.kapanf = pas.kapanf

        """, parameters)
        pas = res.scalar ()

        message (1, "chap * ms * pas    = {cnt}".format (cnt = pas))


if __name__ == '__main__':

    parser = argparse.ArgumentParser (description='Prepare a new database for CBGM')

    parser.add_argument ('source_db', metavar='SOURCE_DB',    help='the source ECM database (required)')
    parser.add_argument ('target_db', metavar='TARGET_DB',    help='the target ECM database (required)')
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
    v = Bag ()

    dba = db.DBA (args.profile, args.target_db)

    try:
        for step in range (args.range[0], args.range[1] + 1):
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
                    print_stats (dba, parameters)
                continue
            if step == 8:
                step08 (dba, parameters)
                if args.verbose >= 1:
                    print_stats (dba, parameters)
                continue
            if step == 10:
                #step10 (dba, parameters)
                continue
            if step == 11:
                #step11 (dba, parameters)
                continue
            if step == 20:
                #step20 (dba, parameters)
                continue
            if step == 21:
                #step21 (dba, parameters)
                continue
            if step == 22:
                #step22 (dba, parameters)
                continue

            if step == 31:
                create_ms_pass_tables (dba, parameters)
                create_labez_table (dba, parameters)
                if args.verbose >= 1:
                    print_stats (dba, parameters)
                continue
            if step == 32:
                copy_genealogical_data (dba, parameters)
                continue
            if step == 33:
                create_labez_matrix (dba, parameters, v)
                continue
            if step == 34:
                calculate_mss_similarity (dba, parameters, v)
                affinity_to_gephi (dba, parameters, v)
                continue

    except KeyboardInterrupt:
        execute (dba.connection ('ROLLBACK'))

    dba.connection.close ()

    message (1, "          Done")
