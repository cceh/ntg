# -*- encoding: utf-8 -*-

"""This module contains the sqlalchemy classes that create the database structure
we need for doing the CBGM and running the application server.

"""

from sqlalchemy import String, Integer, Float, Boolean, DateTime, Column, Index, ForeignKey
from sqlalchemy import UniqueConstraint, CheckConstraint, ForeignKeyConstraint, PrimaryKeyConstraint
from sqlalchemy.dialects.postgresql import TSTZRANGE
from sqlalchemy.ext import compiler
from sqlalchemy.ext.declarative import declarative_base, declared_attr
from sqlalchemy.schema import DDLElement
from sqlalchemy.sql import text
from sqlalchemy_utils import IntRangeType

# let sqlalchemy manage our views

class CreateView (DDLElement):
    def __init__ (self, name, sql):
        self.name = name
        self.sql = sql.strip ()

class DropView (DDLElement):
    def __init__ (self, name):
        self.name = name

@compiler.compiles(CreateView)
def compile (element, compiler, **kw):
    return 'CREATE OR REPLACE VIEW %s AS %s' % (element.name, element.sql)

@compiler.compiles(DropView)
def compile (element, compiler, **kw):
    # Use CASCADE to drop dependent views because we drop the views in the same
    # order as we created them instead of correctly using the reverse order.
    return 'DROP VIEW IF EXISTS %s CASCADE' % (element.name)

def view (name, metadata, sql):
    CreateView (name, sql).execute_at ('after-create', metadata)
    DropView (name).execute_at ('before-drop', metadata)


# let sqlalchemy manage our functions

class CreateFunction (DDLElement):
    def __init__ (self, name, params, returns, sql, **kw):
        self.name       = name
        self.params     = params
        self.returns    = returns
        self.sql        = sql.strip ()
        self.language   = kw.get ('language', 'SQL')
        self.volatility = kw.get ('volatility', 'VOLATILE')

class DropFunction (DDLElement):
    def __init__ (self, name, params):
        self.name   = name
        self.params = params

@compiler.compiles(CreateFunction)
def compile (element, compiler, **kw):
    return 'CREATE OR REPLACE FUNCTION {name} ({params}) RETURNS {returns} LANGUAGE {language} {volatility} AS $$ {sql} $$'.format (**element.__dict__)

@compiler.compiles(DropFunction)
def compile (element, compiler, **kw):
    return 'DROP FUNCTION IF EXISTS {name} ({params}) CASCADE'.format (**element.__dict__)

def function (name, metadata, params, returns, sql, **kw):
    CreateFunction (name, params, returns, sql, **kw).execute_at ('after-create', metadata)
    DropFunction (name, params).execute_at ('before-drop', metadata)


# let sqlalchemy manage our foreign data wrappers

class CreateFDW (DDLElement):
    def __init__ (self, name, pg_db, mysql_db):
        self.name     = name
        self.pg_db    = pg_db
        self.mysql_db = mysql_db

class DropFDW (DDLElement):
    def __init__ (self, name, pg_db, mysql_db):
        self.name     = name
        self.pg_db    = pg_db
        self.mysql_db = mysql_db

@compiler.compiles(CreateFDW)
def compile (element, compiler, **kw):
    pp = element.pg_db.params
    mp = element.mysql_db.params
    return '''
    CREATE SCHEMA {name};
    -- Following commands don't work because you have to be superuser:
    -- CREATE EXTENSION mysql_fdw;
    -- GRANT USAGE ON FOREIGN DATA WRAPPER mysql_fdw TO {username};
    CREATE SERVER {name}_server FOREIGN DATA WRAPPER mysql_fdw OPTIONS (host '{host}', port '{port}');
    CREATE USER MAPPING FOR {pg_user} SERVER {name}_server OPTIONS (username '{username}', password '{password}');
    IMPORT FOREIGN SCHEMA "{database}" FROM SERVER {name}_server INTO {name};
    '''.format (name = element.name, pg_database = pp['database'], pg_user = pp['user'], **mp)

@compiler.compiles(DropFDW)
def compile (element, compiler, **kw):
    pp = element.pg_db.params
    mp = element.mysql_db.params
    return '''
    DROP SCHEMA IF EXISTS {name} CASCADE;
    DROP USER MAPPING IF EXISTS FOR {pg_user} SERVER {name}_server;
    DROP SERVER IF EXISTS {name}_server;
    '''.format (name = element.name, pg_database = pp['database'], pg_user = pp['user'], **mp)

def fdw (name, metadata, pg_database, mysql_db):
    CreateFDW (name, pg_database, mysql_db).execute_at ('after-create', metadata)
    DropFDW (name, pg_database, mysql_db).execute_at ('before-drop', metadata)


# let sqlalchemy manage generic stuff like triggers, aggregates, unique partial indices

class CreateGeneric (DDLElement):
    def __init__ (self, create_cmd):
        self.create = create_cmd

class DropGeneric (DDLElement):
    def __init__ (self, drop_cmd):
        self.drop = drop_cmd

@compiler.compiles(CreateGeneric)
def compile (element, compiler, **kw):
    return element.create

@compiler.compiles(DropGeneric)
def compile (element, compiler, **kw):
    return element.drop

def generic (metadata, create_cmd, drop_cmd):
    CreateGeneric (create_cmd).execute_at ('after-create', metadata)
    DropGeneric (drop_cmd).execute_at ('before-drop', metadata)


# Input tables from the Nestle-Aland database

Base = declarative_base ()

CreateGeneric ('CREATE SCHEMA ntg').execute_at ('before-create', Base.metadata)
DropGeneric ('DROP SCHEMA IF EXISTS ntg CASCADE').execute_at ('after-drop', Base.metadata)

Base.metadata.schema = 'ntg'

