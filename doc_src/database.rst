====================
 Database Structure
====================

.. figure:: uml.*

   Diagram of the CBGM database

To the :ref:`description of tables and fields <db>`.


Source Tables
=============

Description of the source tables.


LocStemEd
---------

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
