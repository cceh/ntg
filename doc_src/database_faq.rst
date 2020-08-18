==============
 Database FAQ
==============

.. _cbgm-db-faq:


Manual Editing of Journalled Tables
===================================

When trying to edit a journalled table, you get the error message:
ERROR:unrecognized configuration parameter "ntg.user_id"

When editing a journalled table, the id of the user doing the change is supposed
to be logged.  The Web Application automatically sets this id to the currently
logged-in user.  When doing manual edits to the database the user_id must also
be set, although a user_id of 0 is sufficient.  That is the id used by all
commandline tools.

To set the user id:

.. code-block:: psql

   SET ntg.user_id = 0;

The user id is set for the duration of the psql session.


Apparatus Updates
=================

When trying to update the apparatus you get the error message:
ERROR:update or delete on table "apparatus" violates foreign key
constraint "ms_cliques_ms_id_fkey" on table "ms_cliques"

The apparatus table and the ms_cliques table are closley related.  Changes to
these tables must be done in one transaction and constraint checks must only be
done just before committing.


Example:

.. code-block:: psql

   BEGIN;
   SET CONSTRAINTS ALL DEFERRED;
   UPDATE apparatus SET labez = 'zz' WHERE pass_id = 11 AND ms_id = 1;
   UPDATE ms_cliques SET labez = 'zz' WHERE pass_id = 11 AND ms_id = 1;
   COMMIT;
