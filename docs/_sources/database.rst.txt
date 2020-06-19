====================
 Database Structure
====================

.. _cbgm-db:

CBGM Database
=============

The CBGM database is built from the `source-db` by the :mod:`import
<scripts.cceh.import>` script.  The :mod:`API server <server>` uses this
database.

.. _db-overwiew:

.. figure:: uml.*
   :align: center

   Overview of the CBGM database (some columns omitted)

The editors update the tables shown in green through a graphical editor.  These
tables are `journalled <tts>` to provide undo functionality.

The CBGM process updates the tables shown in red and the Apparatus table where
manuscript 'A' is concerned.

The `server` uses all these tables.

.. Palette https://github.com/d3/d3-scale-chromatic/blob/master/src/categorical/Paired.js

.. sauml::
   :include: books passages ranges readings cliques manuscripts ms_cliques locstem notes apparatus ms_ranges affinity
   :caption: Work database structure
   :html-classes: pic-w100
   :align: center

   { rank=same; passages, ranges }


.. _tts:

Transaction-Time State Tables
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

A transaction-time state table keeps track of the table's contents as it changes
over time.  This is the basis for our undo-functionality in the graphical stemma
editors.

Our TTS tables are temporally partitioned (See [SNODGRASS2000]_ Section 9.4).
We have one table that holds the current rows and another table that holds the
rows that were valid at some time in the past.

We have triggers in place that hide the details of TTS table maintenance:
operations on the current table automagically update the past table also.


Tables
~~~~~~

.. automodule:: ntg_common.db
   :synopsis: Database Structure
   :members:


.. _source-db:

Source Database
===============

This is the legacy database used in Münster.
There are 28 instances of each table, one for each chapter of Acts.
These tables are only used once for building the :mod:`CBGM database <ntg_common.db>`.
The database system is MySQL.

.. sauml:: mysql:///ECM_ActsPh4?read_default_group=client
   :include: Acts01GVZ Acts01GVZlac
   :html-classes: pic-w100
   :align: center

.. sauml:: mysql:///VarGenAtt_ActPh4?read_default_group=client
   :include: LocStemEdAct01 RdgAct01 VarGenAttAct01
   :caption: Source database structure
   :html-classes: pic-w100
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