class Att (Base):
    r"""Input buffer table for the Nestle-Aland ECM_Acts*GVZ tables.

    The Nestle-Aland database contains one table for each chapter (for
    historical reasons). As first step we copy those many tables into one big
    table, this one.

    This table contains a `negative apparatus <transform-positive>` of all
    manuscripts.  For the CBGM the data in this table has to be normalised into
    our database structure and converted into a positive apparatus.

    .. sauml::
       :include: att

    .. _att:

    .. attribute:: hsnr

       Interne Handschriftnummer.

    .. attribute:: hs

       Siglum der Handschrift.  An das Siglum werden :ref:`Suffixe <suffix>`
       angehängt, die die Hand und die Lesung bezeichnen.  Im Laufe der
       Verarbeitung werden die Lesarten reduziert, bis nur eine Lesart pro
       Handschrift übrigbleibt.  Parallel dazu werden die Suffixe von den Siglen
       entfernt.

    .. attribute:: begadr, endadr

       Zusammengesetzt aus Buch, Kapitel, Vers, Wort.  Es werden Wörter und
       Zwischenräume gezählt.  Gerade Zahlen bezeichnen ein Wort, ungerade einen
       Zwischenraum.

    .. attribute:: labez

       See the :ref:`description of this field in table readings <labez>`.

    .. attribute:: labezsuf

       Contains auxiliary information about the reading:

       .. data:: f

          Fehler.  The reading is considered a scribal error.

       .. data:: o

          Orthographicum.  The reading is considered an orthographical variant,
          eg. a variant place name.

       If the labez is 'zw' labezsuf contains a "/"-separated list of possible
       readings, eg. "a/b_o/c_f" means this reading may be 'a' or an
       orthographicum of 'b' or a scribal error of 'c'.

    .. _suffix:

    .. attribute:: suffix

       .. data:: \*

          Erste, ursprüngliche Hand

       .. data:: C*

          Von erster Hand korrigiert

       .. data:: C1

          Erster Korrektor (Korrektoren der ersten Stunde)

       .. data:: C2

          Zweiter Korrektor (Korrektoren aus späteren Jahrhunderten)

       .. data:: C

          Korrektor (Korrektor aus ungewisser Epoche)

       .. data:: L1, L2

          Unterschiedliche Lesungen in einem Lektionar.  L2 ist für die CBGM
          nicht relevant.

       .. data:: T1, T2

          Unterschiedliche Lesungen des Textes der ersten Hand.  Die erste Hand
          hat diese Passagen mehrmals abgeschrieben, vielleicht aus
          unterschiedlicher Quelle.  Bei fehlender Übereinstimmung muß 'zw'
          gesetzt werden.

       .. data:: A

          Vom Schreiber selbst gekennzeichnete alternative Lesart.  Für die CBGM
          nicht relevant.

       .. data:: K

          Varianten im Kommentar einer Handschrift.  Für die CBGM nicht relevant.

       .. data:: s, s1, s2

          (supplement) Nachträgliche Ergänzung verlorener Stellen.  Bei nur
          einer Ergänzung wird 's' verwendet.  Bei mehreren Ergänzungen werden
          's1', 's2', etc. für jeweils einen Abschnitt verwendet.  Ergänzungen
          können nicht die Authorität der jeweiligen Hs beanspruchen.

       .. data:: V

          (vid, ut videtur) augenscheinlich.  Unsichere aber höchst
          wahrscheinliche Lesung.  Ist für die CBGM als sichere Lesart zu
          akzeptieren.

    .. attribute:: fehler

       Denotes an orthografical error in Catholic Letters.  This became part of
       labezsuf in the other books.

    .. attribute:: base

       Basistext. Nur relevant bei :ref:`Fehlversen <fehlvers>`.

       "'base = b' steht für eine alternative Subvariante (dem Textus receptus)."
       -- prepare4cbgm_10.py

       .. data:: a

          Urtext

       .. data:: b

          :ref:`Textus Receptus <rt>`.

    .. attribute:: comp

       "Eine variierte Stelle ist eine umfasste Stelle, wenn comp = 'x' ist."
       -- prepare4cbgm_10.py

       .. data:: x

          :ref:`Umfaßte Variante <umfasst>`.

    .. attribute:: lekt

       Lektionen in einem Lektionar.

    """

    __tablename__ = 'att'

    id           = Column (Integer,       primary_key = True, autoincrement = True)
    hsnr         = Column (Integer,       nullable = False, index = True)
    hs           = Column (String(32),    nullable = False, index = True)
    begadr       = Column (Integer,       nullable = False, index = True)
    endadr       = Column (Integer,       nullable = False, index = True)
    labez        = Column (String(64),    nullable = False, server_default = '')
    labezsuf     = Column (String(64),    server_default = '')
    certainty    = Column (Float(16),     nullable = False, server_default = '1.0')
    lemma        = Column (String(1024),  server_default = '')
    lesart       = Column (String(1024),  server_default = '')
    labezorig    = Column (String(32),    nullable = False, server_default = '')
    labezsuforig = Column (String(64),    server_default = '')
    suffix2      = Column (String(32),    server_default = '')
    kontrolle    = Column (String(1),     server_default = '')
    fehler       = Column (String(2),     server_default = '')
    suff         = Column (String(32),    server_default = '')
    vid          = Column (String(32),    server_default = '')
    vl           = Column (String(32),    server_default = '')
    korr         = Column (String(32),    server_default = '')
    lekt         = Column (String(32),    server_default = '')
    komm         = Column (String(32),    server_default = '')
    anfalt       = Column (Integer)
    endalt       = Column (Integer)
    labezalt     = Column (String(32),    server_default = '')
    lasufalt     = Column (String(32),    server_default = '')
    base         = Column (String(8),     server_default = '')
    over         = Column (String(1),     server_default = '')
    comp         = Column (String(1),     server_default = '')
    over1        = Column (String(1),     server_default = '')
    comp1        = Column (String(1),     server_default = '')
    printout     = Column (String(32),    server_default = '')
    category     = Column (String(1),     server_default = '')
    passage      = Column (IntRangeType,  nullable = False)

    __table_args__ = (
        Index ('ix_att_begadr_endadr_hs', begadr, endadr, hs),
        Index ('ix_att_hs_passage', hs, passage, unique = True, postgresql_where = certainty == 1.0),
    )


class Lac (Base):
    """Input buffer table for the Nestle-Aland ECM_Acts*GVZLac tables.

    The Nestle-Aland database contains one table for each chapter (for
    historical reasons). As first step we copy those many tables into one big
    table, this one.

    This table contains a list of all lacunae in all manuscripts.  It records
    the start and end of each lacuna.  A lacuna entry generally spans many
    passages in the Att table.

    This table has the same structure as table Att.  For the description of the
    columns see :ref:`table Att <att>`.

    .. sauml::
       :include: lac

    """

    __tablename__ = 'lac'

    id        = Column (Integer,       primary_key = True, autoincrement = True)
    hsnr      = Column (Integer,       nullable = False)
    hs        = Column (String(32),    nullable = False)
    begadr    = Column (Integer,       nullable = False)
    endadr    = Column (Integer,       nullable = False)
    labez     = Column (String(64),    server_default = '')
    labezsuf  = Column (String(64),    server_default = '')
    lemma     = Column (String(1024),  server_default = '')
    lesart    = Column (String(1024),  server_default = '')
    suffix2   = Column (String(32),    server_default = '')
    kontrolle = Column (String(1),     server_default = '')
    fehler    = Column (String(2),     server_default = '')
    suff      = Column (String(32),    server_default = '')
    vid       = Column (String(32),    server_default = '')
    vl        = Column (String(32),    server_default = '')
    korr      = Column (String(32),    server_default = '')
    lekt      = Column (String(32),    server_default = '')
    komm      = Column (String(32),    server_default = '')
    anfalt    = Column (Integer)
    endalt    = Column (Integer)
    labezalt  = Column (String(32),    server_default = '')
    lasufalt  = Column (String(32),    server_default = '')
    base      = Column (String(8),     server_default = '')
    over      = Column (String(1),     server_default = '')
    comp      = Column (String(1),     server_default = '')
    over1     = Column (String(1),     server_default = '')
    comp1     = Column (String(1),     server_default = '')
    printout  = Column (String(32),    server_default = '')
    category  = Column (String(1),     server_default = '')
    passage   = Column (IntRangeType,  nullable = False)

    __table_args__ = (
        Index ('ix_lac_passage_gist', passage, postgresql_using = 'gist'),
        UniqueConstraint (hs, passage)
    )


function ('char_labez', Base.metadata, 'l INTEGER', 'CHAR (3)', '''
    SELECT CASE WHEN l > 0 THEN chr (l + 96) ELSE 'z' END
    ''', volatility = 'IMMUTABLE')

function ('ord_labez', Base.metadata, 'l CHAR (2)', 'INTEGER', '''
    SELECT CASE WHEN ascii (l) >= 122 THEN 0 ELSE ascii (l) - 96 END
    ''', volatility = 'IMMUTABLE')

function ('adr2bk_id', Base.metadata, 'adr INTEGER', 'INTEGER', '''
    SELECT (adr / 10000000)
    ''', volatility = 'IMMUTABLE')

function ('adr2chapter', Base.metadata, 'adr INTEGER', 'INTEGER', '''
    SELECT ((adr / 100000) %% 100)
    ''', volatility = 'IMMUTABLE')

function ('adr2verse', Base.metadata, 'adr INTEGER', 'INTEGER', '''
    SELECT ((adr / 1000) %% 100)
    ''', volatility = 'IMMUTABLE')

