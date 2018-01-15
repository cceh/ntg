# -*- encoding: utf-8 -*-

"""Prepare the database for CBGM

This script converts the apparatus tables used in the production of Nestle-Aland
into tables suitable for doing CBGM:

- copy the data from multiple mysql tables to a single postgres table
- remove unwanted readings
- build a positive apparatus
- calculate the pre-coherence similarity of manuscripts
- calculate the post-coherence ancestrality of manuscripts

"""

from __future__ import print_function
from __future__ import unicode_literals

import argparse
import collections
import datetime
import html
import itertools
import logging
import math
import operator
import os
import re
import sys

import networkx as nx
import numpy as np
import sqlalchemy

from ntg_common import db
from ntg_common import tools
from ntg_common import db_tools
from ntg_common.db_tools import execute, executemany, executemany_raw, warn, debug, fix
from ntg_common.tools import log
from ntg_common.config import args

PLOT = 0 # plot pretty pictures
if PLOT:
    from ntg_common import plot

NULL_FIELDS = 'lemma lesart labezsuf'.split ()
""" Fields to look for data entry error NULL, and change it into '' """

NULL_N_FIELDS = 'base comp comp1 komm kontrolle korr lekt over over1 suff suffix2 vid vl'.split ()
""" Fields to look for data entry error 'N' and NULL, and change them into '' """


def copy_table (conn, source_table, dest_table):
    """ Make a copy of a table. """

    execute (conn, """
    DROP TABLE IF EXISTS {dest_table};
    SELECT * INTO {dest_table} FROM {source_table}
    """, dict (parameters, dest_table = dest_table, source_table = source_table))


def copy_table_fdw (conn, fdw, source_table, dest_table):
    """ Make a copy of a table. """

    execute (conn, """
    DROP TABLE IF EXISTS {dest_table};
    """, dict (parameters, dest_table = dest_table))

    execute (conn, """
    SELECT * INTO {dest_table} FROM  {fdw}."{source_table}"
    """, dict (parameters, fdw = fdw, dest_table = dest_table, source_table = source_table))


def concat_tables (conn, meta, dest_table, fdw, source_tables):
    """Copy 28 tables into one for easier debugging."""

    source_table = source_tables % '01'

    execute (conn, """
    DROP TABLE IF EXISTS {dest_table}
    """, dict (parameters, dest_table = dest_table))

    execute (conn, """
    CREATE TABLE {dest_table} ( LIKE {fdw}."{source_table}" )
    """, dict (parameters, dest_table = dest_table, source_table = source_table, fdw = fdw))

    source_model = sqlalchemy.Table (source_table, meta, autoload = True)
    columns = [column.name for column in source_model.columns]

    for column in columns:
        if column != column.lower ():
            execute (conn, 'ALTER TABLE {dest_table} RENAME COLUMN "{source_column}" TO "{dest_column}"',
                     dict (parameters, dest_table = dest_table, source_column = column, dest_column = column.lower ()))

    table_mask = re.compile ('^' + (source_tables % r'\d\d') + '$')
    for source_table in sorted (meta.tables.keys ()):
        if not table_mask.match (source_table):
            continue
        log (logging.INFO, "        : Copying table %s" % source_table)

        # some tables in att do not contain the field 'fehler'
        source_model = sqlalchemy.Table (source_table, meta, autoload = True)
        columns = [column.name for column in source_model.columns]

        source_columns = ['"' + column + '"'          for column in columns]
        dest_columns   = ['"' + column.lower () + '"' for column in columns]

        rows = execute (conn, """
        INSERT INTO {dest_table} ({dest_columns})
        SELECT {source_columns}
        FROM {fdw}."{source_table}"
        """, dict (parameters, source_table = source_table, dest_table = dest_table, fdw = fdw,
                   source_columns = ', '.join (source_columns),
                   dest_columns = ', '.join (dest_columns)))


