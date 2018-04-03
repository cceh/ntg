# -*- encoding: utf-8 -*-

"""This module is for documentation purposes only.  It contains sqlalchemy
classes that show the source database structure.  We never actually use these
classes in the code.

"""

import sqlalchemy

from sqlalchemy import String, Integer, Float, Boolean, DateTime, Column, Index, ForeignKey, text
from sqlalchemy import UniqueConstraint, CheckConstraint, ForeignKeyConstraint, PrimaryKeyConstraint

from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base ()
""" Input tables we only want to document, not use. """


class Acts01GVZ (Base):
    """This table contains a negative apparatus.

    .. sauml:: mysql:///ECM_ActsPh4?read_default_group=ntg
       :include: Acts01GVZ

    """

    __tablename__ = 'Acts01GVZ'

    id          = Column (Integer, primary_key=True)
    BUCH        = Column (Integer)
    KAPANF      = Column (Integer)
    VERSANF     = Column (Integer)
    LEMMA       = Column (String (1024))
    WORTANF     = Column (Integer)
    WORTEND     = Column (Integer)
    LABEZ       = Column (String (32))
    LESART      = Column (String (1024))
    HS          = Column (String (32))
    SUFFIX1     = Column (String (32))
    SUFFIX2     = Column (String (32))
    KONTROLLE   = Column (String (1))
    KAPEND      = Column (Integer, server_default=text("'0'"))
    VERSEND     = Column (Integer, server_default=text("'0'"))
    LABEZSUF    = Column (String (32))
    fehler      = Column (Integer, server_default=text("'0'"))
    HSNR        = Column (Integer)
    SUFF        = Column (String (32))
    VID         = Column (String (32))
    VL          = Column (String (32))
    KORR        = Column (String (32))
    LEKT        = Column (String (32))
    KOMM        = Column (String (32))
    BEGADR      = Column (Integer)
    ENDADR      = Column (Integer)
    ADR         = Column (Integer)
    ANFALT      = Column (Integer)
    ENDALT      = Column (Integer)
    LABEZALT    = Column (String (32))
    LASUFALT    = Column (String (32))
    ZUSATZ      = Column (String (255))
    LesartenKey = Column (Integer, nullable=False, server_default=text("'0'"))
    base        = Column (String (1), server_default=text("''"))
    over        = Column (String (1), server_default=text("''"))
    comp        = Column (String (1), server_default=text("''"))
    over1       = Column (String (1), server_default=text("''"))
    comp1       = Column (String (1), server_default=text("''"))


class Acts01GVZlac (Base):
    """This table contains a list of lacunae.

    .. sauml:: mysql:///ECM_ActsPh4?read_default_group=ntg
       :include: Acts01GVZlac

    """

    __tablename__ = 'Acts01GVZlac'

    id          = Column (Integer,       primary_key=True)
    BUCH        = Column (Integer,       nullable=False)
    KAPANF      = Column (Integer,       nullable=False)
    VERSANF     = Column (Integer,       nullable=False)
    LEMMA       = Column (String (1024), nullable=False)
    WORTANF     = Column (Integer,       nullable=False)
    WORTEND     = Column (Integer)
    LABEZ       = Column (String (255),  nullable=False)
    LESART      = Column (String (1024), nullable=False)
    HS          = Column (String (255))
    SUFFIX1     = Column (String (255))
    SUFFIX2     = Column (String (255))
    KONTROLLE   = Column (String (1))
    KAPEND      = Column (Integer, server_default=text("'0'"))
    VERSEND     = Column (Integer, server_default=text("'0'"))
    LABEZSUF    = Column (String (255))
    fehler      = Column (Integer, server_default=text("'0'"))
    HSNR        = Column (Integer)
    SUFF        = Column (String (255))
    VID         = Column (String (255))
    VL          = Column (String (255))
    KORR        = Column (String (255))
    LEKT        = Column (String (255))
    KOMM        = Column (String (255))
    BEGADR      = Column (Integer)
    ENDADR      = Column (Integer)
    ADR         = Column (Integer)
    ANFALT      = Column (Integer)
    ENDALT      = Column (Integer)
    LABEZALT    = Column (String (255))
    LASUFALT    = Column (String (255))
    ZUSATZ      = Column (String (255))
    printout    = Column (String (255))
    category    = Column (String (1))
    base        = Column (String (1), server_default=text("''"))
    over        = Column (String (1), server_default=text("''"))
    comp        = Column (String (1), server_default=text("''"))
    over1       = Column (String (1), server_default=text("''"))
    comp1       = Column (String (1), server_default=text("''"))