function ('adr2word', Base.metadata, 'adr INTEGER', 'INTEGER', '''
    SELECT (adr %% 1000)
    ''', volatility = 'IMMUTABLE')


# Tables for the CBGM / App Server

Base2 = declarative_base ()
Base2.metadata.schema = 'ntg'

class Manuscripts (Base2):
    """A table that lists all the manuscripts.

    This table lists all the manuscripts of New Testament that we have collated
    for the edition.

    .. sauml::
       :include: manuscripts

    .. attribute:: ms_id

       The primary key.  We use a surrogate integer key because we need to
       interface with numpy, which only allows for integer row and column
       indices.  If we every lose this requirement, hsnr will become our primary
       key.

    .. attribute:: hsnr

        The project-internal number of the manuscript.

        This is a six-digit number. The first digit encodes the type of the
        manuscript: 1 = papyrus, 2 = uncial, 3 = minuscule, 4 = lectionary, 5 =
        patristic citations and versions.  The next 4 digits are taken from the
        digits of the Gregory-Aland number, eg. P45 would yield 0045.  The last
        digit encodes supplements: 0 = original ms., 1 = first supplement, 2 =
        second supplement.

        N.B. Patristic citations and versions are not used in the CBGM, and thus
        purged from the database.

    .. attribute:: hs

        The Gregory-Aland number of the manuscript. eg. 'P45', '03', or '1739'.

    """

    __tablename__ = 'manuscripts'

    ms_id     = Column (Integer,       primary_key = True, autoincrement = True)
    hsnr      = Column (Integer,       nullable = False, unique = True)
    hs        = Column (String (32),   nullable = False, unique = True)


class Books (Base2):
    """A table that lists all the books of the New Testament.

    This table lists all the books of the NT and the book id given to them.

    .. sauml::
       :include: books

    .. attribute:: bk_id

        The book id: 1 - 27 (Matthew - Revelation).

    .. attribute:: siglum

        The book siglum, eg. 'Mt'

    .. attribute:: book

        The book name, eg. 'Matthew'

    .. attribute:: passage

        The book extent in passages.

    """

    __tablename__ = 'books'

    bk_id     = Column (Integer,       primary_key = True, autoincrement = True)

    siglum    = Column (String,        nullable = False)
    book      = Column (String,        nullable = False)
    passage   = Column (IntRangeType,  nullable = False)

    __table_args__ = (
        UniqueConstraint (siglum),
        UniqueConstraint (book),
        Index ('ix_books_passage_gist', passage, postgresql_using = 'gist'),
    )


class Passages (Base2):
    """A table that lists the variant passages.

    This table lists all the passages we established during the collation of the
    manuscripts.  Passages that are the same in all manuscripts (invariant) are
    purged because they are irrelevant to the CBGM.

    .. sauml::
       :include: passages

    .. attribute:: pass_id

       The primary key.  We use a surrogate integer key because we need to
       interface with numpy, which only allows for integer row and column
       indices.  If we every lose this requirement, passage will become our
       primary key (but join performance should also be considered).

    .. attribute:: passage

        The extent of the passage.

        The beginning and end of every passage is encoded in this way:

          book id * 10,000,000 +
          chapter *    100,000 +
          verse   *      1,000 +
          word    *          2

        Words are always even and the space between to words is always odd.

    .. attribute:: variant

        True if this passage is a variant passage.  (It has at least two
        different certain readings.)

    .. attribute:: spanning

        True if this passage is spanning other passages.

    .. attribute:: spanned

        True if this passage is spanned by other passages.

    .. attribute:: fehlvers

        True if this passage is a later addition, eg. the pericope adulterae.

        Only set if the passages is spanned.

    """

    __tablename__ = 'passages'

    pass_id   = Column (Integer,       primary_key = True, autoincrement = True)

    bk_id     = Column (Integer,       nullable = False)

    begadr    = Column (Integer,       nullable = False)
    endadr    = Column (Integer,       nullable = False)
    passage   = Column (IntRangeType,  nullable = False)

    variant   = Column (Boolean,       nullable = False, server_default = 'False')
    spanning  = Column (Boolean,       nullable = False, server_default = 'False')
    spanned   = Column (Boolean,       nullable = False, server_default = 'False')
    fehlvers  = Column (Boolean,       nullable = False, server_default = 'False')

    __table_args__ = (
        ForeignKeyConstraint ([bk_id], ['books.bk_id']),
        UniqueConstraint (passage, name = 'unique_passages_passage'), # needs name
        Index ('ix_passages_passage_gist', passage, postgresql_using = 'gist'),
    )


class Readings (Base2):
    """A table that contains the different readings found at each passage.

    First scribal errors are corrected and orthographical differences are
    normalized, then equal readings are grouped.  Each group of readings is
    assigned an id, the 'labez'.

    .. sauml::
       :include: readings

    .. _labez:

    .. attribute:: labez

        (LesArtBEZeichnung).  Usually 'a' indicates the original reading, while
        'b'...'y' indicate readings relegated to the apparatus, although this is
        not necessarily so.  Exceptions are the :ref:`Fehlverse <fehlvers>` and
        the cases where no original reading could be assessed.

        Readings starting with 'z' have special meaning:

        .. data:: zu

            Hier nicht zitierbar aufgrund einer übergreifenden Variante.  Diese
            umfaßte Variante wurde schon in der umfassenden Variante
            verzeichnet.  Entspricht in der ECM einem Pfeil nach oben.  In der
            CBGM ist 'zu' wie 'zz' zu behandeln.

        .. data:: zv

            There is an illegible addition in the manuscript(s) cited which
            makes it impossible to ascribe it to a known variant.

        .. data:: zw

            What remains of the text of the manuscript(s) cited would allow
            reconstruction in agreement with two or more different variants.
            Entspricht in der ECM einem Doppelpfeil nach links-rechts.

            The reading 'zw' is used only in the Att table.  In this table each
            questionable reading will get its own entry with a certainty < 1.0.

        .. data:: zz

            The reading is too lacunose to be identified.

            Alle Verzeichnungen, die aus der Tabelle der Lacunae erzeugt wurden,
            erhalten labez = 'zz'.

            Ein Wort steht nicht in der systematischen Lückenliste wenn
            mindestens ein Buchstabe vorhanden ist.  In diesem Fall steht es in
            der stellenbezogenen Lückenliste.

        Caveat: die Lesart der Handschrift 'A' kann trotz negativem Apparat in
        der Tabelle Att in derselben Passage mehrmals vorkommen, weil an einigen
        Stellen im Nestle-Aland ein positiver Apparat benutzt wurde.

    .. attribute:: lesart

        The normalized reading.  Scribal errors are silently corrected and
        orthographic variants are normalized.  Following abbreviations are used:

        .. data:: om

          Missing text (omissio).  The scribe did not write any text.

        .. data:: NULL

          Missing substrate (lacuna).  The manuscript is damaged or missing.
    """

    __tablename__ = 'readings'

    pass_id   = Column (Integer,       nullable = False)
    labez     = Column (String (3),    nullable = False)

    lesart    = Column (String (1024))

    __table_args__ = (
        PrimaryKeyConstraint (pass_id, labez),
        ForeignKeyConstraint ([pass_id], ['passages.pass_id']),
    )


