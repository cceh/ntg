====================
 Database Structure
====================


:mod:`ntg_common.db` --- Work Database
======================================

.. figure:: uml.*
   :align: center

   Overview of the CBGM database (some columns omitted)

This work database is built
from the :mod:`source database <ntg_common.src_db>`
by the :mod:`prepare4cbgm <scripts.cceh.prepare4cbgm>` script.
The :mod:`online application <server>` reads this database.

The editors update the green tables through a graphical editor.  These tables
are journalled to provide undo functionality.

The CBGM process populates the red tables.

.. Palette https://github.com/d3/d3-scale-chromatic/blob/master/src/categorical/Paired.js

.. sauml::
   :include: books passages ranges readings cliques manuscripts ms_cliques locstem apparatus ms_ranges affinity
   :caption: Work database structure
   :align: center
   :dot-table: bgcolor.ms_cliques=#b2df8a&color.ms_cliques=#33a02c&bgcolor.locstem=#b2df8a&color.locstem=#33a02c&bgcolor.cliques=#b2df8a&color.cliques=#33a02c&bgcolor.affinity=#fb9a99&color.affinity=#e31a1c&bgcolor.ms_ranges=#fb9a99&color.ms_ranges=#e31a1c

   { rank=same; passages, ranges }


Transform the negative apparatus into a positive apparatus
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

1. Set all passages in all manuscripts to the reading 'a'.

2. Overwrite all Fehlverse in all manuscripts with the reading 'zu'.

3. Unroll the lacuna table. Overwrite with 'zz' every passage that is inside a
   lacuna.

4. Overwrite everything with the reading from the negative apparatus, if there
   is one.


.. _tts:

Transaction-Time State Tables
-----------------------------

A transaction-time state table keeps track of the table's contents as it changes
over time.  This is the basis for our undo-functionality in the graphical stemma
editors.

Our TTS tables are temporally partitioned (See [SNODGRASS2000]_ Section 9.4).
We have one table that holds the current rows and another table that holds the
rows that were valid at some time in the past.

We have triggers in place that hide the details of TTS table maintenance:
operations on the current table automagically update the past table also.


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
~~~~~~

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


Literature
==========

.. [SNODGRASS2000] Snodgrass, R.T.  *Developing Time-Oriented Database
                   Applications in SQL*. 2000. Morgan Kaufmann Publishers, San
                   Francisco.