def step01 (dba, dbb, parameters):
    """Copy tables to new database

    Copy the (28 * 2) mysql tables to 2 tables in a new postgres database.  Do
    *not* copy versions and patristic manuscripts.

    """

    log (logging.INFO, "        : Copying tables ...")

    dba_meta = sqlalchemy.schema.MetaData (bind = dba.engine)
    dba_meta.reflect ()

    with dbb.engine.begin () as dest:
        concat_tables (dest, dba_meta, 'original_att', 'app_fdw', 'Acts%sGVZ')
        concat_tables (dest, dba_meta, 'original_lac', 'app_fdw', 'Acts%sGVZlac')

    att_model = sqlalchemy.Table ('att', db.Base.metadata)
    lac_model = sqlalchemy.Table ('lac', db.Base.metadata)

    dest_columns_att = set ([c.name.lower () for c in att_model.columns])
    dest_columns_lac = set ([c.name.lower () for c in lac_model.columns])

    # these columns get special treatment
    dest_columns_att -= set (('id', 'created'))
    dest_columns_lac -= set (('id', 'created'))

    dbb_meta = sqlalchemy.schema.MetaData (bind = dbb.engine)
    dbb_meta.reflect ()

    with dbb.engine.begin () as dest:
        for source_table in ('original_att', 'original_lac'):
            is_lac_table = source_table.endswith ('lac')

            dest_table   = 'lac' if is_lac_table else 'att'
            dest_columns = dest_columns_lac  if is_lac_table else dest_columns_att

            source_model = sqlalchemy.Table (source_table, dbb_meta, autoload = True)
            columns = [column.name for column in source_model.columns if column.name.lower () in dest_columns]
            source_columns = ['"' + column + '"' for column in columns]
            dest_columns   = [column.lower ()    for column in columns]

            log (logging.INFO, '          Copying table %s' % source_table)

            rows = execute (dest, """
            INSERT INTO {dest_table} ({dest_columns}, irange, created)
            SELECT {source_columns}, int4range (anfadr, endadr + 1), '{created}'
            FROM {source_table} s
            WHERE hsnr < 500000 AND endadr >= anfadr
            ON CONFLICT DO NOTHING
            """, dict (parameters, source_table = source_table, dest_table = dest_table,
                       source_columns = ', '.join (source_columns),
                       dest_columns = ', '.join (dest_columns),
                       created = datetime.date.today().strftime ("%Y-%m-%d")))


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

    with dba.engine.begin () as conn:

        # make a backup of the original labez
        execute (conn, """
        UPDATE att
        SET labezorig = labez, labezsuforig = labezsuf
        """, parameters)

        execute (conn, """
        UPDATE att
        SET lesart = NULL
        WHERE lesart = ''
        """, parameters)

        fix (conn, "Wrong hs", """
        SELECT hs, hsnr, suffix2, anfadr, endadr
        FROM att
        WHERE hs = 'L156s1'
        """, """
        UPDATE att
        SET hs = 'L156s', suffix2 = 's'
        WHERE hs = 'L156s1' AND anfadr = 50311014 AND endadr = 50311014
        """, parameters)

        # fix (conn, "Wrong hsnr Ph3", """
        # SELECT DISTINCT hs, hsnr, adr2chapter (anfadr)
        # FROM att
        # WHERE hs ~ '^L1188s2' AND hsnr = 411881
        # """, """
        # UPDATE att SET hsnr = 411881 WHERE hs ~ '^L1188s1';
        # UPDATE att SET hsnr = 411882 WHERE hs ~ '^L1188s2';
        # """, parameters)

        fix (conn, "Wrong hsnr Ph4", """
        SELECT DISTINCT hs, hsnr, adr2chapter (anfadr)
        FROM att
        WHERE hs = 'L1188' AND hsnr != 411880
           OR hs != 'L1188' AND hsnr = 411880
        """, """
        UPDATE att SET hsnr = 411881 WHERE hs ~ '^L1188s';
        UPDATE att SET hsnr = 411880 WHERE hs = 'L1188';
        UPDATE lac SET hsnr = 411881, hs = REPLACE (hs, 's2', 's') WHERE hs ~ '^L1188s2';
        UPDATE lac SET hsnr = 411880, hs = REPLACE (hs, 's1', '')  WHERE hs ~ '^L1188s1';
        UPDATE lac SET hsnr = 411881, hs = 'L1188s' WHERE hs = 'L1188S';
        """, parameters)

        fix (conn, "Attestation of A != 'a'", """
        SELECT hs, labez, labezsuf, anfadr, endadr
        FROM att
        WHERE hs = 'A' AND labez ~ '^[b-y]'
        """, """
        UPDATE att
        SET labez = 'a', labezsuf = ''
        WHERE (hs, anfadr, endadr) = ('A', 50240012, 50240018)
        """, parameters)

        # Passages not in A
        fix (conn, "Passages not in A", """
        SELECT DISTINCT anfadr, endadr
        FROM att
        WHERE (anfadr, endadr) NOT IN (
          SELECT anfadr, endadr
          FROM att
          WHERE hs = 'A'
        )
        """, """
        INSERT INTO att (hsnr, hs, anfadr, endadr, labez, irange)
        VALUES (0, 'A', 51528017, 51528017, 'a', int4range (51528017, 51528017 + 1))
        """, parameters)

        # Alle Fehlverse in A mit labez 'zu'?
        fix (conn, "Fehlverse in A with labez <> 'zu'", """
        SELECT anfadr, endadr, labez
        FROM att
        WHERE {fehlverse} AND hs = 'A' AND labez <> 'zu'
        """, "", dict (parameters, fehlverse = tools.FEHLVERSE))

        # Some labez fields end with spaces
        fix (conn, "labez with spaces", """
        SELECT labez
        FROM att
        WHERE labez ~ ' '
        """, """
        UPDATE att
        SET labez = REPLACE (labez, ' ', '')
        WHERE labez ~ ' '
        """, parameters)

        # Some labezsuf fields contain - instead of /
        fix (conn, "labezsuf with minus separator", """
        SELECT labezsuf
        FROM att
        WHERE labezsuf ~ '-[a-y]'
        """, r"""
        UPDATE att
        SET labezsuf = REGEXP_REPLACE (labezsuf, '-([a-y])', '/\1')
        WHERE labezsuf ~ '-[a-y]'
        """, parameters)

        # Some fields contain 'N' (only in chapter 5)
        # Is this a typo for NULL?  NULL will be replaced with '' later.
        for col in NULL_N_FIELDS:
            fix (conn, "{col} = N".format (col = col), """
            SELECT hs, anfadr, labez, labezsuf, lesart, {col}
            FROM att
            WHERE {col} IN ('N', 'NULL')
            LIMIT 10
            """, """
            UPDATE att
            SET {col} = NULL
            WHERE {col} IN ('N', 'NULL')
            """, dict (parameters, col = col))

        # Normalize NULL to ''
        # suffix2 sometimes contains a carriage return character
        for t in ('att', 'lac'):
            # Delete spurious '\r' characters in suffix2 field.
            execute (conn, """
            UPDATE {t}
            SET suffix2 = REGEXP_REPLACE (suffix2, '\r', '')
            WHERE suffix2 ~ '\r'
            """, dict (parameters, t = t))

            # replace NULL fields with ''
            for col in NULL_N_FIELDS + NULL_FIELDS:
                execute (conn, """
                UPDATE {t}
                SET {col} = ''
                WHERE {col} IS NULL
                """, dict (parameters, t = t, col = col))

        # Clean up the lacunae table.
        # Any errors in the lacunae table will wreak havoc with lacunae unrolling.

        debug (conn, "nested lacunae", """
        SELECT l.id, l.hs, l.anfadr, l.endadr
        FROM lac l
        JOIN lac l2
          ON l.hs = l2.hs AND l.anfadr != l2.anfadr AND l.endadr != l2.endadr
            AND int4range (l.anfadr, l.endadr + 1) <@ int4range (l2.anfadr, l2.endadr + 1)
        """, parameters)

        # Lac with anfadr > endadr
        fix (conn, "Lac with anfadr > endadr", """
        SELECT *
        FROM lac
        WHERE anfadr > endadr
        """, """
        UPDATE lac
        SET anfadr = endadr, endadr = anfadr
        WHERE anfadr > endadr
        """, parameters)

        # Fix inconsistencies in endadr between Att and Lac
        fix (conn, "Inconsistent chapter ends in Att and Lac", """
        SELECT adr2chapter (anfadr), max (endadr) AS maxend
        FROM att AS a
        GROUP BY adr2chapter (anfadr)
        HAVING max (endadr) NOT IN (
          SELECT max (endadr)
          FROM lac
          GROUP BY adr2chapter (anfadr)
        )
        """, """
        UPDATE lac
        SET endadr = 50301004
        WHERE endadr IN (50247036, 50247042);
        UPDATE lac
        SET endadr = 50760037
        WHERE endadr = 50760036;
        UPDATE lac
        SET endadr = 51130024
        WHERE hsnr = 202440 AND anfadr = 51101002;
        UPDATE lac
        SET anfadr = 51201001
        WHERE anfadr = 51201002;
        UPDATE lac
        SET endadr = 52831035
        WHERE endadr = 52831034;
        UPDATE lac
        SET irange = int4range (anfadr, endadr + 1);
        """, parameters)

        # Check consistency between Att and Lac tables
        fix (conn, "Manuscript found in lac table but not in att table", """
        SELECT DISTINCT hsnr, adr2chapter (anfadr)
        FROM lac
        WHERE hsnr NOT IN (
          SELECT DISTINCT hsnr FROM att
        )
        """, """
        DELETE
        FROM lac
        WHERE hsnr NOT IN (
          SELECT DISTINCT hsnr FROM att
        )
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

    with dba.engine.begin () as conn:

        execute (conn, """
        UPDATE att
        SET lekt = korr, korr = ''
        WHERE korr ~ '^L'
        """, parameters)

        execute (conn, """
        UPDATE att
        SET korr = lekt, lekt = ''
        WHERE lekt ~ '[C*]'
        """, parameters)

        execute (conn, """
        UPDATE att
        SET korr = '*'
        WHERE korr = '' AND suffix2 ~ '[*]'
        """, parameters)

        execute (conn, """
        UPDATE att
        SET suff = 'S'
        WHERE suff = '' AND suffix2 ~ 's'
        """, parameters)

        execute (conn, """
        UPDATE att
        SET lekt = SUBSTRING (suffix2, 'L[1-9]')
        WHERE lekt IN ('', 'L') AND suffix2 ~ 'L[1-9]'
        """, parameters)

        execute (conn, """
        UPDATE att
        SET korr = SUBSTRING (suffix2, 'C[1-9*]')
        WHERE korr IN ('', 'C') AND suffix2 ~ 'C[1-9*]'
        """, parameters)

        execute (conn, """
        UPDATE att
        SET vl = SUBSTRING (suffix2, 'T[1-9]')
        WHERE vl IN ('', 'T') AND suffix2 ~ 'T[1-9]'
        """, parameters)

        fix (conn, "Incompatible hs and suffix2 for T reading", """
        SELECT hs, anfadr, lekt, vl, suffix2
        FROM att
        WHERE hs ~ 'T[1-9]' AND hs !~ suffix2
        """, """
        UPDATE att
        SET lekt    = '',
            vl      = SUBSTRING (hs, 'T[1-9]'),
            suffix2 = SUBSTRING (hs, 'T[1-9]')
        WHERE hs ~ 'T[1-9]'
        """, parameters)

        fix (conn, "Wrong labez", """
        SELECT labez, labezsuf, adr2chapter (anfadr), count (*) AS anzahl
        FROM att
        WHERE labez ~ '.[fo]'
        GROUP BY labez, labezsuf, adr2chapter (anfadr)
        ORDER BY labez, labezsuf, adr2chapter (anfadr)
        """, """
        UPDATE att
        SET labez = SUBSTRING (labez, 1, 1),
            labezsuf = SUBSTRING (labez, 2, 1)
        WHERE labez ~ '.[fo]'
        """, parameters)

        # Print domain of fields
        for col in NULL_N_FIELDS:
            debug (conn, "Domain of {col}".format (col = col), """
            SELECT {col}, count (*) as Anzahl
            FROM att
            GROUP BY {col}
            """, dict (parameters, col = col))


def save_readings (dba, parameters):

    with dba.engine.begin () as conn:

        execute (conn, """
        INSERT INTO save_readings (anfadr, endadr, labez, lemma, lesart)
        SELECT anfadr, endadr, labez,
               MODE () WITHIN GROUP (ORDER BY lemma) AS lemma,
               MODE () WITHIN GROUP (ORDER BY lesart) AS lesart
        FROM att a
        GROUP BY anfadr, endadr, labez
        """, parameters)


def step05 (dba, parameters):
    """Process differing readings in commentaries (T1, T2)

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

    with dba.engine.begin () as conn:

        # T1 or T2 but not both
        # promote to normal status by stripping T[1-9] from hs
        execute (conn, """
        UPDATE att u
        SET hs = REGEXP_REPLACE (hs, 'T[1-9]', ''),
            vl = '',
            suffix2 = REGEXP_REPLACE (suffix2, 'T[1-9]', '')
        FROM (
          SELECT hsnr, anfadr, endadr
          FROM att
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
        FROM att
        WHERE (hsnr, anfadr, endadr) IN (
          SELECT DISTINCT hsnr, anfadr, endadr
          FROM att
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
                    ids.append (str (row[0]))
                    labez.add (row[1] + ('_' + row[2] if row[2] else ''))

                assert len (ids) > 1, "Programming error in T1, T2 processing."

                execute (conn, """
                DELETE FROM att
                WHERE id IN ({ids})
                """, dict (parameters, ids = ', '.join (ids[1:])))

                execute (conn, """
                UPDATE att
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

    with dba.engine.begin () as conn:

        for t in ('att', 'lac'):
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

    with dba.engine.begin () as conn:

        fix (conn, "Duplicate readings", """
        SELECT hs, hsnr, anfadr, endadr, labez, labezsuf, lesart FROM att
        WHERE (hsnr, anfadr, endadr) IN (
           SELECT hsnr, anfadr, endadr
           FROM att
           GROUP BY hsnr, anfadr, endadr
           HAVING count (*) > 1
        )
        """, """
        DELETE FROM att
        WHERE (hs, anfadr, endadr) = ('L156s*', 50405022, 50405034) OR
              (hs, anfadr, endadr) = ('1891*V', 52716012, 52716012) OR
              (hs, anfadr, endadr) = ('P74V',   51535022, 51535028) OR
              (hs, anfadr, endadr) = ('P74V',   50124030, 50125002) OR
              (hs, anfadr, endadr) = ('P74C*V', 50124030, 50125003) OR
              (hs, anfadr, endadr) = ('02*V',   52101008, 52101010)

        """, parameters)

        for t in ('att', 'lac'):
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

    with dba.engine.begin () as conn:

        debug (conn, "Hs with more than one hsnr", """
        SELECT hs FROM (
          SELECT DISTINCT hs, hsnr FROM att
        ) AS tmp
        GROUP BY hs
        HAVING count (*) > 1
        """, parameters)

        # print some debug info
        debug (conn, "Suffix2 debug info", """
        SELECT lekt, korr, suffix2, count (*) AS anzahl
        FROM att
        GROUP BY lekt, korr, suffix2
        ORDER BY lekt, korr, suffix2
        """, parameters)

        # Debug hs where hs and suffix2 still mismatch
        debug (conn, "hs and suffix2 mismatch", """
        SELECT hs, suffix2, anfadr, endadr, lesart
        FROM att
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
          SELECT DISTINCT hs, hsnr FROM att
        ) AS tmp
        GROUP BY hsnr
        HAVING count (*) > 1
        """, """
        UPDATE att AS t
        SET hs = g.minhs
        FROM (SELECT min (hs) AS minhs, hsnr FROM att GROUP BY hs, hsnr ORDER BY hs) AS g
        WHERE t.hsnr = g.hsnr
        """, parameters)


def step07 (dba, parameters):
    """zw Lesarten

    Aus: prepare4cbgm_7.py

        zw-Lesarten der übergeordneten Variante zuordnen, wenn ausschliesslich
        verschiedene Lesarten derselben Variante infrage kommen (z.B. zw a/ao
        oder b/bo_f).  In diesen Fällen tritt die Buchstabenkennung der
        übergeordneten Variante in labez an die Stelle von 'zw'.

    Unroll uncertain labez into multiple rows and set the certainty to <1.0.  In
    the end we will have no 'zw' rows left (they only gave trouble anyway).

    """

    with dba.engine.begin () as conn:

        fields = 'hsnr hs anfadr endadr labez labezsuf labezorig labezsuforig certainty lemma lesart irange created'.split ()
        Zw = collections.namedtuple ('Zw', fields)
        res = execute (conn, "SELECT %s FROM att WHERE labez = 'zw'" % ', '.join (fields), parameters)
        zws = list (map (Zw._make, res))

        execute (conn, """
        DELETE FROM att
        WHERE labez = 'zw'
        """, dict (parameters))

        updated = 0
        params = dict (
            fields = ', '.join (fields),
            values = ':' + ', :'.join (fields)
        )
        for zw in zws:
            unique_labez = collections.defaultdict (list)
            for suf in zw.labezsuf.split ('/'):
                unique_labez[suf[0]].append (suf[1:].replace ('_', ''))
            options = len (unique_labez)
            if options > 0:
                updated += options
                certainty = 1.0 / options
                more_params = zw._asdict ()
                for k, v in unique_labez.items ():
                    more_params.update (labez = k, labezsuf = '/'.join (v), certainty = certainty),
                    execute (conn, """
                    INSERT INTO att ({fields}) VALUES ({values})
                    """, dict (parameters, **params, **more_params), 4)

    log (logging.DEBUG, "          %d 'zw' rows unrolled" % updated)


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
        DELETE FROM att
        WHERE (anfadr, endadr) IN (
          SELECT anfadr, endadr
          FROM (
            SELECT DISTINCT anfadr, endadr, labez
            FROM att
            WHERE labez !~ '^z' AND certainty = 1.0
          ) AS i
          GROUP BY anfadr, endadr
          HAVING count (*) <= 1
        )
        """, parameters)


class CBGM_Params (object):
    """ Structure for intermediate results of the CBGM. """

    n_mss = 0               # No. of manuscripts
    n_passages = 0          # No. of passages
    n_ranges = 0            # No. of ranges
    mss = None              # list of named tuple Manuscript
    passages = None         # list of passages
    ranges = None           # list of named tuple Range
    labez_matrix = None     # mss x passages matrix of labez
    affinity_matrix = None  # mss x mss matrix of similarity measure


def copy_genealogical_data (dbsrcvg, dbdest, parameters):
    """Copy / update genealogical data

    Aus: VGA/Att2CBGMPh3.pl

    "kopiert die Daten aus ECM_Acts_CBGM nach VarGenAtt_Act,
    zur weiteren Bearbeitung im Stemma-Editor"

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

    dbsrcvg_meta = sqlalchemy.schema.MetaData (bind = dbsrcvg.engine)
    dbsrcvg_meta.reflect ()

    with dbdest.engine.begin () as dest:

        concat_tables (dest, dbsrcvg_meta, 'tmp_locstemed', 'var_fdw', 'LocStemEdAct%s')
        concat_tables (dest, dbsrcvg_meta, 'tmp_rdg',       'var_fdw', 'RdgAct%s')
        concat_tables (dest, dbsrcvg_meta, 'tmp_var',       'var_fdw', 'VarGenAttAct%s')
        copy_table (dest, 'tmp_locstemed', 'original_locstemed');
        copy_table (dest, 'tmp_rdg',       'original_rdg');
        copy_table (dest, 'tmp_var',       'original_var');
        copy_table_fdw (dest, 'var_fdw', 'Memo', 'memo')

        execute (dest, """
        DELETE FROM tmp_var
        WHERE begadr = 50516020 AND witn = 'L1188s' AND varnew = 'c'
        """, parameters)

        execute (dest, """
        DELETE FROM tmp_var
        WHERE (begadr, endadr) = (52212026, 52212028) AND witn = '1838'
        """, parameters)

        execute (dest, """
        UPDATE tmp_locstemed
        SET varid = 'zw', varnew = 'zw'
        WHERE (begadr, endadr, varnew) = (50323002, 50323006, 'e')
        """, parameters)

        execute (dest, """
        UPDATE tmp_var
        SET varid = 'zw', varnew = 'zw'
        WHERE (begadr, endadr, varnew) = (50323002, 50323006, 'e')
        """, parameters)

        execute (dest, """
        UPDATE tmp_locstemed
        SET varid = 'zw', varnew = 'zw'
        WHERE (begadr, endadr, varid) = (50424028, 50424030, 'e');
        UPDATE tmp_var
        SET varid = 'zw', varnew = 'zw'
        WHERE (begadr, endadr, varid) = (50424028, 50424030, 'e')
        """, parameters)

        execute (dest, """
        UPDATE tmp_locstemed
        SET varid = 'a', varnew = 'a', s1 = '*'
        WHERE (begadr, endadr, varnew) = (51413002, 51413044, 'e')
        """, parameters)

        execute (dest, """
        INSERT INTO tmp_locstemed (id, begadr, endadr, varid, varnew, s1, s2, prs1, prs2, "check")
        VALUES (0, 51313038, 51313038, 'd', 'd', '?', '', '', '', '');
        UPDATE tmp_var
        SET s1 = '?'
        WHERE (begadr, endadr, varnew) = (51313038, 51313038, 'd')
        """, parameters)

        for old, new in zip ('n o p'.split (), 'm n o'.split ()):
            execute (dest, """
            UPDATE tmp_locstemed
            SET varid = :new, varnew = :new
            WHERE (begadr, endadr, varid) = (52621006, 52621010, :old);
            UPDATE tmp_var
            SET varid = :new, varnew = :new
            WHERE (begadr, endadr, varid) = (52621006, 52621010, :old)
            """, dict (parameters, old = old, new = new))

        execute (dest, """
        DELETE FROM tmp_locstemed
        WHERE (begadr, endadr, varnew, s1) = (52621006, 52621010, 'm', '?');
        DELETE FROM tmp_var
        WHERE (begadr, endadr, varnew, s1) = (52621006, 52621010, 'm', '?');
        DELETE FROM tmp_locstemed
        WHERE (begadr, endadr, varnew) = (50116013, 50116013, 'zv');
        DELETE FROM tmp_locstemed
        WHERE (begadr, endadr) = (52209026, 52209034);
        """, parameters)

        execute (dest, """
        UPDATE tmp_var
        SET varid = 'c', varnew = 'c'
        WHERE varnew = 'cf';
        UPDATE tmp_var
        SET varid = 'd', varnew = 'd'
        WHERE varnew = 'df';
        UPDATE tmp_locstemed
        SET varid = 'c', varnew = 'c'
        WHERE varnew = 'cf';
        UPDATE tmp_locstemed
        SET varid = 'd', varnew = 'd'
        WHERE varnew = 'df';
        UPDATE tmp_locstemed
        SET s1 = 'h1'
        WHERE begadr = 50247038 AND endadr = 50301004 AND s1 = 'h';
        UPDATE tmp_locstemed
        SET s1 = 'a1'
        WHERE begadr = 50313008 AND endadr = 50313008 AND s1 = 'a';
        UPDATE tmp_locstemed
        SET s1 = 'c1'
        WHERE begadr = 50412022 AND endadr = 50412040 AND s1 = 'c';
        UPDATE tmp_locstemed
        SET s1 = 'a1'
        WHERE begadr = 50516018 AND endadr = 50516018 AND s1 = 'a';
        UPDATE tmp_locstemed
        SET s1 = 'b1'
        WHERE begadr = 51915006 AND endadr = 51915008 AND s1 = 'b';
        UPDATE tmp_locstemed
        SET s1 = 'b1'
        WHERE begadr = 52525008 AND endadr = 52525016 AND s1 = 'b';
        UPDATE tmp_locstemed
        SET s1 = 'a'
        WHERE begadr = 52507028 AND endadr = 52507028 AND s1 = 'b';
        """, parameters)

        execute (dest, """
        UPDATE tmp_var
        SET s1 = 'a1'
        WHERE begadr = 51314016 AND endadr = 51314022 AND witn = '2147';
        UPDATE tmp_var
        SET varid = 'zw', varnew = 'zw', s1 = ''
        WHERE begadr = 50926004 AND endadr = 50926008 AND witn = '424';
        UPDATE tmp_var
        SET varid = 'b', varnew = 'b', s1 = 'a1'
        WHERE begadr = 51314016 AND endadr = 51314022 AND witn = '2718';
        UPDATE tmp_var
        SET varid = 'a', varnew = 'a2', s1 = '?'
        WHERE begadr = 50405022 AND endadr = 50405034 AND witn = 'L156s'
        """, parameters)

        execute (dest, """
        UPDATE tmp_var
        SET varid = 'f', varnew = 'f', s1 = 'a'
        WHERE begadr = 51201014 and endadr = 51201022 AND witn = 'L1188';
        UPDATE tmp_var
        SET varid = 'b', varnew = 'b', s1 = 'a'
        WHERE begadr = 51309022 and endadr = 51309022 AND witn = 'L1188';
        UPDATE tmp_var
        SET varid = 'c', varnew = 'c2', s1 = 'a1'
        WHERE begadr = 51324020 and endadr = 51324026 AND witn = 'L1188';
        UPDATE tmp_var
        SET varid = 'd', varnew = 'd', s1 = 'a'
        WHERE begadr = 52207002 and endadr = 52207004 AND witn = 'L1188'
        """, parameters)

        execute (dest, """
        UPDATE tmp_var
        SET varid = 'a', varnew = 'a1', s1 = '*'
        WHERE begadr = 51342020 AND endadr = 51342026 AND witn = '383'
        """, parameters)

        execute (dest, """
        UPDATE tmp_var
        SET varid = 'zz', varnew = 'zz', s1 = ''
        WHERE begadr = 50111044 AND endadr = 50111044 AND witn = '321'
        """, parameters)

        execute (dest, """
        UPDATE memo
        SET remarks = TRIM (BOTH FROM REGEXP_REPLACE (remarks, '\s*\r?\n', E'\n', 'g'));
        UPDATE memo
        SET remarks = NULL
        WHERE remarks = ''
        """, parameters)

        res = execute (dest, """
        SELECT id, remarks
        FROM memo
        WHERE remarks ~ '&'
        """, parameters)

        params = []
        for row in res.fetchall ():
            params.append ([
                html.unescape (row['remarks']),
                row['id'],
            ])

        executemany_raw (dest, """
        UPDATE memo
        SET remarks = %s
        WHERE id = %s
        """, parameters, params)


def fill_passages_table (dba, parameters):
    """ Create the Passages table. """

    with dba.engine.begin () as conn:

        execute (conn, """
        TRUNCATE books RESTART IDENTITY CASCADE
        """, parameters)

        # The Books Table

        Book = collections.namedtuple ('Book', 'bk_id siglum book ranges')

        executemany (conn, """
        INSERT INTO books (bk_id, siglum, book, irange)
        VALUES (:bk_id, :siglum, :book, int4range (:bk_id * 10000000, (:bk_id + 1) * 10000000))
        """, parameters, [ Book._make (b)._asdict () for b in tools.BOOKS if b[3] > 0])

        # The Ranges Table

        params = []
        for b in map (Book._make, tools.BOOKS):
            if b.ranges > 0:
                offset = 10000000 * b.bk_id
                params.append ([b.bk_id, 'All', offset, offset + 10000000])
                for ch in range (1, b.ranges + 1):
                    params.append ([b.bk_id, str (ch), offset + ch * 100000, offset + ((ch + 1) * 100000)])

        executemany_raw (conn, """
        INSERT INTO ranges (bk_id, range, irange)
        VALUES (%s, %s, int4range (%s, %s))
        """, parameters, params)

        # The Passages Table

        execute (conn, """
        INSERT INTO passages (anfadr, endadr, irange, lemma, bk_id)
        SELECT anfadr, endadr, int4range (anfadr, endadr + 1),
               MODE () WITHIN GROUP (ORDER BY lemma) AS lemma,
               bk_id
        FROM att a
        JOIN books b ON b.irange @> anfadr
        GROUP BY anfadr, endadr, int4range (anfadr, endadr + 1), bk_id
        ORDER BY anfadr, endadr DESC
        """, parameters)

        # Mark Nested Passages

        execute (conn, """
        UPDATE passages p
        SET spanned = EXISTS (
          SELECT irange FROM passages o
          WHERE o.irange @> p.irange AND p.pass_id <> o.pass_id
        ),
        spanning = EXISTS (
          SELECT irange FROM passages i
          WHERE i.irange <@ p.irange AND p.pass_id <> i.pass_id
        )
        """, parameters)

        # Mark Fehlverse

        execute (conn, """
        UPDATE passages p
        SET fehlvers = True
        WHERE {fehlverse}
        """, dict (parameters, fehlverse = tools.FEHLVERSE))

        # Insert remarks

        execute (conn, """
        UPDATE passages p
        SET remarks = m.remarks
        FROM memo m
        WHERE (p.anfadr, p.endadr) = (m.anfadr, m.endadr)
        """, parameters)


def fill_manuscripts_table (dba, parameters):
    """ Create the Manuscripts and Ms_Ranges tables. """

    with dba.engine.begin () as conn:

        execute (conn, """
        TRUNCATE manuscripts RESTART IDENTITY CASCADE
        """, parameters)

        # The Manuscripts Table

        # ms_id = 1
        execute (conn, """
        INSERT INTO manuscripts (hs, hsnr) VALUES ('A', 0)
        """, parameters)

        # ms_id = 2
        execute (conn, """
        INSERT INTO manuscripts (hs, hsnr) VALUES ('MT', 1)
        """, parameters)

        # ms_id = 3, 4, 5, ...
        execute (conn, """
        INSERT INTO manuscripts (hs, hsnr)
        SELECT DISTINCT hs, hsnr
        FROM att
        WHERE hsnr >= 100000
        ORDER BY hsnr
        """, parameters)

        # Init the Ms_Ranges Table

        execute (conn, """
        INSERT INTO ms_ranges (ms_id, rg_id, length)
        SELECT ms.ms_id, ch.rg_id, 0
        FROM manuscripts ms
        CROSS JOIN ranges ch
        """, parameters)


def fill_readings_table (dba, parameters):
    """ Create the readings table. """

    with dba.engine.begin () as conn:

        execute (conn, """
        TRUNCATE readings RESTART IDENTITY CASCADE
        """, parameters)

        execute (conn, """
        INSERT INTO readings (pass_id, labez, lesart)
        SELECT p.pass_id, a.labez, a.lesart
        FROM save_readings a
        JOIN passages p
        ON (a.anfadr, a.endadr) = (p.anfadr, p.endadr)
        """, parameters)

        # Insert a 'zz' reading for every passage
        execute (conn, """
        INSERT INTO readings (pass_id, labez, lesart)
        SELECT p.pass_id, 'zz', ''
        FROM passages p
        ON CONFLICT DO NOTHING
        """, parameters)

        # Update lesart of 'zu' readings
        execute (conn, """
        UPDATE readings
        SET lesart = 'overlap'
        WHERE labez = 'zu'
        """, parameters)

        # Update lesart of 'zz' readings
        execute (conn, """
        UPDATE readings
        SET lesart = ''
        WHERE labez = 'zz'
        """, parameters)

        # Delete 'zw' readings.  'zw' readings in the att table get unrolled
        # into many uncertain non-'zw' readings, so they will never relate to
        # 'zw' readings back here anyway.
        execute (conn, """
        DELETE FROM readings
        WHERE labez = 'zw'
        """, parameters)


def fill_cliques_table (db, parameters):

    with db.engine.begin () as conn:

        execute (conn, """
        TRUNCATE cliques RESTART IDENTITY CASCADE
        """, parameters)

        warn (conn, "Readings in locstemed but not in readings", """
        SELECT l.begadr, l.endadr, l.varid
        FROM tmp_locstemed l
        LEFT JOIN readings_view r
          ON (l.begadr, l.endadr, l.varid) = (r.anfadr, r.endadr, r.labez)
        WHERE r.labez IS NULL AND l.varid != 'zw' AND NOT (l.varnew = 'a' AND l.s1 = '?')
        ORDER BY l.begadr, l.endadr, l.varid
        """, parameters)

        warn (conn, "Readings in readings but not in locstemed", """
        SELECT r.anfadr, r.endadr, r.labez
        FROM readings_view r
        LEFT JOIN tmp_locstemed l
          ON (r.anfadr, r.endadr, r.labez) = (l.begadr, l.endadr, l.varid)
        WHERE r.labez !~ '^z' AND l.varid IS NULL
        ORDER BY r.pass_id, r.labez
        """, parameters)

        # copy default readings into cliques

        execute (conn, """
        INSERT INTO cliques (pass_id, labez)
        SELECT r.pass_id, r.labez
        FROM readings r
        """, parameters)

        # add 'editor' cliques from locstem

        execute (conn, """
        INSERT INTO cliques (pass_id, labez, clique)
        SELECT p.pass_id, varnew2labez (varnew), varnew2clique (varnew)
        FROM tmp_locstemed l, passages p
        WHERE p.irange = int4range (l.begadr, l.endadr + 1)
          AND varnew !~ '^z'
        GROUP BY p.pass_id, varnew2labez (varnew), varnew2clique (varnew)
        ON CONFLICT DO NOTHING
        """, parameters)

        warn (conn, "Duplicates in VarGenAtt", """
        SELECT begadr, endadr, witn
        FROM tmp_var
        GROUP BY witn, begadr, endadr
        HAVING count (*) > 1
        """, parameters)

        # warn (conn, "Cliques in VarGen but not in Cliques", """
        # SELECT p.pass_id, ms.ms_id, v.varnew
        #   FROM tmp_var v
        #   JOIN passages p ON (v.begadr, v.endadr) = (p.anfadr, p.endadr)
        #   JOIN manuscripts ms ON v.ms = ms.hsnr
        #   LEFT JOIN cliques q ON q.pass_id = p.pass_id AND q.labez = varnew2labez (v.varnew) AND q.clique = varnew2clique (v.varnew)
        # WHERE v.varnew !~ '^z[uvw]' AND q.labez IS NULL
        # """, parameters)

        # insert missing cliques into Cliques

        # execute (conn, """
        # INSERT INTO cliques (pass_id, labez, clique)
        # SELECT p.pass_id, varnew2labez (v.varnew) AS labez, varnew2clique (v.varnew) AS clique
        # FROM tmp_var v
        # JOIN passages p ON (p.anfadr, p.endadr) = (v.begadr, v.endadr)
        # WHERE varnew2clique (v.varnew) > '1' AND v.varnew !~ '^z[uvw]'
        # GROUP BY pass_id, labez, clique
        # """, parameters)


def fill_apparatus_table (dba, parameters):
    """ Create the apparatus table.

    Build a positive apparatus.
    """

    with dba.engine.begin () as conn:

        execute (conn, """
        TRUNCATE apparatus RESTART IDENTITY CASCADE
        """, parameters)

        # 1. Fill all mss with the default readings of ms 'A'
        #
        # See paper: "Arbeitsablauf CBGM auf Datenbankebene, I. Vorbereitung der
        # Datenbasis für CBGM"

        log (logging.INFO, "          Filling default readings of 'A' ...")

        execute (conn, """
        INSERT INTO apparatus (ms_id, pass_id, labez, cbgm, labezsuf, certainty, lesart, origin)
        SELECT ms.ms_id, p.pass_id, a.labez, true, a.labezsuf, 1.0, NULLIF (a.lesart, r.lesart), 'DEF'
        FROM passages p
          CROSS JOIN manuscripts ms
          JOIN att a ON p.irange = a.irange AND a.hsnr = 0
          JOIN readings r ON r.pass_id = p.pass_id AND r.labez = a.labez
        """, parameters)


    with dba.engine.begin () as conn:

        # 2. Unroll lacunae from lacunae table into apparatus
        #
        # There is only one entry for each lacuna in the lacunae table even if
        # it spans multiple passages.  We need to unroll every lacuna onto every
        # passages it spans.

        log (logging.INFO, "          Unrolling lacunae ...")

        execute (conn, """
        UPDATE apparatus app
        SET labez = 'zz', cbgm = true, labezsuf = '', certainty = 1.0, lesart = NULL, origin = 'LAC'
        FROM (
          SELECT DISTINCT ms.ms_id, p.pass_id
          FROM lac l
          JOIN passages p
            ON p.irange <@ l.irange
          JOIN manuscripts ms
            ON ms.hsnr = l.hsnr
        ) AS a
        WHERE a.pass_id = app.pass_id AND a.ms_id = app.ms_id
        """, parameters)


    with dba.engine.begin () as conn:

        # 3. Overwrite default readings if there is a reading in att
        #
        # N.B. must be done after lacunae unrolling because readings
        # in att do "override" lacunae

        log (logging.INFO, "          Filling in readings from negative apparatus ...")

        execute (conn, """
        UPDATE apparatus app
        SET labez = a.labez, cbgm = a.certainty = 1.0, labezsuf = a.labezsuf,
            certainty = a.certainty, lesart = NULLIF (a.lesart, r.lesart), origin = 'ATT'
        FROM passages p, manuscripts ms, readings r, att a
        WHERE app.pass_id = p.pass_id AND p.irange = a.irange AND r.pass_id = p.pass_id
          AND app.ms_id = ms.ms_id  AND ms.hsnr = a.hsnr AND r.labez = a.labez
          AND a.certainty = 1.0
        """, parameters)

        # Insert uncertain readings

        execute (conn, """
        DELETE FROM apparatus app
          USING passages p, manuscripts ms, att a
          WHERE p.pass_id  = app.pass_id AND
                ms.ms_id = app.ms_id AND
                a.irange = p.irange AND a.hsnr = ms.hsnr AND
                a.certainty < 1.0
        """, parameters)

        execute (conn, """
        INSERT INTO apparatus (pass_id, ms_id, labez, cbgm, labezsuf, certainty, lesart, origin)
        SELECT p.pass_id, ms.ms_id, a.labez, a.certainty = 1.0, a.labezsuf, a.certainty, NULLIF (a.lesart, r.lesart), 'UNC'
        FROM passages p, manuscripts ms, readings r, att a
        WHERE p.pass_id = r.pass_id AND p.irange = a.irange
          AND ms.hsnr = a.hsnr AND r.labez = a.labez
          AND a.certainty < 1.0
        """, parameters)

    with dba.engine.begin () as conn:

        # Data entry fixes

        log (logging.INFO, "          Doing sanity checks ...")

        fix (conn, "Readings in tmp_var != Apparatus", """
        SELECT a.pass_id, a.anfadr, a.endadr, a.ms_id, a.hs, a.hsnr, a.labez, v.varid, v.varnew
        FROM tmp_var v
        JOIN apparatus_view a
          ON int4range (v.begadr, v.endadr + 1) = a.irange AND v.ms = a.hsnr
        WHERE v.varid != a.labez AND v.varid !~ '^z' AND a.cbgm
        ORDER BY a.anfadr, a.endadr, a.hsnr, a.labez;
        """, """
        UPDATE tmp_var v
        SET varid = 'zu', varnew = 'zu'
        FROM apparatus_view a
        WHERE (v.begadr, v.endadr, v.ms, 'zu') = (a.anfadr, a.endadr, a.hsnr, a.labez);
        UPDATE tmp_var v
        SET varid = 'a', varnew = 'a1'
        FROM apparatus_view a
        WHERE (v.begadr, v.endadr, v.ms) = (a.anfadr, a.endadr, a.hsnr)
          AND (a.anfadr, a.endadr, a.labez, v.varid) = (51122038, 51122040, 'a', 'b');
        """, parameters)

        log (logging.INFO, "          Doing sanity checks ...")

        fix (conn, "Original reading uncertain but apparatus doesn't read zz", """
        SELECT a.*, l.varid, l.varnew, l.s1
        FROM apparatus_view a, tmp_locstemed l
        WHERE (a.anfadr, a.endadr) = (l.begadr, l.endadr)
          AND l.varnew = 'a' AND l.s1 = '?'
          AND a.ms_id = 1 and a.labez != 'zz'
        """, """
        UPDATE apparatus a
        SET labez = 'zz', cbgm = true, certainty = 1.0, origin = 'LOC'
        FROM passages p, tmp_locstemed l
        WHERE a.pass_id = p.pass_id AND (p.anfadr, p.endadr) = (l.begadr, l.endadr)
          AND l.varnew = 'a' AND l.s1 = '?'
          AND a.ms_id = 1 and a.labez != 'zz'
        """, parameters)

    with dba.engine.begin () as conn:

        # Update the clique no. in Apparatus

        log (logging.INFO, "          Filling in clique numbers ...")

        execute (conn, """
        UPDATE apparatus u
        SET clique = varnew2clique (v.varnew)
        FROM tmp_var v, manuscripts ms, cliques_view cq
        WHERE (cq.pass_id, cq.labez) = (u.pass_id, u.labez)
          AND u.ms_id = ms.ms_id AND ms.hsnr = v.ms
          AND cq.labez = varnew2labez (v.varnew)
          AND cq.clique = varnew2clique (v.varnew)
          AND cq.irange = int4range (v.begadr, v.endadr + 1)
          AND v.varnew !~ '^z[uvw]'
          AND varnew2clique (v.varnew) != '1'
        """, parameters)


def build_byzantine_text (dba, parameters):
    """Reconstruct the Majority Text

    Build a virtual manuscript that reconstructs the :ref:`Majority Text <mt>`.
    The MT manuscripts has a hard-coded ms_id of 2.

    .. _mt_rules:

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

    --PreCo/PreCoActs/ActsMT2.pl

    """

    with dba.engine.begin () as conn:

        execute (conn, """
        DELETE FROM apparatus WHERE ms_id = 2
        """, parameters)

        execute (conn, """
        INSERT INTO apparatus (ms_id, pass_id, labez, clique, cbgm, origin)
          SELECT 2, pass_id, labez[1], clique[1], true, 'BYZ'
          FROM (
            SELECT pass_id,
                   ARRAY_AGG (labez  ORDER BY cnt DESC) AS labez,
                   ARRAY_AGG (clique ORDER BY cnt DESC) AS clique,
                   ARRAY_AGG (cnt    ORDER BY cnt DESC) AS mask
            FROM (
              SELECT pass_id, labez, clique, count (*) AS cnt
              FROM apparatus_view a
              WHERE hsnr IN {byzlist}
              GROUP BY pass_id, labez, clique
            ) AS q1
            GROUP BY pass_id
          ) AS q2
          WHERE mask IN ('{{7}}', '{{6,1}}', '{{5,1,1}}')
        """, dict (parameters, byzlist = tools.BYZ_HSNR))

        # Fill with labez 'zz' where MT is undefined
        execute (conn, """
        INSERT INTO apparatus (ms_id, pass_id, labez, cbgm, origin)
        SELECT 2, p.pass_id, 'zz', true, 'BYZ'
        FROM passages p
        ON CONFLICT DO NOTHING
        """, parameters)


def fill_locstem_table (db, parameters):

    with db.engine.begin () as conn:

        execute (conn, """
        TRUNCATE locstem RESTART IDENTITY CASCADE
        """, parameters)

        fix (conn, "Duplicates in LocStem", """
        SELECT begadr, endadr, varnew
        FROM tmp_locstemed
        GROUP BY begadr, endadr, varnew
        HAVING count (*) > 1
        """, """
        DELETE FROM tmp_locstemed
        WHERE (begadr, endadr, varnew, s1) = (51702028, 51702030, 'c2', '?');
        DELETE FROM tmp_locstemed
        WHERE (begadr, endadr, varnew, s1) = (52830006, 52830014, 'd', '?')
        """, parameters)

        warn (conn, "Sources in LocStemEd but not in Cliques", """
        SELECT p.pass_id, p.anfadr, p.endadr, l.varnew, l.s1
        FROM tmp_locstemed l
        JOIN passages p ON p.irange = int4range (l.begadr, l.endadr + 1)
        LEFT JOIN cliques q ON q.pass_id = p.pass_id AND q.labez = source2labez (l.s1) AND q.clique = varnew2clique (l.s1)
        WHERE  l.varnew !~ '^z' AND l.s1 NOT IN ('*', '?', '') AND q.labez IS NULL
        """, parameters)

        # copy cliques into locstem

        execute (conn, """
        INSERT INTO locstem (pass_id, labez, clique, source_labez, source_clique, original)
        SELECT pass_id, labez, clique, NULL, NULL, false
        FROM cliques
        """, parameters)

        # update locstem from LocStemEd

        # s1 = '*'   =>   s1 = NULL AND original = True
        # s1 = '?'   =>   s1 = NULL AND original = False
        execute (conn, """
        UPDATE locstem u
        SET source_labez  = source2labez (l.s1),
            source_clique = source2clique (l.s1),
            original      = source2original (l.s1)
        FROM tmp_locstemed l, passages p
        WHERE u.pass_id = p.pass_id AND
              u.labez   = varnew2labez (l.varnew)  AND
              u.clique  = varnew2clique (l.varnew) AND
              (p.anfadr, p.endadr) = (l.begadr, l.endadr) AND
              l.varnew !~ '^z'
        """, parameters)

        # check generated locstem
        fix (conn, "Self-references in locstem", """
        SELECT pass_id, anfadr, endadr, labez, clique, source_labez, source_clique
        FROM locstem_view
        WHERE labez = source_labez AND clique = source_clique
        """, """
        DELETE FROM locstem
        WHERE labez = source_labez AND clique = source_clique
        """, parameters)


def create_labez_matrix (dba, parameters, val):
    """Create the labez matrix.

    Create a matrix of manuscripts x passages.  Each entry represents one
    reading: 0 = lacuna, 1 = 'a', 2 = 'b', ...

    """

    Manuscript = collections.namedtuple ('Manuscript', 'hs hsnr')

    with dba.engine.begin () as conn:

        np.set_printoptions (threshold = 30)

        # get passages
        res = execute (conn, """
        SELECT anfadr, endadr
        FROM passages
        ORDER BY anfadr, endadr DESC
        """, parameters)

        res = list (res)
        val.n_passages = len (res)
        val.passages   = ["%s-%s" % (x[0], x[1]) for x in res]

        # get manuscript names and numbers
        res = execute (conn, """
        SELECT hs, hsnr
        FROM manuscripts
        ORDER BY ms_id
        """, parameters)
        res = list (res)
        val.n_mss = len (res)
        val.mss = list (map (Manuscript._make, res))

        # get no. of ranges
        Range = collections.namedtuple ('Range', 'rg_id range start end')
        res = execute (conn, """
        SELECT rg_id, range, MIN (pass_id) - 1 AS first_id, MAX (pass_id) AS last_id
        FROM ranges ch
        JOIN passages p ON ch.irange @> p.irange
        GROUP BY rg_id, range
        ORDER BY lower (ch.irange), upper (ch.irange) DESC
        """, parameters)
        val.n_ranges = res.rowcount
        val.ranges = list (map (Range._make, res))

        # Matrix ms x pass

        # Initialize all manuscripts to the labez 'a'
        labez_matrix  = np.broadcast_to (np.array ([1], np.uint32), (val.n_mss, val.n_passages)).copy ()

        # overwrite matrix where actual labez is different from 'a'
        res = execute (conn, """
        SELECT ms_id - 1, pass_id - 1, ord_labez (labez) as labez
        FROM apparatus a
        WHERE labez != 'a' AND cbgm
        """, parameters)

        for row in res:
            labez_matrix [row[0], row[1]] = row[2]

        # clear matrix where reading is uncertain
        res = execute (conn, """
        SELECT DISTINCT ms_id - 1, pass_id - 1
        FROM apparatus
        WHERE certainty != 1.0
        """, parameters)

        for row in res:
            labez_matrix [row[0], row[1]] = 0

        val.labez_matrix = labez_matrix

        # Boolean matrix ms x pass set where passage is defined
        val.def_matrix = np.greater (val.labez_matrix, 0)

        log (logging.INFO, 'Size of the labez matrix: ' + str (val.labez_matrix.shape))

        # debug plot the matrix
        if PLOT:
            ticks_labels_x = plot.passages_labels (val.passages)
            ticks_labels_y = plot.mss_labels (val.mss)

            plot.plt.figure (1)
            plot.heat_matrix (val.def_matrix, "Manuscript Definition Matrix",
                              ticks_labels_x, ticks_labels_y, plot.colormap_bw ())
            plot.plt.savefig ('output/mss-definition.png')
            plot.plt.close ()


def count_by_range (a, range_starts, range_ends):
    """Count true bits in array ranges

    Count the bits that are true in multiple ranges of the same array of booleans.

    :param numpy.Array a:      Input array
    :type a: np.Array of np.bool:
    :param int[] range_starts: Starting offsets of the ranges to count.
    :param int[] range_ends:   Ending offsets of the ranges to count.

    """
    cs = np.cumsum (a)    # cs[0] = a[0], cs[1] = cs[0] + a[1], ..., cs[n] = total
    cs = np.insert (cs, 0, 0)
    cs_start = cs[range_starts] # get the sums at the range beginnings
    cs_end   = cs[range_ends]   # get the sums at the range ends
    return cs_end - cs_start


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

    # Matrix range x ms x ms with count of the passages that are defined in both mss
    val.and_matrix = np.zeros ((val.n_ranges, val.n_mss, val.n_mss), dtype = np.uint16)

    # Matrix range x ms x ms with count of the passages that are equal in both mss
    val.eq_matrix  = np.zeros ((val.n_ranges, val.n_mss, val.n_mss), dtype = np.uint16)

    # Matrix range x ms of range lengths
    val.range_len_matrix = np.zeros ((val.n_ranges, val.n_mss), dtype = np.uint16)

    val.range_starts = [ch.start for ch in val.ranges]
    val.range_ends   = [ch.end   for ch in val.ranges]

    # pre-genealogical coherence outputs symmetrical matrices
    # loop over all mss O(n_mss² * n_ranges * n_passages)

    for j in range (0, val.n_mss):
        labezj = val.labez_matrix[j]
        defj   = val.def_matrix[j]

        for k in range (j + 1, val.n_mss):
            labezk = val.labez_matrix[k]
            defk   = val.def_matrix[k]

            def_and  = np.logical_and (defj, defk)
            labez_eq = np.logical_and (def_and, np.equal (labezj, labezk))

            val.and_matrix[:,j,k] = val.and_matrix[:,k,j] = count_by_range (def_and, val.range_starts, val.range_ends)
            val.eq_matrix[:,j,k]  = val.eq_matrix[:,k,j]  = count_by_range (labez_eq, val.range_starts, val.range_ends)

    # calculate range lengths
    for j in range (0, val.n_mss):
        val.range_len_matrix[:,j] = count_by_range (val.def_matrix[j], val.range_starts, val.range_ends)


def calculate_mss_similarity_postco (dba, parameters, val):
    """Calculate post-coherence mss similarity

    Genealogical coherence outputs asymmetrical matrices.
    Loop over all mss O(n_mss² * n_ranges * n_passages).

    """

    with dba.engine.begin () as conn:

        execute (conn, "TRUNCATE affinity RESTART IDENTITY", parameters)

        # Load all passages into memory

        res = execute (conn, """
        SELECT pass_id, anfadr, endadr FROM passages
        ORDER BY pass_id
        """, parameters)

        stemmas = dict ()
        for pass_id, anfadr, endadr in res.fetchall ():
            G = db_tools.local_stemma_to_nx (conn, pass_id)

            G.add_node ('root', label = 'root')
            G.add_edge ('root', '*')
            G.add_edge ('root', '?')

            # sanity tests
            if not nx.is_weakly_connected (G):
                # use it anyway
                log (logging.WARNING, "Local Stemma @ %s-%s is not connected (pass_id=%s)." %
                     (anfadr, endadr, pass_id))
            if not nx.is_directed_acyclic_graph (G):
                # don't use these
                log (logging.ERROR, "Local Stemma @ %s-%s is not a directed acyclic graph (pass_id=%s)." %
                     (anfadr, endadr, pass_id))
                continue

            G.remove_node ('root')

            # build node masks
            # print (list (enumerate (sorted (G.nodes ()))))
            for i, n in enumerate (sorted (G.nodes ())):
                attrs = G.node[n]
                attrs['mask'] = (1 << i)
                attrs['parents'] = 0
                attrs['ancestors'] = 0
            # parents mask
            for n in G:
                mask = G.node[n]['mask']
                for succ in G.successors (n):
                    G.node[succ]['parents'] |= mask
            # ancestors mask
            TC = nx.transitive_closure (G)
            for n in TC:
                # transitive_closure does not copy attributes !
                mask = G.node[n]['mask']
                for succ in TC.successors (n):
                    G.node[succ]['ancestors'] |= mask

            stemmas[pass_id - 1] = G

        # Matrix mss x passages containing the bitmask of the current reading
        mask_matrix     = np.zeros ((val.n_mss, val.n_passages), np.uint64)
        # Matrix mss x passages containing the bitmask of the parent readings
        parent_matrix   = np.zeros ((val.n_mss, val.n_passages), np.uint64)
        # Matrix mss x passages containing the bitmask of the ancestral readings
        ancestor_matrix = np.zeros ((val.n_mss, val.n_passages), np.uint64)
        # Matrix mss x passages containing True if source is unclear (s1 = '?')
        quest_matrix    = np.zeros ((val.n_mss, val.n_passages), np.bool_)

        # load ms x pass
        res = execute (conn, """
        SELECT pass_id - 1 AS pass_id,
               ms_id   - 1 AS ms_id,
               labez_clique (labez, clique) AS labez_clique
        FROM apparatus a
        WHERE labez !~ '^z' AND cbgm
        ORDER BY pass_id
        """, parameters)

        LocStemEd = collections.namedtuple ('LocStemEd', 'pass_id ms_id labez_clique')
        rows = list (map (LocStemEd._make, res))

        # If ((current bitmask of ms j) and (ancestor bitmask of ms k) > 0) then
        # ms j is an ancestor of ms k.

        error_count = 0
        for row in rows:
            try:
                attrs = stemmas[row.pass_id].node[row.labez_clique]
                mask_matrix     [row.ms_id, row.pass_id] = attrs['mask']
                parent_matrix   [row.ms_id, row.pass_id] = attrs['parents']
                ancestor_matrix [row.ms_id, row.pass_id] = attrs['ancestors']
                quest_matrix    [row.ms_id, row.pass_id] = attrs['parents'] & 2 # '*', '?', 'a', ...
            except KeyError as e:
                error_count += 1
                #print (row.pass_id + 1)
                #print (str (e))

        if error_count:
            log (logging.WARNING, "Could not find labez and clique in LocStem in %d cases." % error_count)
        log (logging.INFO, "mask:\n"      + str (mask_matrix))
        log (logging.INFO, "parents:\n"   + str (parent_matrix))
        log (logging.INFO, "ancestors:\n" + str (ancestor_matrix))
        log (logging.INFO, "quest:\n"     + str (quest_matrix))

        def postco (mask_matrix, anc_matrix):

            local_stemmas_with_loops = set ()

            # Matrix range x ms x ms with count of the passages that are older in ms1 than in ms2
            ancestor_matrix = np.zeros ((val.n_ranges, val.n_mss, val.n_mss), dtype = np.uint16)

            # Matrix range x ms x ms with count of the passages whose relationship is unclear in ms1 and ms2
            unclear_matrix  = np.zeros ((val.n_ranges, val.n_mss, val.n_mss), dtype = np.uint16)

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
                    unclear = np.logical_and (unclear, np.not_equal (val.labez_matrix[j], val.labez_matrix[k]))
                    unclear = np.logical_and (unclear, np.logical_or (quest_matrix[j], quest_matrix[k]))
                    unclear = np.logical_and (unclear, np.logical_not (np.logical_or (varidj_is_older, varidk_is_older)))

                    ancestor_matrix[:,j,k] = count_by_range (varidj_is_older, val.range_starts, val.range_ends)
                    unclear_matrix[:,j,k]  = count_by_range (unclear, val.range_starts, val.range_ends)

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

        log (logging.INFO, "          Updating length in Ranges table ...")

        # calculate ranges lengths using numpy
        params = []
        for i, ms in enumerate (val.mss):
            for range_ in val.ranges:
                length = int (np.sum (val.def_matrix[i, range_.start:range_.end]))
                params.append ( { 'ms_id': i + 1, 'range': range_.rg_id, 'length': length } )

        executemany (conn, """
        UPDATE ms_ranges
        SET length = :length
        WHERE ms_id = :ms_id AND rg_id = :range
        """, parameters, params)

        log (logging.INFO, "          Filling Affinity table ...")

        for i, range_ in enumerate (val.ranges):
            values = []
            for j in range (0, val.n_mss):
                for k in range (0, val.n_mss):
                    if j != k:
                        common = int (val.and_matrix[i,j,k])
                        if common > 0:
                            values.append ( (
                                range_.rg_id,
                                j + 1,
                                k + 1,
                                common,
                                int (val.eq_matrix[i,j,k]),
                                int (val.ancestor_matrix[i,j,k]),
                                int (val.ancestor_matrix[i,k,j]),
                                int (val.unclear_ancestor_matrix[i,j,k]),
                                int (val.parent_matrix[i,j,k]),
                                int (val.parent_matrix[i,k,j]),
                                int (val.unclear_parent_matrix[i,j,k]),
                            ) )

            # speed gain for using executemany_raw: 65s to 55s :-(
            # probably the bottleneck here is string formatting with %s
            executemany_raw (conn, """
            INSERT INTO affinity (rg_id, ms_id1, ms_id2, common, equal,
                                  older, newer, unclear,
                                  p_older, p_newer, p_unclear)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, parameters, values)

        log (logging.INFO, "          Updating affinity in Affinity table ...")

        execute (conn, """
        UPDATE affinity
        SET affinity = equal::float / common::float
        WHERE common > 0
        """, parameters)

        log (logging.INFO, "          Done with Affinity table ...")

        print ("eq\n",       val.eq_matrix)
        print ("ancestor\n", val.ancestor_matrix)
        print ("unclear\n",  val.unclear_ancestor_matrix)
        print ("and\n",      val.and_matrix)


def vacuum (dba, parameters):
    """Vacuum database

    """

    # turn off auto-transaction because vacuum won't work in a transaction
    connection = dba.engine.raw_connection ()
    connection.set_isolation_level (0)
    connection.cursor ().execute ("VACUUM FULL ANALYZE")
    log (logging.INFO, ''.join (connection.notices))


def print_stats (dba, parameters):

    with dba.engine.begin () as conn:

        res = execute (conn, "SELECT count (distinct hs) FROM att", parameters)
        hs = res.scalar ()
        log (logging.INFO, "hs       = {cnt}".format (cnt = hs))

        res = execute (conn, "SELECT count (*) FROM (SELECT DISTINCT anfadr, endadr FROM att) AS sq", parameters)
        passages = res.scalar ()
        log (logging.INFO, "passages = {cnt}".format (cnt = passages))

        log (logging.INFO, "hs * passages      = {cnt}".format (cnt = hs * passages))

        res = execute (conn, "SELECT count(*) FROM att", parameters)
        att = res.scalar ()
        res = execute (conn, "SELECT count(*) FROM lac", parameters)
        lac = res.scalar ()

        log (logging.INFO, "rows in att        = {cnt}".format (cnt = att))
        log (logging.INFO, "rows in lac        = {cnt}".format (cnt = lac))

        debug (conn, 'Table Sizes', """
        SELECT *, pg_size_pretty(total_bytes) AS total
            , pg_size_pretty(index_bytes) AS INDEX
            , pg_size_pretty(toast_bytes) AS toast
            , pg_size_pretty(table_bytes) AS TABLE
          FROM (
          SELECT *, total_bytes-index_bytes-COALESCE(toast_bytes,0) AS table_bytes FROM (
              SELECT c.oid,nspname AS table_schema, relname AS TABLE_NAME
                      , c.reltuples AS row_estimate
                      , pg_total_relation_size(c.oid) AS total_bytes
                      , pg_indexes_size(c.oid) AS index_bytes
                      , pg_total_relation_size(reltoastrelid) AS toast_bytes
                  FROM pg_class c
                  LEFT JOIN pg_namespace n ON n.oid = c.relnamespace
                  WHERE relkind = 'r'
          ) a
        ) a where table_schema = 'public' order by table_bytes desc;
        """, parameters)


if __name__ == '__main__':

    parser = argparse.ArgumentParser (description='Prepare a database for CBGM')

    parser.add_argument ('profile', metavar='PROFILE', help="the database profile file (required)")

    parser.add_argument ('-v', '--verbose', dest='verbose', action='count',
                         help='increase output verbosity', default=0)
    parser.add_argument ('-r', '--range', default='',
                         help='range of steps (default: all)')

    parser.parse_args (namespace = args)

    config = tools.config_from_pyfile (args.profile)

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
    LOG_LEVELS = { 0: logging.CRITICAL, 1: logging.ERROR, 2: logging.WARN, 3: logging.INFO, 4: logging.DEBUG }
    args.log_level = LOG_LEVELS.get (args.verbose, logging.CRITICAL)
    parameters = dict ()
    parameters['target_db'] = tools.quote (config['PGDATABASE'])
    parameters['source_db'] = tools.quote (config['MYSQL_ECM_DB'])
    parameters['src_vg_db'] = tools.quote (config['MYSQL_VG_DB'])

    logging.getLogger ().setLevel (args.log_level)
    formatter = logging.Formatter (fmt = '%(relativeCreated)d - %(levelname)s - %(message)s')

    stderr_handler = logging.StreamHandler ()
    stderr_handler.setFormatter (formatter)
    logging.getLogger ().addHandler (stderr_handler)

    file_handler = logging.FileHandler ('prepare4cbgm.log')
    file_handler.setFormatter (formatter)
    logging.getLogger ().addHandler (file_handler)

    if (args.log_level == logging.INFO):
        # sqlalchemy is way too verbose on level INFO
        sqlalchemy_logger = logging.getLogger ('sqlalchemy.engine')
        sqlalchemy_logger.setLevel (logging.WARN)

    dbsrc1 = db_tools.MySQLEngine      (config['MYSQL_GROUP'], config['MYSQL_ECM_DB'])
    dbsrc2 = db_tools.MySQLEngine      (config['MYSQL_GROUP'], config['MYSQL_VG_DB'])
    dbdest = db_tools.PostgreSQLEngine (**config)

    db.fdw ('app_fdw', db.Base.metadata,  dbdest, dbsrc1)
    db.fdw ('var_fdw', db.Base2.metadata, dbdest, dbsrc2)

    v = CBGM_Params ()
    try:
        for step in range (args.range[0], args.range[1] + 1):
            if step == 1:
                log (logging.INFO, "Step  1 : Creating tables ...")

                db.Base.metadata.drop_all (dbdest.engine)
                db.Base.metadata.create_all (dbdest.engine)

                step01  (dbsrc1, dbdest, parameters)
                step01b (dbdest, parameters)
                log (logging.INFO, "Step  1c: Data entry fixes ...")
                step01c (dbdest, parameters)
                continue
            if step == 2:
                log (logging.INFO, "Step  2 : Cleanup korr and lekt ...")
                step02 (dbdest, parameters)
                continue
            if step == 5:
                log (logging.INFO, "Step  5: Processing Commentaries ...")
                save_readings (dbdest, parameters)
                step05 (dbdest, parameters)
                continue
            if step == 6:
                log (logging.INFO, "Step  6 : Delete later hands ...")
                step06 (dbdest, parameters)
                log (logging.INFO, "Step  6b: Delete [CLTV*] from HS ...")
                step06b (dbdest, parameters)
                continue
            if step == 7:
                log (logging.INFO, "Step  7 : Fix 'zw' ...")
                step07 (dbdest, parameters)
                continue
            if step == 8:
                log (logging.INFO, "Step  8 : Deleting passages without variants ...")
                delete_passages_without_variants (dbdest, parameters)
                continue
            if step == 9:
                if args.verbose >= 1:
                    log (logging.INFO, "Step  9 : Printing stats ...")
                    print_stats (dbdest, parameters)
                continue

            if step == 31:
                log (logging.INFO, "Step 31 : Creating CBGM tables ...")
                db.Base2.metadata.drop_all   (dbdest.engine)
                db.Base2.metadata.create_all (dbdest.engine)
                copy_genealogical_data (dbsrc2, dbdest, parameters)

            if step == 32:
                log (logging.INFO, "Step 32 : Filling the Passages table ...")
                fill_passages_table (dbdest, parameters)

                log (logging.INFO, "          Filling the Manuscripts table ...")
                fill_manuscripts_table (dbdest, parameters)

                log (logging.INFO, "          Filling the Readings table ...")
                fill_readings_table (dbdest, parameters)

                log (logging.INFO, "          Filling the Cliques table ...")
                fill_cliques_table (dbdest, parameters)

            if step == 33:
                log (logging.INFO, "Step 33 : Filling the Apparatus table with a positive apparatus ...")
                fill_apparatus_table (dbdest, parameters)

                log (logging.INFO, "          Building Byzantine text ...")
                build_byzantine_text (dbdest, parameters)

                log (logging.INFO, "          Filling the LocStem table ...")
                fill_locstem_table (dbdest, parameters)

            if step == 37:
                log (logging.INFO, "Step 37 : Creating the labez matrix ...")
                create_labez_matrix (dbdest, parameters, v)

                log (logging.INFO, "          Calculating mss similarity pre-co ...")
                calculate_mss_similarity_preco (dbdest, parameters, v)

                log (logging.INFO, "          Calculating mss similarity post-co ...")
                calculate_mss_similarity_postco (dbdest, parameters, v)

                continue

            if step == 99:
                log (logging.INFO, "Step 99 : Vacuum ...")
                vacuum (dbdest, parameters)

    except KeyboardInterrupt:
        pass

    log (logging.INFO, "          Done")