class Apparatus (Base2):
    """A table that contains the `positive apparatus <transform-positive>`.

    .. sauml::
       :include: apparatus

    .. attribute:: cbgm

        True if this entry is eligible for CBGM, eg. is by the orginal scribe
        and is 100% certain.  There can be only one entry eligible for CBGM for
        every manuscript and passage.

    .. attribute:: labezsuf

        Contains auxiliary information about the reading:

        .. data:: f

            Fehler.  The reading is considered a scribal error.

        .. data:: o

           Orthographicum.  The reading is considered an orthographical variant,
           eg. a variant place name.

    .. attribute:: certainty

        Certainty of the reading for the purposes of the CBGM.  Only readings
        with a certainty of 1.0 are used by the CBGM. A certainty of 1.0 is
        given if the reading unequivocally witnesses for one labez.

        There can be only one reading with a certainty of 1.0, but multiple
        readings with certainty < 1.0, all of them summing to no more than 1.0.

    .. attribute:: lesart

        The actual reading offered by the manuscript.  A lacuna is stored as
        NULL.  Omitted text is stored as the empty string.

        This field is also set to NULL if the manuscript offers the same reading
        as recorded in the :class:`~ntg_common.db.Readings` table for the
        manuscript's labez.  (Saves space and can easily be reconstructed.)

        As a rule of thumb: For 'f' and 'o' readings (errors and orthographic
        variants) the actual reading will be inserted.

    .. attribute:: origin

        Used only for debugging.  Shows where this entry in the positive
        apparatus came from.

        .. data:: ATT

           Copied from negative apparatus in att table in
           :meth:`~scripts.cceh.prepare.fill_apparatus_table`.

        .. data:: BYZ

           Deduced `mt` in :meth:`~scripts.cceh.prepare.build_MT_text`.

        .. data:: DEF

           Default value from conversion to positive apparatus in
           :meth:`~scripts.cceh.prepare.fill_apparatus_table`.

        .. data:: LAC

           Unrolled lacuna from lac table in
           :meth:`~scripts.cceh.prepare.fill_apparatus_table`.

        .. data:: LOC

           Deduced from locstem table in
           :meth:`~scripts.cceh.cbgm.build_A_text`.

        .. data:: ZW

           Uncertain reading from unrolling of 'zw' in
           :meth:`~scripts.cceh.prepare.unroll_zw`.

    """

    __tablename__ = 'apparatus'

    ms_id     = Column (Integer,       nullable = False, index = True)
    pass_id   = Column (Integer,       nullable = False)
    labez     = Column (String (3),    nullable = False)

    cbgm      = Column (Boolean,       nullable = False)
    labezsuf  = Column (String (64),   nullable = False, server_default = '')
    certainty = Column (Float (16),    nullable = False, server_default = '1.0')
    lesart    = Column (String (1024), nullable = True,  server_default = None)
    origin    = Column (String (3),    nullable = False)

    __table_args__ = (
        PrimaryKeyConstraint (pass_id, ms_id, labez),
        ForeignKeyConstraint ([ms_id], ['manuscripts.ms_id']),
        ForeignKeyConstraint ([pass_id, labez], ['readings.pass_id', 'readings.labez']),
        Index ('ix_apparatus_pass_id_ms_id', pass_id, ms_id, unique = True, postgresql_where = cbgm == True),
        CheckConstraint ('certainty > 0.0 AND certainty <= 1.0'),
        CheckConstraint ('(certainty = 1.0) >= cbgm'),  # cbgm implies 100% certainty
    )


class TTS_Mixin (object):
    # use of declared_attr to create these columns last in table
    @declared_attr
    def sys_period (cls):
        return Column (TSTZRANGE,  nullable = False, server_default = text ('tstzrange (now (), NULL)'))

    @declared_attr
    def user_id_start (cls):
        return Column (Integer,    nullable = False)

    @declared_attr
    def user_id_stop (cls):
        return Column (Integer,    nullable = True)


class Cliques_Mixin (TTS_Mixin):
    pass_id   = Column (Integer,    nullable = False)
    labez     = Column (String (3), nullable = False)
    clique    = Column (String (2), nullable = False, server_default = '1')


class Cliques (Cliques_Mixin, Base2):
    """A table that contains the cliques at every passage

    A clique is a set of strongly related manuscripts that offer the same
    reading.  A reading may have been originated independently more than once,
    but in a clique a reading has been originated only once.

    This is the current table of a transaction state table pair.
    :class:`Cliques_TTS` is the table that contains the past rows.  See
    :ref:`transaction-time state tables<tts>`.

    .. sauml::
       :include: cliques

    .. attribute:: clique

        Name of the Clique.  '1', '2' ...

    .. attribute:: sys_period

       The time period in which this row is valid.  In this table all rows are
       still valid, so the end of the period is not set.

    .. attribute:: user_id_start

       The id of the user making the change at the start of the validity period.
       See: :class:`.User`.

    .. attribute:: user_id_stop

       The id of the user making the change at the end of the validity period.
       See: :class:`.User`.

    """

    __tablename__ = 'cliques'

    __table_args__ = (
        PrimaryKeyConstraint ('pass_id', 'labez', 'clique'),
        ForeignKeyConstraint (['pass_id', 'labez'], ['readings.pass_id', 'readings.labez']),
    )


class Cliques_TTS (Cliques_Mixin, Base2):
    """A table that contains the cliques at every passage

    This is the past table of a transaction state table pair.  :class:`Cliques`
    is the table that contains the current rows.  The structure of the two
    tables is the same.  See :ref:`transaction-time state tables<tts>`.

    """

    __tablename__ = 'cliques_tts'

    __table_args__ = (
        PrimaryKeyConstraint ('pass_id', 'labez', 'clique', 'sys_period'),
    )


class MsCliques_Mixin (TTS_Mixin):
    ms_id         = Column (Integer,    nullable = False, index = True)
    pass_id       = Column (Integer,    nullable = False)
    labez         = Column (String (3), nullable = False)
    clique        = Column (String (2), nullable = False, server_default = '1')


class MsCliques (MsCliques_Mixin, Base2):
    """A table that relates manuscripts and cliques.

    This table records the editorial decisions regarding which manuscripts
    represent each clique.  The editors decide which reading is derived from
    which other reading(s) at each passage.

    This is the current table of a transaction state table pair.
    :class:`MsCliques_TTS` is the table that contains the past rows.  See
    :ref:`transaction-time state tables<tts>`.

    .. sauml::
       :include: ms_cliques

    .. attribute:: labez, clique

       The clique this manuscript represents.

    .. attribute:: sys_period

       The time period in which this row is valid.  In this table all rows are
       still valid, so the end of the period is not set.

    .. attribute:: user_id_start

       The id of the user making the change at the start of the validity period.
       See: :class:`.User`.

    .. attribute:: user_id_stop

       The id of the user making the change at the end of the validity period.
       See: :class:`.User`.

    """

    __tablename__ = 'ms_cliques'

    __table_args__ = (
        # Apparatus can have more than one labez per passage per manuscript
        PrimaryKeyConstraint ('ms_id', 'pass_id', 'labez'),
        ForeignKeyConstraint (['ms_id', 'pass_id', 'labez'], ['apparatus.ms_id', 'apparatus.pass_id', 'apparatus.labez'],
                              deferrable = True),
        ForeignKeyConstraint (['pass_id', 'labez', 'clique'], ['cliques.pass_id', 'cliques.labez', 'cliques.clique']),
    )


class MsCliques_TTS (MsCliques_Mixin, Base2):
    """A table that relates manuscripts and cliques.

    This is the past table of a transaction state table pair.
    :class:`MsCliques` is the table that contains the current rows.  The
    structure of the two tables is the same.  See :ref:`transaction-time state
    tables<tts>`.

    """

    __tablename__ = 'ms_cliques_tts'

    __table_args__ = (
        PrimaryKeyConstraint ('ms_id', 'pass_id', 'sys_period'),
    )


