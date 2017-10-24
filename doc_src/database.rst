====================
 Database Structure
====================


:mod:`ntg_common.db` --- Work Database
======================================

.. figure:: uml.*

   Overview of the CBGM database (some columns omitted)

The work database is build
from the :mod:`source database <ntg_common.src_db>`
by the :mod:`prepare4cbgm <scripts.cceh.prepare4cbgm>` script.
The :mod:`online application <server>` reads this database.
The database system is PostgreSQL.

.. sauml::
   :include: books passages ranges readings cliques locstem manuscripts apparatus ms_ranges affinity
   :caption: Work database structure
   :align: center

   { rank=same; passages, ranges, manuscripts }
   { rank=same; cliques, ms_ranges }
   { rank=same; locstem, apparatus, affinity }


Tables
------

.. automodule:: ntg_common.db
   :synopsis: Database Structure
   :members:


:mod:`ntg_common.src_db` --- Source Database
============================================

This is the legacy database used in Münster.
There are 28 instances of each table, one for each chapter of Acts.
These tables are only used once for building the :mod:`work database <ntg_common.db>`.
The database system is MySQL.

.. sauml:: mysql:///ECM_ActsPh4?read_default_group=ntg
   :include: Acts01GVZ Acts01GVZlac
   :align: center

.. sauml:: mysql:///VarGenAtt_ActPh4?read_default_group=ntg
   :include: LocStemEdAct01 RdgAct01 VarGenAttAct01
   :caption: Source database structure
   :align: center


Tables
------

.. autoclass:: ntg_common.src_db.Acts01GVZ
   :members:

.. autoclass:: ntg_common.src_db.Acts01GVZlac
   :members:

.. autoclass:: ntg_common.src_db.LocStemEdAct01
   :members:

.. autoclass:: ntg_common.src_db.RdgAct01
   :members:

.. autoclass:: ntg_common.src_db.VarGenAttAct01
   :members:
