.. _cbgm:

======
 CBGM
======


Preparing the Database for the CBGM
===================================

All input data must be converted and imported into one Postgres database.

- The mysql database "ECM" contains the apparatus of the *Editio
  Critica Maior* publication.
  This database is exported from the NTVMR application
  (New Testament Virtual Manuscript Room).

- The mysql database "Leitzeile" contains the Leitzeile of the
  current Nestle-Aland edition or any other appropriate "Leitzeile".

- Optionally the mysql database "VarGen" contains
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
   database  "Acts"       as db
   note left of db: Postgres

   dbsrc1  --> import
   dbsrc2  --> import
   dbsrc3  --> import
   import  --> prepare
   prepare --> db

The `import.py` script copies the mysql databases into temporary tables of the
postgres database without doing any integrity checking.
The temporary tables are named "original_*".
These tables are very useful for finding and understanding data errors.

The `prepare.py` script reads the temporary tables in the Postgres database and
writes tables in a :ref:`<cbgm-db database structure>` suitable for doing the CBGM.
This structure is normalized and data integrity is enforced.

All data integrity errors that surface at this point must be fixed in the source
data before the database can be fully prepared.  Then the source data must be
imported again. This is an iterative and very time-consuming process.

This process needs to be done only once for each project.

The databases for John and Mark are imported in a similar way.  Each team has a
different workflow, and uses a different structure in their input databases.
The prepare.py script tries to accomodate all those differences by special
casing.  See the source.


Applying the CBGM
=================

The `cbgm.py` script recalculates the CBGM.  Whenever a local stemma changes,
the CBGM coefficients have to be recalculated.  This process must be run
immediately after the `prepare.py` script.

.. pic:: uml
   :caption: Applying the CBGM

   skinparam backgroundColor transparent

   component "cbgm script" as cbgm
   database  "Acts"        as db

   db -> cbgm
   db <- cbgm


New Project
===========

A new project is created.

Example
-------

As an example let us create a new project: Matthew Phase 1.

ssh into the server and create an empty Postgres database:

.. code:: bash

   sudo -u ntg bash
   psql -c "CREATE DATABASE mt_ph1"

Now create local mysql databases:

.. code:: bash

   mysql -e "CREATE DATABASE ECM_MtPh1"
   mysql -e "CREATE DATABASE VarGenAtt_MtPh1"
   mysql -e "CREATE DATABASE Nestle29"

And fill them with data.
You probably got these database dumps from the NTVMR people.

.. code:: bash

   cat ECM_MtPh1.dump.sql       | mysql -D ECM_MtPh1
   cat VarGenAtt_MtPh1.dump.sql | mysql -D VarGenAtt_MtPh1
   cat Nestle29.dump.sql        | mysql -D Nestle29

Then create a new server instance.
The fastest way is to just copy an old instance configuration file and edit it:

.. code:: bash

   cd ~/prj/ntg/ntg/instance
   cp acts_ph4.conf mt_ph1.conf
   emacs mt_ph1.conf

Change all relevant parts of the instance configuration file.

Use the `import.py` and `prepare.py` scripts to import
the mysql databases into Postgres and prepare them for CBGM,
then do the CBGM with the `cbgm.py` script:

.. code:: bash

   cd ~/prj/ntg/ntg
   python3 -m scripts.cceh.import  -vvv instance/mt_ph1.conf
   python3 -m scripts.cceh.prepare -vvv instance/mt_ph1.conf
   python3 -m scripts.cceh.cbgm    -vvv instance/mt_ph1.conf

Last, restart the application server:

.. code:: bash

   sudo /bin/systemctl restart ntg

If the server doesn't start, check for configuration errors:

.. code:: bash

   sudo /bin/journalctl -u ntg


New Phases
==========

A new phase of the project is entered after the editors have completed a pass
over the whole text.
All editorial decisions taken during this pass are used to recalculate
the CBGM for the next phase.

To start a new phase:

- copy the database into a new database,
- add an instance to the server, and
- run the CBGM on the new instance.


Example
-------

As an example let us create a new Acts Phase 5 from an existing Acts Phase 4.

ssh into the server and
stop the application server and make a copy of the acts_ph4 database:

.. code:: bash

   sudo -u ntg bash
   sudo /bin/systemctl stop ntg
   psql -c "CREATE DATABASE acts_ph5 WITH TEMPLATE acts_ph4"
   sudo /bin/systemctl start ntg

Then create a new server instance:

.. code:: bash

   cd ~/prj/ntg/ntg/instance
   cp acts_ph4.conf acts_ph5.conf
   emacs acts_ph5.conf

Change all relevant parts of the configuration file. Then run the CBGM on the *new* instance:

.. code:: bash

   cd ~/prj/ntg/ntg
   python3 -m scripts.cceh.cbgm -vvv instance/acts_ph5.conf

Last, restart the application server:

.. code:: bash

   sudo /bin/systemctl restart ntg


New Phases With Apparatus Updates
=================================

Sometimes a new phase goes hand in hand with a change in the apparatus.

To update the apparatus while maintaining (most) editorial decisions:

- create a new databse for the phase,
- add an instance to the server,
- prepare a new database with the new apparatus,
- save the editorial decisions from the old database,
- load the editorial decisions into the new database, and
- run the CBGM on the new instance.


Example
-------

As an example let us create a new Acts Phase 6 from an existing Acts Phase 5
using a new apparatus.

ssh into the server and create a new database for the new phase:

.. code:: bash

   sudo -u ntg bash
   psql -c "CREATE DATABASE acts_ph6"

Then create a new server instance:

.. code:: bash

   cd ~/prj/ntg/ntg/instance
   cp acts_ph5.conf acts_ph6.conf
   emacs acts_ph6.conf

Change all relevant parts of the configuration file.

Now import the new apparatus: follow the steps in `New Project`_ above.

Then use the `save_edits.py` script to save the editorial decisions
of the previous instance and the `load_edits.py` script to load them
into the new instance:

.. code:: bash

   cd ~/prj/ntg/ntg
   python3 -m scripts.cceh.save_edits -vvv -o saved_edits.xml instance/acts_ph5.conf
   python3 -m scripts.cceh.load_edits -vvv -i saved_edits.xml instance/acts_ph6.conf

The last command will also output a list of passages in the old apparatus
that are missing or different in the new apparatus and store them
in the file :file:`load_edits.log`.

Then run the `cbgm.py` script on the *new* instance to apply the CBGM method:

.. code:: bash

   python3 -m scripts.cceh.cbgm -vvv instance/acts_ph6.conf

Last, restart the application server:

.. code:: bash

   sudo /bin/systemctl restart ntg