class LocStem_Mixin (TTS_Mixin):
    pass_id       = Column (Integer,    nullable = False)
    labez         = Column (String (3), nullable = False)
    clique        = Column (String (2), nullable = False, server_default = '1')
    source_labez  = Column (String (3), nullable = False)
    source_clique = Column (String (2), nullable = False, server_default = '1')


class LocStem (LocStem_Mixin, Base2):
    """A table that contains the priority of the cliques at each passage

    This table contains one DAG (directed acyclic graph) of cliques for each
    passage.  The editors decide from which other clique(s) each clique is
    derived, or if it is original.

    This is the current table of a transaction state table pair.
    :class:`LocStem_TTS` is the table that contains the past rows.  See
    :ref:`transaction-time state tables<tts>`.


    .. sauml::
       :include: locstem

    .. attribute:: labez, clique

        The younger clique which was derived from the older clique.

    .. attribute:: source_labez, source_clique

        The older clique that was the source of the younger clique, or '*' if
        the reading is original, or '?' if the source is unknown.

        Note: These columns should have a foreign key constraint into the
        cliques table but do not, because postgres doesn't support partial
        foreign keys and the cliques table does not contain the '*' and '?'
        pseudo-cliques.

    .. attribute:: sys_period

       The time period in which this row is valid.  In this table all rows are
       still valid, so the end of the period is not set.

    .. attribute:: user_id_start

       The id of the user making the change at the start of the validity period.
       See: :class:`.User`.

    .. attribute:: user_id_stop

       The id of the user making the change at the end of the validity period.
       See: :class:`.User`.

    """

    __tablename__ = 'locstem'

    __table_args__ = (
        PrimaryKeyConstraint ('pass_id', 'labez', 'clique', 'source_labez', 'source_clique'),
        Index ('ix_locstem_unique_original', 'pass_id', unique = True,
               postgresql_where = text ("source_labez = '*'")),
        ForeignKeyConstraint (['pass_id', 'labez', 'clique'],
                              ['cliques.pass_id', 'cliques.labez', 'cliques.clique']),
        CheckConstraint ('labez != source_labez', name='check_same_source'),
    )


class LocStem_TTS (LocStem_Mixin, Base2):
    """A table that contains the priority of the cliques at each passage

    This is the past table of a transaction state table pair.  :class:`LocStem`
    is the table that contains the current rows.  The structure of the two
    tables is the same.  See :ref:`transaction-time state tables<tts>`.

    """

    __tablename__ = 'locstem_tts'

    __table_args__ = (
        PrimaryKeyConstraint ('pass_id', 'labez', 'clique', 'source_labez', 'source_clique', 'sys_period'),
    )


class Notes_Mixin (TTS_Mixin):
    pass_id   = Column (Integer, nullable = False)
    note      = Column (String,  nullable = False)


class Notes (Notes_Mixin, Base2):
    """A table that contains editorial notes attached to passages.

    This is the current table of a transaction state table pair.
    :class:`Notes_TTS` is the table that contains the past rows.  See
    :ref:`transaction-time state tables<tts>`.

    """

    __tablename__ = 'notes'

    __table_args__ = (
        PrimaryKeyConstraint ('pass_id'),
        ForeignKeyConstraint (['pass_id'], ['passages.pass_id']),
    )


class Notes_TTS (Notes_Mixin, Base2):
    """A table that contains editorial notes attached to passages.

    This is the past table of a transaction state table pair.  :class:`Notes` is
    the table that contains the current rows.  The structure of the two tables
    is the same.  See :ref:`transaction-time state tables<tts>`.

    """

    __tablename__ = 'notes_tts'

    __table_args__ = (
        PrimaryKeyConstraint ('pass_id', 'sys_period'),
    )


class Import_Cliques (Cliques_Mixin, Base2):
    """A table to help importing of saved state.

    This table is used only by the load_edits.py script.
    """

    __tablename__ = 'import_cliques'

    pass_id = Column (Integer)
    passage = Column (IntRangeType, nullable = False)

    __table_args__ = (
        PrimaryKeyConstraint ('passage', 'labez', 'clique', 'sys_period'),
    )


class Import_MsCliques (MsCliques_Mixin, Base2):
    """A table to help importing of saved state.

    This table is used only by the load_edits.py script.
    """

    __tablename__ = 'import_ms_cliques'

    pass_id = Column (Integer)
    ms_id   = Column (Integer)
    passage = Column (IntRangeType, nullable = False)
    hsnr    = Column (Integer,      nullable = False)

    __table_args__ = (
        PrimaryKeyConstraint ('hsnr', 'passage', 'labez', 'sys_period'),
    )


class Import_LocStem (LocStem_Mixin, Base2):
    """A table to help importing of saved state.

    This table is only used by the load_edits.py script.

    """

    __tablename__ = 'import_locstem'

    pass_id = Column (Integer)
    passage = Column (IntRangeType, nullable = False)

    __table_args__ = (
        PrimaryKeyConstraint ('passage', 'labez', 'clique', 'source_labez', 'source_clique', 'sys_period'),
    )


class Import_Notes (Notes_Mixin, Base2):
    """A table to help importing of saved state.

    This table is only used by the load_edits.py script.

    """

    __tablename__ = 'import_notes'

    pass_id = Column (Integer)
    passage = Column (IntRangeType, nullable = False)

    __table_args__ = (
        PrimaryKeyConstraint ('passage', 'sys_period'),
    )


class Ranges (Base2):
    """A table that contains the ranges of passages for the CBGM.

    The CBGM is agnostic about the division in books and chapters of the NT.  It
    can be run on any range of passages (in theory even on sets of non-contiguous
    passages, although not yet in this implementation).

    This table contains all ranges we are interested in, that is, one range for
    each chapter of each book and also one range for each whole book.  The
    ranges corresponding to chapters are named by the chapter number, '1', '2',
    ...  The whole book range is called 'All'.

    .. sauml::
       :include: ranges

    .. attribute:: range

        The name of the range, eg. '1' for Chapter 1.

    .. attribute:: passage

        The extent of the range.

    """

    __tablename__ = 'ranges'

    rg_id     = Column (Integer,          primary_key = True, autoincrement = True)

    bk_id     = Column (Integer,          nullable = False)

    range_    = Column ('range', String,  nullable = False)

    passage   = Column (IntRangeType,     nullable = False)

    __table_args__ = (
        ForeignKeyConstraint ([bk_id], ['books.bk_id']),
        Index ('ix_ranges_passage_gist', passage, postgresql_using = 'gist'),
    )


class Ms_Ranges (Base2):
    """A table that contains CBGM output related to each manuscript.

    Here we hold values that are calculated by CBGM related to one manuscript.

    .. sauml::
       :include: ms_ranges

    .. attribute:: length

        Calculated: no. of defined passages in the manuscript inside this range.

    """

    __tablename__ = 'ms_ranges'

    rg_id      = Column (Integer, nullable = False)
    ms_id      = Column (Integer, nullable = False)

    length     = Column (Integer)

    __table_args__ = (
        PrimaryKeyConstraint (rg_id, ms_id),
        ForeignKeyConstraint ([ms_id], ['manuscripts.ms_id']),
        ForeignKeyConstraint ([rg_id], ['ranges.rg_id']),
    )


