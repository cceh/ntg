.. _cbgm:

======
 CBGM
======


Preparing the Database for the CBGM
===================================

All input data must be converted and imported into one Postgres database.

- The mysql database :code:`ECM` contains the apparatus of the *Editio
  Critica Maior* publication.
  This database is exported from the NTVMR application
  (New Testament Virtual Manuscript Room).

- The mysql database :code:`Leitzeile` contains the Leitzeile of the
  current Nestle-Aland edition or any other appropriate "Leitzeile".

- Optionally the mysql database :code:`VarGen` contains
  previous editorial decisions regarding the priority of the readings.
  If this database is not supplied default priorities are used.

.. pic:: uml
   :caption: Database Preparation for CBGM

   skinparam backgroundColor transparent

   database  "ECM"        as dbsrc1
   database  "Leitzeile"  as dbsrc2
   database  "VarGen"     as dbsrc3
   note left of dbsrc1: mysql

   component "import.py"  as import
   component "prepare.py" as prepare
   database  "Acts"       as db1
   database  "Acts"       as db2
   note left of db1: Postgres
   note right of import: copies mysql\nto Postgres
   note right of prepare: normalizes and\nchecks for integrity

   dbsrc1  --> import
   dbsrc2  --> import
   dbsrc3  --> import
   import  --> db1
   db1     --> prepare
   prepare --> db2

The `import.py` script copies the mysql databases into temporary tables of the
postgres database without doing any integrity checking.
The temporary tables are named :file:`original_*`.
These tables are very useful for finding and understanding data errors.

The `prepare.py` script reads the temporary tables in the Postgres database and
writes tables in a :ref:`database structure <cbgm-db>` suitable for doing the CBGM.
This structure is normalized and data integrity is enforced.
The script will print all data integrity errors found
and also log them in the file :file:`prepare.log`.

.. warning::

   The script will not complete if there are data integrity errors.

All data integrity errors that surface at this point must be fixed in the
source data with the aid of the NTVMR people.  Then the source data must be
imported again. This is an iterative and often very time-consuming process.


Applying the CBGM
=================

The `cbgm.py` script applies the CBGM method.
The CBGM is applied at the start of every new project phase.
It must also be applied immediately after the `prepare.py` script.

.. pic:: uml
   :caption: Applying the CBGM

   skinparam backgroundColor transparent

   database  "Acts"    as db1
   component "cbgm.py" as cbgm
   database  "Acts"    as db2
   note right of cbgm: applies the\nCBGM method

   db1  --> cbgm
   cbgm --> db2


.. _cbgm-new-project:

Starting a New Project
======================

To start a new project:

- create a new Postgres database,
- create local copies of the mysql databases,
- add an instance to the server,
- prepare the new Postgres database,
- run the CBGM,
- restart the application server.


Worked Example
--------------

As an example we will create a new project: Mark Phase 9.9.

The name of the new Postgres database is: :code:`mark_ph99`.

We assume having obtained two mysql database dumps from the NTVMR people:
:file:`ECM_Mk_Apparat_6.dump.bz2` and :file:`Nestle29-2.dump.bz2`.

ssh into the server.

.. note::

   You need to have permission to sudo postgres and sudo ntg.

First create a new Postgres database:

.. code:: bash

   sudo -u postgres ~ntg/prj/ntg/ntg/scripts/cceh/create_database.sh mark_ph99

Then import the database dumps into three local mysql databases:

.. code:: bash

   sudo -u ntg bash

   mysql -e "CREATE DATABASE ECM_Mark_Ph99"
   mysql -e "CREATE DATABASE Nestle29"

   bzcat ECM_Mk_Apparat_6.dump.bz2 | mysql -D ECM_Mark_Ph99
   bzcat Nestle29-2.dump.bz2       | mysql -D Nestle29

Then create a new server instance.
The fastest way is to just copy an old instance configuration file and edit it:

.. code:: bash

   cd ~/prj/ntg/ntg/instance
   cp mark_ph22.conf mark_ph99.conf
   emacs mark_ph99.conf

Change all relevant parts of the instance configuration file.
See: :ref:`api-server-config-files`.

Use the `import.py` and `prepare.py` scripts to import
the mysql databases into Postgres and prepare them for CBGM:

.. code:: bash

   cd ~/prj/ntg/ntg
   python3 -m scripts.cceh.import  -vvv instance/mark_ph99.conf
   python3 -m scripts.cceh.prepare -vvv instance/mark_ph99.conf

Then run the CBGM with the `cbgm.py` script:

.. code:: bash

   python3 -m scripts.cceh.cbgm -vvv instance/mark_ph99.conf

Last, restart the application server:

.. code:: bash

   sudo /bin/systemctl restart ntg

If the server doesn't start, check for configuration errors:

.. code:: bash

   sudo /bin/journalctl -u ntg

If you are satisfied with the new project,
you may drop the mysql databases.
The application server uses the Postgres database only.

.. code:: bash

   mysql -e "DROP DATABASE ECM_Mark_Ph99"
   mysql -e "DROP DATABASE Nestle29"


Starting a New Phase
====================

A new phase of the project is entered after the editors have completed a pass
over the whole text.
All editorial decisions taken during this pass are used to recalculate
the CBGM for the next phase.

To start a new phase:

- copy the database into a new database,
- add an instance to the server, and
- run the CBGM on the new instance.


Worked Example
--------------

As an example let us create a new Mark Phase 2.3 from an existing Mark Phase 2.2.

ssh into the server.

.. note::

   You need to have permission to sudo postgres and sudo ntg.

First stop the application server and make a copy of the mark_ph22 database:

.. code:: bash

   sudo -u ntg sudo /bin/systemctl stop ntg
   sudo -u postgres psql -c "CREATE DATABASE mark_ph23 TEMPLATE mark_ph22 OWNER ntg"
   sudo -u ntg sudo /bin/systemctl start ntg

Then create a new server instance:

.. code:: bash

   sudo -u ntg bash
   cd ~/prj/ntg/ntg/instance
   cp mark_ph22.conf mark_ph23.conf

Change all relevant parts of the instance configuration file.
See: :ref:`api-server-config-files`.

.. code:: bash

   emacs mark_ph23.conf

Put the old database in read-only mode (set WRITE_ACCESS="nobody"):

.. code:: bash

   emacs mark_ph22.conf

Then run the CBGM on the *new* instance:

.. code:: bash

   cd ~/prj/ntg/ntg
   python3 -m scripts.cceh.cbgm -vvv instance/mark_ph23.conf

Last, restart the application server:

.. code:: bash

   sudo /bin/systemctl restart ntg


Starting a New Phase With Apparatus Update
==========================================

Sometimes a new phase goes hand in hand with a change in the apparatus.

To update the apparatus while maintaining (most) editorial decisions:

- create a new database for the phase,
- add an instance to the server,
- prepare the new database with the new apparatus,
- save the editorial decisions from the old database,
- load the editorial decisions into the new database, and
- run the CBGM on the new instance.


Worked Example
--------------

As an example let us create a new Mark Phase 2.3 from an existing Mark Phase 2.2
using a new apparatus.

First follow the steps in :ref:`cbgm-new-project` above, until you reach the
CBGM step.

Put the old database in read-only mode (set WRITE_ACCESS="nobody"):

.. code:: bash

   cd ~/prj/ntg/ntg/instance
   emacs mark_ph22.conf

Then use the `save_edits.py` script to save the editorial decisions
of the previous phase and the `load_edits.py` script to load them
into the new instance:

.. code:: bash

   cd ~/prj/ntg/ntg
   python3 -m scripts.cceh.save_edits -vvv -o saved_edits.xml instance/mark_ph22.conf
   python3 -m scripts.cceh.load_edits -vvv -i saved_edits.xml instance/mark_ph23.conf

The last command will also output a list of passages in the old apparatus
that are missing or different in the new apparatus and store them
in the file :file:`load_edits.log`.

Then run the `cbgm.py` script on the *new* instance to apply the CBGM method:

.. code:: bash

   python3 -m scripts.cceh.cbgm -vvv instance/mark_ph23.conf

Last, restart the application server:

.. code:: bash

   sudo /bin/systemctl restart ntg
