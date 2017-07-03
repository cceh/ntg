class Passages (Base2):
    ''' Alle Passagen. '''

    __tablename__ = 'passages'

    pass_id   = Column (Integer,       primary_key = True, autoincrement = True)

    irange    = Column (IntRangeType,  nullable = False, unique = True)
    anfadr    = Column (Integer,       nullable = False)
    endadr    = Column (Integer,       nullable = False)

    lemma     = Column (String (1024), nullable = False)
    comp      = Column (Boolean,       nullable = False, server_default = 'False')
    fehlvers  = Column (Boolean,       nullable = False, server_default = 'False')


class Readings (Base2):
    ''' Alle (normalisierten) Lesarten aller Passagen. '''

    __tablename__ = 'readings'

    rdg_id    = Column (Integer,       primary_key = True, autoincrement = True)
    pass_id   = Column (Integer,       ForeignKey ('passages.pass_id'), nullable = False, index = True)

    labez     = Column (String (2),    nullable = False, server_default = '')
    lesart    = Column (String (1024), nullable = True, server_default = None)
    ''' Lesart wenn abweichend vom Lemma, sonst NULL. '''

    __table_args__ = (
        UniqueConstraint ('pass_id', 'labez' , name = 'unique_readings_pass_id_labez'),
        UniqueConstraint ('pass_id', 'lesart', name = 'unique_readings_pass_id_lesart'),
    )


class Cliques (Base2):
    ''' Benennt die Cliquen im lokalen Graphen. '''

    __tablename__ = 'cliques'

    clique_id = Column (Integer,       primary_key = True, autoincrement = True)
    rdg_id    = Column (Integer,       ForeignKey ('readings.rdg_id'), nullable = False, index = True)

    clique    = Column (Integer,       nullable = False)

    __table_args__ = (
        UniqueConstraint ('rdg_id', 'clique' , name = 'unique_clique_rdg_id_clique'),
    )


class LocStemEd (Base2):
    ''' Bestimmt die Abhängigkeit(en) zwischen den Cliquen '''

    __tablename__ = 'locstemed'

    clique_id   = Column (Integer,       ForeignKey ('cliques.clique_id'), nullable = False, index = True)
    source_id   = Column (Integer,       ForeignKey ('cliques.clique_id'), nullable = False, index = True)

    recursive   = Column (Boolean,       nullable = False, server_default = False)

    __table_args__ = (
        PrimaryKey ('clique_id', 'source_id')
        # FIXME: ABhängigkeiten nur innerhalb derselben Passage
    )


class Manuscripts (Base2):
    ''' Die Handschriften. '''

    __tablename__ = 'manuscripts'

    ms_id     = Column (Integer,       primary_key = True, autoincrement = True)

    hsnr      = Column (Integer,       nullable = False, unique = True)
    hs        = Column (String (32),   nullable = False, unique = True)
    length    = Column (Integer)


class Variants (Base2):
    ''' Ordnet die Manuskripte den Cliquen im lokalen Graphen zu. '''

    __tablename__ = 'var'

    clique_id = Column (Integer,       ForeignKey ('cliques.clique_id'), nullable = False, index = True)
    ms_id     = Column (Integer,       ForeignKey ('manuscripts.ms_id'), nullable = False, index = True)

    __table_args__ = (
        PrimaryKey ('clique_id', 'ms_id')
    )


class Chapters (Base2):
    '''  Die Länge der Kapitel in den Hss. '''

    __tablename__ = 'chapters'

    ch_id     = Column (Integer,       primary_key = True, autoincrement = True)
    ms_id     = Column (Integer,       ForeignKey ('manuscripts.id'), nullable = False, index = True)

    chapter   = Column (Integer,       nullable = False)
    length    = Column (Integer)

    __table_args__ = (
        UniqueConstraint ('ms_id', 'chapter', name = 'unique_chapters_ms_id_chapter'),
    )


class Apparatus (Base2):
    __tablename__ = 'app'

    app_id    = Column (Integer,       primary_key = True, autoincrement = True)
    rdg_id    = Column (Integer,       ForeignKey ('readings.rdg_id'), nullable = False, index = True)
    ms_id     = Column (Integer,       ForeignKey ('manuscripts.ms_id'), nullable = False, index = True)

    labezsuf  = Column (String (32),   nullable = False, server_default = '')
    lesart    = Column (String (1024), nullable = True, server_default = None)
    ''' Lesart falls abweichend vom readings.lesart. Sonst NULL. '''

    ### Brauchen wir den Apparat in der CBGM ?
    ### Was machen wir bei ungewiß a/b ?


# FIXME:
#
# Wir benötigen für jede Tabelle Views, die die abstrakten ids in leserliche ids übersetzen.
#


Fragezeichen in Locstemed ausblenden wenn nicht im Editor
NTG in Köln 18.07 11:00h