class LocStemEdAct01 (Base):
    """A table that contains the priority of the cliques at each passage

    This table contains the main output of the editors.  The editors decide
    which reading is derived from which other reading(s) at each passage.

    .. sauml:: mysql:///VarGenAtt_ActPh4?read_default_group=ntg
       :include: LocStemEdAct01

    .. attribute:: id

       Primary key

    .. attribute:: varid

       Same as :ref:`labez <labez>`.

    .. attribute:: varnew

       This is the :ref:`labez <labez>` concatenated with the number of the :ref:`split <split>`.

    .. attribute:: s1

       Source of this reading.

    .. attribute:: s2

       Optionally second source of reading.

    .. attribute:: begadr, endar

       The passage.

    .. attribute:: w

       Flag :ref:`"Western Text" <wt>`.  Not needed for the CBGM.

    """

    __tablename__ = 'LocStemdEdAct'

    id     = Column (Integer,    primary_key=True)
    VARID  = Column (String (2), nullable=False, server_default=text ("''"))
    VARNEW = Column (String (2), nullable=False)
    S1     = Column (String (2), nullable=False, server_default=text ("''"))
    S2     = Column (String (2), nullable=False, server_default=text ("''"))
    PRS1   = Column (String (2), nullable=False, server_default=text ("''"))
    PRS2   = Column (String (2), nullable=False, server_default=text ("''"))
    BEGADR = Column (Integer,    nullable=False, server_default=text ("'0'"))
    ENDADR = Column (Integer,    nullable=False, server_default=text ("'0'"))
    CHECK  = Column (String (2), nullable=False, server_default=text ("''"))
    CHECK2 = Column (String (2))
    w      = Column (String (1), server_default=text("''"))


class RdgAct01 (Base):
    """This table contains readings.

    .. sauml:: mysql:///VarGenAtt_ActPh4?read_default_group=ntg
       :include: RdgAct01

    """

    __tablename__ = 'RdgAct'

    id        = Column (Integer,       primary_key=True)
    BUCH      = Column (Integer,       nullable=False, server_default=text ("'0'"))
    KAPANF    = Column (Integer,       nullable=False, server_default=text ("'0'"))
    VERSANF   = Column (Integer,       nullable=False, server_default=text ("'0'"))
    WORTANF   = Column (Integer,       nullable=False, server_default=text ("'0'"))
    KAPEND    = Column (Integer,       nullable=False, server_default=text ("'0'"))
    VERSEND   = Column (Integer,       nullable=False, server_default=text ("'0'"))
    WORTEND   = Column (Integer,       nullable=False, server_default=text ("'0'"))
    LABEZ     = Column (String (2),    nullable=False)
    VARID     = Column (String (2),    server_default=text ("''"))
    LABEZSUF  = Column (String (30),   nullable=False)
    FEHLER    = Column (String (10),   nullable=False)
    LESART    = Column (String (1024), nullable=False)
    KOMMENTAR = Column (String (50),   nullable=False)
    SPRACHE   = Column (String (1),    nullable=False)
    BEGADR    = Column (Integer,       nullable=False, server_default=text ("'0'"))
    ENDADR    = Column (Integer,       nullable=False, server_default=text ("'0'"))
    ADR       = Column (Integer,       nullable=False, server_default=text ("'0'"))
    UEBER     = Column (String (1),    nullable=False)
    UNTER     = Column (String (1),    nullable=False)
    Z_ZAHL    = Column (Integer,       nullable=False, server_default=text ("'0'"))
    BYZ       = Column (String (1),    nullable=False)
    KONTROLLE = Column (String (1),    nullable=False)
    zv        = Column (String (1),    server_default=text ("''"))
    al        = Column (String (1),    server_default=text ("''"))


class VarGenAttAct01 (Base):
    """This table relates splits to manuscripts.

    .. sauml:: mysql:///VarGenAtt_ActPh4?read_default_group=ntg
       :include: VarGenAttAct01

    """

    __tablename__ = 'VarGenAttAct'

    BOOK   = Column (Integer,     nullable=False, server_default=text ("'0'"))
    CHBEG  = Column (Integer,     nullable=False, server_default=text ("'0'"))
    VBEG   = Column (Integer,     nullable=False, server_default=text ("'0'"))
    WBEG   = Column (Integer,     nullable=False, server_default=text ("'0'"))
    WEND   = Column (Integer,     nullable=False, server_default=text ("'0'"))
    VARID  = Column (String (2),  nullable=False, server_default=text ("''"))
    VARNEW = Column (String (2),  nullable=False)
    S1     = Column (String (2),  nullable=False, server_default=text ("''"))
    S2     = Column (String (2),  nullable=False, server_default=text ("''"))
    PRS1   = Column (String (2),  nullable=False, server_default=text ("''"))
    PRS1A  = Column (String (2),  nullable=False, server_default=text ("''"))
    PRS1B  = Column (String (2),  nullable=False, server_default=text ("''"))
    PRS2   = Column (String (2),  nullable=False, server_default=text ("''"))
    PRS2A  = Column (String (2),  nullable=False, server_default=text ("''"))
    PRS2B  = Column (String (2),  nullable=False, server_default=text ("''"))
    WITN   = Column (String (10), nullable=False, server_default=text ("''"))
    MS     = Column (Integer,     nullable=False, server_default=text ("'0'"))
    CHEND  = Column (Integer,     nullable=False, server_default=text ("'0'"))
    VEND   = Column (Integer,     nullable=False, server_default=text ("'0'"))
    BEGADR = Column (Integer,     nullable=False, server_default=text ("'0'"))
    ENDADR = Column (Integer,     nullable=False, server_default=text ("'0'"))
    CHECK  = Column (String (2),  nullable=False, server_default=text ("''"))

    __table_args__ = (
        PrimaryKeyConstraint (BEGADR, ENDADR, MS),
    )