class Affinity (Base2):
    r"""A table that contains CBGM output related to each pair of manuscripts.

    This table contains the actual results of applying the CBGM: the priority of
    the manuscripts.  It has one row for each pair of manuscripts that have at
    least one passage in common and each range we are interested in.

    Two sets of data are included, one for the recursive interpretation of the
    locstem data, and one for the backward-compatible non-recurisve
    interpretation (with 'p\_' prefix).

    .. sauml::
       :include: affinity

    .. attribute:: common

        No. of passages defined in both manuscripts.

    .. attribute:: equal

        No. of passages that have the same reading in both manuscripts.

    .. attribute:: affinity

        equal / common

    .. attribute:: older

        No. of passages that have an older reading in ms1.

    .. attribute:: newer

        No. of passages that have an newer reading in ms1.

    .. attribute:: unclear

        No. of passages where it is unclear which reading is older.

    """

    __tablename__ = 'affinity'

    rg_id      = Column (Integer,       nullable = False)
    ms_id1     = Column (Integer,       nullable = False)
    ms_id2     = Column (Integer,       nullable = False)

    affinity   = Column (Float,         nullable = False, server_default = '0')

    common     = Column (Integer,       nullable = False)
    equal      = Column (Integer,       nullable = False)

    older      = Column (Integer,       nullable = False)
    newer      = Column (Integer,       nullable = False)
    unclear    = Column (Integer,       nullable = False)

    p_older    = Column (Integer,       nullable = False)
    p_newer    = Column (Integer,       nullable = False)
    p_unclear  = Column (Integer,       nullable = False)

    __table_args__ = (
        PrimaryKeyConstraint (rg_id, ms_id1, ms_id2),
        Index ('ix_affinity_rg_id_ms_id2', rg_id, ms_id2),
        ForeignKeyConstraint ([rg_id, ms_id1], ['ms_ranges.rg_id', 'ms_ranges.ms_id']),
        ForeignKeyConstraint ([rg_id, ms_id2], ['ms_ranges.rg_id', 'ms_ranges.ms_id']),
    )


function ('labez_array_to_string', Base2.metadata, 'a CHAR[]', 'CHAR', '''
SELECT array_to_string (a, '/', '')
''', volatility = 'IMMUTABLE')

function ('varnew2labez', Base2.metadata, 'varnew CHAR (2)', 'CHAR', '''
SELECT REGEXP_REPLACE (varnew, '[0-9]+$', '')
''', volatility = 'IMMUTABLE')

function ('varnew2clique', Base2.metadata, 'varnew CHAR (2)', 'CHAR', '''
SELECT COALESCE (NULLIF (REGEXP_REPLACE (varnew, '^[^0-9]+', ''), ''), '1')
''', volatility = 'IMMUTABLE')

function ('labez_clique', Base2.metadata, 'labez CHAR, clique CHAR', 'CHAR', '''
SELECT labez || COALESCE (NULLIF (clique, '1'), '')
''', volatility = 'IMMUTABLE')

function ('reading', Base2.metadata, 'labez CHAR, lesart VARCHAR', 'VARCHAR', '''
SELECT CASE WHEN labez = 'zz' THEN '' WHEN labez = 'zu' THEN 'overlap' ELSE COALESCE (NULLIF (lesart, ''), 'om') END
''', volatility = 'IMMUTABLE')

function ('close_period', Base2.metadata, 'period TSTZRANGE', 'TSTZRANGE', '''
SELECT TSTZRANGE (LOWER (period), NOW ())
''', volatility = 'IMMUTABLE')

generic (Base2.metadata, '''
CREATE AGGREGATE labez_agg (CHAR) (
  sfunc = array_append,
  stype = char[],
  initcond = '{}',
  finalfunc = labez_array_to_string
)
''', '''
DROP AGGREGATE IF EXISTS labez_agg (CHAR) CASCADE
'''
)

view ('ranges_view', Base2.metadata, '''
    SELECT bk.bk_id, bk.siglum, bk.book, ch.rg_id, ch.range, ch.passage
    FROM books bk
    JOIN ranges ch USING (bk_id)
    ''')

view ('ms_ranges_view', Base2.metadata, '''
    SELECT ch.*, mc.ms_id, mc.length
    FROM ms_ranges mc
    JOIN ranges_view ch USING (rg_id)
    ''')

view ('passages_view', Base2.metadata, '''
    SELECT b.bk_id, b.siglum, b.book,
           adr2chapter (p.begadr) AS chapter,
           adr2verse   (p.begadr) AS verse,
           adr2word    (p.begadr) AS word,
           p.pass_id, p.begadr, p.endadr, p.passage, p.variant, p.spanning, p.spanned, p.fehlvers
    FROM passages p
    JOIN books b USING (bk_id)
    ''')

view ('passages_view_lemma', Base2.metadata, '''
    SELECT p.*, COALESCE (rl.lesart, 'undef') AS lemma
    FROM passages_view p
    LEFT JOIN (
      SELECT r.pass_id, r.lesart
      FROM readings r
      JOIN locstem l ON (l.pass_id, l.labez, l.source_labez) = (r.pass_id, r.labez, '*')
    ) rl ON (p.pass_id = rl.pass_id)
    ORDER by p.pass_id;
    ''')

view ('locstem_view', Base2.metadata, '''
    SELECT p.begadr, p.endadr, p.passage, p.fehlvers, locstem.*
    FROM locstem
    JOIN passages p USING (pass_id)
    ''')

view ('readings_view', Base2.metadata, '''
    SELECT p.begadr, p.endadr, p.passage, r.*
    FROM readings r
    JOIN passages p USING (pass_id)
    ''')

view ('cliques_view', Base2.metadata, '''
    SELECT r.begadr, r.endadr, r.passage, r.lesart, q.*
    FROM cliques q
    JOIN readings_view r USING (pass_id, labez)
    ''')

view ('ms_cliques_view', Base2.metadata, '''
    SELECT q.begadr, q.endadr, q.passage, q.lesart, ms.hs, ms.hsnr, mq.*
    FROM ms_cliques mq
    JOIN cliques_view q USING (pass_id, labez, clique)
    JOIN manuscripts ms USING (ms_id)
    ''')

view ('notes_view', Base2.metadata, '''
    SELECT p.begadr, p.endadr, p.passage, p.fehlvers, n.*
    FROM notes n
    JOIN passages p USING (pass_id)
    ''')

view ('apparatus_view', Base2.metadata, '''
    SELECT p.pass_id, p.begadr, p.endadr, p.passage, p.spanning, p.spanned, p.fehlvers,
           ms.ms_id, ms.hs, ms.hsnr,
           a.labez, a.cbgm, a.labezsuf, a.certainty, a.origin,
           COALESCE (a.lesart, r.lesart) AS lesart
    FROM apparatus a
    JOIN readings r     USING (pass_id, labez)
    JOIN passages p     USING (pass_id)
    JOIN manuscripts ms USING (ms_id)
    ''')

view ('apparatus_cliques_view', Base2.metadata, '''
    SELECT a.*, q.clique, labez_clique (q.labez, q.clique) as labez_clique FROM apparatus_view a
    LEFT JOIN ms_cliques q USING (ms_id, pass_id, labez)
    ''')

view ('apparatus_view_agg', Base2.metadata, '''
   SELECT pass_id, ms_id, hs, hsnr,
          MODE () WITHIN GROUP (ORDER BY lesart) AS lesart,
          labez_agg (labez    ORDER BY labez)    AS labez,
          labez_agg (clique   ORDER BY clique)   AS clique,
          labez_agg (labezsuf ORDER BY labezsuf) AS labezsuf,
          labez_agg (labez_clique                ORDER BY labez_clique)            AS labez_clique,
          labez_agg (labez || labezsuf           ORDER BY labez, labezsuf)         AS labez_labezsuf,
          labez_agg (labez || labezsuf || clique ORDER BY labez, labezsuf, clique) AS labez_labezsuf_clique,
          MAX (certainty) AS certainty
   FROM apparatus_cliques_view
   GROUP BY pass_id, ms_id, hs, hsnr
   ''')

