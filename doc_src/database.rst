====================
 Database Structure
====================

.. _cbgm-db:

CBGM Database
=============

The CBGM database is built from the `source-db` by the :mod:`prepare
<scripts.cceh.prepare>` script.  The :mod:`API server <server>` uses this
database.

Blue: initialized by the `scripts.cceh.prepare` script.  These tables change
only between phases.  The Apparatus table is also updated by the
`scripts.cceh.cbgm` script where manuscript 'A' is concerned.

Green: updated by the `server`.  Backed up by `scripts.cceh.save_edits`.
Restored by `scripts.cceh.load_edits`.  The editors update these tables through
a graph editor.  These tables are `journalled <tts>` to eventually provide undo
functionality.

Red: updated by the `scripts.cceh.cbgm` script.

.. _db-overwiew:

.. figure:: uml.*
   :align: center

   Overview of the CBGM database (some columns omitted)


.. Palette https://github.com/d3/d3-scale-chromatic/blob/master/src/categorical/Paired.js

.. pic:: sauml -i books -i passages -i ranges -i readings -i cliques -i manuscripts
               -i ms_cliques -i locstem -i notes -i apparatus -i ms_ranges -i affinity
               postgresql+psycopg2://ntg@localhost:5432/acts_ph4
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

Source Databases
================

These are the databases output by the NTVMR.
There is one instances of each table for every chapter,
eg. in Acts there are 28 instances of each table.
These tables are only used once for building the :mod:`CBGM database <ntg_common.db>`.
The database system is MySQL.

.. pic:: sauml -i Acts01GVZ -i Acts01GVZlac
               mysql:///ECM_ActsPh4?read_default_group=client
   :caption: ECM database structure
   :html-classes: pic-w100
   :align: center


.. pic:: sauml -i LocStemEdAct01 -i RdgAct01 -i VarGenAttAct01
               mysql:///VarGenAtt_ActPh4?read_default_group=client
   :caption: VarGen database structure
   :html-classes: pic-w100
   :align: center


.. pic:: sauml -i Nestle29
               mysql:///Nestle29?read_default_group=client
   :caption: Leitzeile database structure


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

.. autoclass:: ntg_common.src_db.Nestle29
   :members:


Literature
==========

.. [SNODGRASS2000] Snodgrass, R.T.  *Developing Time-Oriented Database
                   Applications in SQL*. 2000. Morgan Kaufmann Publishers, San
                   Francisco.