view ('affinity_view', Base2.metadata, '''
    SELECT ch.bk_id, ch.rg_id, ch.range, ms_id1, ms_id2, common, equal,
           older, newer, unclear,
           affinity,
           ch1.length AS ms1_length,
           ch2.length AS ms2_length
    FROM affinity aff
    JOIN ranges_view ch USING (rg_id)
    JOIN ms_ranges ch1 ON (aff.ms_id1, aff.rg_id) = (ch1.ms_id, ch1.rg_id)
    JOIN ms_ranges ch2 ON (aff.ms_id2, aff.rg_id) = (ch2.ms_id, ch2.rg_id)
    ''')

view ('affinity_p_view', Base2.metadata, '''
    SELECT ch.bk_id, ch.rg_id, ch.range, ms_id1, ms_id2, common, equal,
           p_older as older, p_newer as newer, p_unclear as unclear,
           affinity,
           ch1.length AS ms1_length,
           ch2.length AS ms2_length
    FROM affinity aff
    JOIN ranges_view ch USING (rg_id)
    JOIN ms_ranges ch1 ON (aff.ms_id1, aff.rg_id) = (ch1.ms_id, ch1.rg_id)
    JOIN ms_ranges ch2 ON (aff.ms_id2, aff.rg_id) = (ch2.ms_id, ch2.rg_id)
    ''')

view ('export_cliques', Base2.metadata, '''
    SELECT passage, labez, clique, sys_period, user_id_start, user_id_stop
    FROM cliques_view
    WHERE user_id_start != 0
    UNION
    SELECT p.passage, labez, clique, sys_period, user_id_start, user_id_stop
    FROM cliques_tts cq
    JOIN passages p USING (pass_id)
    ORDER BY passage, sys_period, labez, clique
    ''')

view ('export_ms_cliques', Base2.metadata, '''
    SELECT passage, hsnr, labez, clique, sys_period, user_id_start, user_id_stop
    FROM ms_cliques_view
    WHERE user_id_start != 0
    UNION
    SELECT p.passage, m.hsnr, labez, clique, sys_period, user_id_start, user_id_stop
    FROM ms_cliques_tts mcq
    JOIN passages p USING (pass_id)
    JOIN manuscripts m USING (ms_id)
    ORDER BY passage, sys_period, hsnr, labez, clique
    ''')

view ('export_locstem', Base2.metadata, '''
    SELECT passage, labez, clique, source_labez, source_clique,
           sys_period, user_id_start, user_id_stop
    FROM locstem_view
    UNION
    SELECT p.passage, labez, clique, source_labez, source_clique,
           sys_period, user_id_start, user_id_stop
    FROM locstem_tts lt
    JOIN passages p USING (pass_id)
    ORDER BY passage, sys_period, labez, clique
    ''')

view ('export_notes', Base2.metadata, '''
    SELECT passage, note, sys_period, user_id_start, user_id_stop
    FROM notes_view
    UNION
    SELECT p.passage, note, sys_period, user_id_start, user_id_stop
    FROM notes_tts
    JOIN passages p USING (pass_id)
    ORDER BY passage, sys_period
    ''')

generic (Base2.metadata, '''
CREATE UNIQUE INDEX IF NOT EXISTS readings_unique_pass_id_lesart ON readings (pass_id, lesart) WHERE labez !~ '^z'
''', '''
DROP INDEX IF EXISTS readings_unique_pass_id_lesart
'''
)


LOCSTEM_REC = '''
WITH RECURSIVE locstem_rec (pass_id, labez, clique, source_labez, source_clique) AS (
  SELECT pass_id, labez, clique, source_labez, source_clique
  FROM locstem i
  WHERE i.pass_id = passage_id AND i.labez = labez1 AND i.clique = clique1
  UNION
  SELECT l.pass_id, l.labez, l.clique, l.source_labez, l.source_clique
  FROM locstem l, locstem_rec r
  WHERE l.pass_id = r.pass_id AND l.labez = r.source_labez AND l.clique = r.source_clique
  )
'''

function ('is_older', Base2.metadata, 'passage_id INTEGER, labez2 CHAR, clique2 CHAR, labez1 CHAR, clique1 CHAR', 'BOOLEAN', LOCSTEM_REC + '''
SELECT EXISTS (SELECT * FROM locstem_rec WHERE source_labez = labez2 AND source_clique = clique2);
''', volatility = 'STABLE')

function ('is_unclear', Base2.metadata, 'passage_id INTEGER, labez1 CHAR, clique1 CHAR', 'BOOLEAN', LOCSTEM_REC + '''
SELECT EXISTS (SELECT * FROM locstem_rec WHERE source_labez = '?');
''', volatility = 'STABLE')

function ('is_p_older', Base2.metadata, 'passage_id INTEGER, labez2 CHAR, clique2 CHAR, labez1 CHAR, clique1 CHAR', 'BOOLEAN', '''
SELECT EXISTS (SELECT * FROM locstem
               WHERE pass_id = passage_id AND
                     labez = labez1 AND clique = clique1 AND
                     source_labez = labez2 AND source_clique = clique2);
''', volatility = 'STABLE')

function ('is_p_unclear', Base2.metadata, 'passage_id INTEGER, labez1 CHAR, clique1 CHAR', 'BOOLEAN', '''
SELECT EXISTS (SELECT * FROM locstem
               WHERE pass_id = passage_id AND
                     labez = labez1 AND clique = clique1 AND
                     source_labez = '?');
''', volatility = 'STABLE')

function ('user_id', Base2.metadata, '', 'INTEGER', '''
SELECT current_setting ('ntg.user_id')::int;
''', volatility = 'STABLE')

# implement automagic TTS on cliques, locstem, ms_cliques, and notes

function ('cliques_trigger_f', Base2.metadata, '', 'TRIGGER', '''
   BEGIN
      IF TG_OP IN ('UPDATE', 'DELETE') THEN
        -- transfer data to tts table
        INSERT INTO cliques_tts (pass_id, labez, clique,
                                 sys_period, user_id_start, user_id_stop)
        VALUES (OLD.pass_id, OLD.labez, OLD.clique,
                close_period (OLD.sys_period), OLD.user_id_start, user_id ());
      END IF;
      IF TG_OP IN ('UPDATE', 'INSERT') THEN
        NEW.sys_period = tstzrange (now (), NULL);
        NEW.user_id_start = user_id ();
        RETURN NEW;
      END IF;
      RETURN OLD;
   END;
''', language = 'plpgsql', volatility = 'VOLATILE')

function ('locstem_trigger_f', Base2.metadata, '', 'TRIGGER', '''
   BEGIN
      IF TG_OP IN ('UPDATE', 'DELETE') THEN
        -- transfer data to tts table
        INSERT INTO locstem_tts (pass_id, labez, clique, source_labez, source_clique,
                                 sys_period, user_id_start, user_id_stop)
        VALUES (OLD.pass_id, OLD.labez, OLD.clique, OLD.source_labez, OLD.source_clique,
                close_period (OLD.sys_period), OLD.user_id_start, user_id ());
      END IF;
      IF TG_OP IN ('UPDATE', 'INSERT') THEN
        NEW.sys_period = tstzrange (now (), NULL);
        NEW.user_id_start = user_id ();
        RETURN NEW;
      END IF;
      RETURN OLD;
   END;
''', language = 'plpgsql', volatility = 'VOLATILE')

function ('ms_cliques_trigger_f', Base2.metadata, '', 'TRIGGER', '''
   BEGIN
      IF TG_OP IN ('UPDATE', 'DELETE') THEN
        -- transfer data to tts table
        INSERT INTO ms_cliques_tts (pass_id, ms_id, labez, clique,
                                    sys_period, user_id_start, user_id_stop)
        VALUES (OLD.pass_id, OLD.ms_id, OLD.labez, OLD.clique,
                close_period (OLD.sys_period), OLD.user_id_start, user_id ());
      END IF;
      IF TG_OP IN ('UPDATE', 'INSERT') THEN
        NEW.sys_period = tstzrange (now (), NULL);
        NEW.user_id_start = user_id ();
        RETURN NEW;
      END IF;
      RETURN OLD;
   END;
''', language = 'plpgsql', volatility = 'VOLATILE')

function ('notes_trigger_f', Base2.metadata, '', 'TRIGGER', '''
   BEGIN
      IF TG_OP IN ('UPDATE', 'DELETE') THEN
        -- transfer data to tts table
        INSERT INTO notes_tts (pass_id, note,
                               sys_period, user_id_start, user_id_stop)
        VALUES (OLD.pass_id, OLD.note,
                close_period (OLD.sys_period), OLD.user_id_start, user_id ());
      END IF;
      IF TG_OP IN ('UPDATE', 'INSERT') THEN
        NEW.sys_period = tstzrange (now (), NULL);
        NEW.user_id_start = user_id ();
        RETURN NEW;
      END IF;
      RETURN OLD;
   END;
''', language = 'plpgsql', volatility = 'VOLATILE')

generic (Base2.metadata, '''
    CREATE TRIGGER cliques_trigger
    BEFORE INSERT OR UPDATE OR DELETE ON cliques
    FOR EACH ROW EXECUTE PROCEDURE cliques_trigger_f ()
''', '''
    DROP TRIGGER IF EXISTS cliques_trigger ON locstem
'''
)

generic (Base2.metadata, '''
    CREATE TRIGGER locstem_trigger
    BEFORE INSERT OR UPDATE OR DELETE ON locstem
    FOR EACH ROW EXECUTE PROCEDURE locstem_trigger_f ()
''', '''
    DROP TRIGGER IF EXISTS locstem_trigger ON locstem
'''
)

generic (Base2.metadata, '''
    CREATE TRIGGER ms_cliques_trigger
    BEFORE INSERT OR UPDATE OR DELETE ON ms_cliques
    FOR EACH ROW EXECUTE PROCEDURE ms_cliques_trigger_f ()
''', '''
    DROP TRIGGER IF EXISTS ms_cliques_trigger ON ms_cliques
'''
)

generic (Base2.metadata, '''
    CREATE TRIGGER notes_trigger
    BEFORE INSERT OR UPDATE OR DELETE ON notes
    FOR EACH ROW EXECUTE PROCEDURE notes_trigger_f ()
''', '''
    DROP TRIGGER IF EXISTS notes_trigger ON notes
'''
)

# implement inserts on view apparatus_cliques_view

function ('apparatus_cliques_view_trigger_f', Base2.metadata, '', 'TRIGGER', '''
   BEGIN
      IF TG_OP = 'INSERT' THEN
        INSERT INTO apparatus  (pass_id, ms_id, labez, lesart, cbgm, origin)
               VALUES (NEW.pass_id, NEW.ms_id, NEW.labez, NEW.lesart, NEW.cbgm, NEW.origin);
        INSERT INTO ms_cliques (pass_id, ms_id, labez, clique)
               VALUES (NEW.pass_id, NEW.ms_id, NEW.labez, NEW.clique);
      ELSIF TG_OP = 'UPDATE' THEN
        SET CONSTRAINTS ALL DEFERRED;
        UPDATE apparatus
        SET pass_id = NEW.pass_id, ms_id = NEW.ms_id, labez = NEW.labez, lesart = NEW.lesart, cbgm = NEW.cbgm, origin = NEW.origin
        WHERE (pass_id, ms_id) = (OLD.pass_id, OLD.ms_id);
        UPDATE ms_cliques
        SET pass_id = NEW.pass_id, ms_id = NEW.ms_id, labez = NEW.labez, clique = NEW.clique
        WHERE (pass_id, ms_id) = (OLD.pass_id, OLD.ms_id);
      ELSIF TG_OP = 'DELETE' THEN
        DELETE FROM ms_cliques
        WHERE (pass_id, ms_id) = (OLD.pass_id, OLD.ms_id);
        DELETE FROM apparatus
        WHERE (pass_id, ms_id) = (OLD.pass_id, OLD.ms_id);
      END IF;
      RETURN NEW;
    END;
''', language = 'plpgsql', volatility = 'VOLATILE')

generic (Base2.metadata, '''
    CREATE TRIGGER apparatus_cliques_view_trigger
    INSTEAD OF INSERT OR UPDATE OR DELETE ON apparatus_cliques_view
    FOR EACH ROW EXECUTE PROCEDURE apparatus_cliques_view_trigger_f ();
''', '''
    DROP TRIGGER IF EXISTS apparatus_cliques_view_trigger ON apparatus_cliques_view
'''
)


Base4 = declarative_base ()
Base4.metadata.schema = 'ntg'

class Nestle (Base4):
    """The Leitzeile from the Nestle-Aland

    Dient der Darstellung der Leitzeile im Navigator.

    .. sauml::
       :include: nestle

    .. _nestle_table:

    .. attribute:: begadr, endadr

       Zusammengesetzt aus Buch, Kapitel, Vers, Wort.  Es werden Wörter und
       Zwischenräume gezählt.  Gerade Zahlen bezeichnen ein Wort, ungerade einen
       Zwischenraum.  In dieser Tabelle sind nur Wörter enthalten, keine
       Zwischenräume.  Jedes Wort hat einen eigenen Eintrag, d.h. für alle
       Einträge gilt: begadr = endadr.

    .. attribute:: lemma

       Das Lemma-Wort in der Leitzeile.

    """

    __tablename__ = 'nestle'

    id        = Column (Integer,       primary_key = True, autoincrement = True)

    begadr    = Column (Integer,       nullable = False)
    endadr    = Column (Integer,       nullable = False)
    passage   = Column (IntRangeType,  nullable = False)

    lemma     = Column (String(1024),  server_default = '')

    __table_args__ = (
        UniqueConstraint (passage, name = 'unique_nestle_passage'), # needs name
        Index ('ix_nestle_passage_gist', passage, postgresql_using = 'gist'),
    )


# Tables for flask_login / flask_user / flask_security / whatever

Base3 = declarative_base ()
Base3.metadata.schema = 'ntg'

class _User ():
    __tablename__ = 'user'

    id           = Column (Integer,      primary_key = True)
    username     = Column (String (50),  nullable = False, unique = True)
    password     = Column (String (255), nullable = False, server_default = '')
    email        = Column (String (255), nullable = False, unique = True)
    active       = Column (Boolean,      nullable = False, server_default = '0')
    confirmed_at = Column (DateTime)
    first_name   = Column (String (100), nullable = False, server_default = '')
    last_name    = Column (String (100), nullable = False, server_default = '')


class _Role ():
    __tablename__ = 'role'

    id          = Column (Integer,      primary_key = True)
    name        = Column (String  (80), unique = True)
    description = Column (String (255), nullable = False, server_default = '')


class _Roles_Users ():
    __tablename__ = 'roles_users'

    id      = Column (Integer, primary_key = True)

    @declared_attr
    def user_id (cls):
        return Column (Integer, ForeignKey ('user.id', ondelete='CASCADE'))

    @declared_attr
    def role_id (cls):
        return Column (Integer, ForeignKey ('role.id', ondelete='CASCADE'))


class User (_User, Base3):
    pass

class Role (_Role, Base3):
    pass

class Roles_Users (_Roles_Users, Base3):
    pass
