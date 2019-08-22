==============
 Introduction
==============

A program suite for doing CBGM.

The CBGM is a method for inferring global manuscript stemmata from local
stemmata in the manuscripts' texts.

..
   http://ntg.cceh.uni-koeln.de/ph4/coherence#51528030-4

.. graphviz:: local-stemma-example.dot
   :align: center
   :caption: An example of a local stemma

In the CBGM we assume that a manuscript is prior to another manuscript if it
contains a greater percentage of prior readings than posterior readings.  Then
we build a global stemma of manuscripts by using the most similar prior
manuscripts as the parent manuscript.

The program suite consists of:

1. a web application, and
2. a set of scripts to manipulate the CBGM database.


Web Application
===============

The web application consists of a :mod:`web client <client>` and an :mod:`API
server <server>`. The client runs in the user's browser.  The API server runs on
a dedicated web server.  It can manage multiple databases.

.. uml::
   :align: center
   :caption: Web Application

   skinparam backgroundColor transparent

   component "Web Client" as client
   component "API Server" as api
   database "Acts" as db1
   database "John" as db2
   database "Mark" as db3

   client <--> api
   api <--> db1
   api <--> db2
   api <--> db3


Preparing the Database for the CBGM
===================================

Currently we host the CBGM for three books, namely Acts, John and Mark, by
different editorial teams and in different stages of completion.  Each book gets
its own database.

As raw input we use the database that contains the apparatus of the *Editio
Critica Maior* publication.  Supplemental data comes from a database of
editorial decisions (VarGen) regarding the priority of the readings.  The Nestle
database contains the "Leitzeile".

The `import.py` script imports the mysql databases into the postgres database
and the `prepare.py` script transforms the structure of the database into one
suitable for doing the CBGM.

This process needs to be done only once.

.. uml::
   :align: center
   :caption: Database Preparation for CBGM

   skinparam backgroundColor transparent

   database  "ECM"        as dbsrc1
   database  "VarGen"     as dbsrc2
   database  "Nestle"     as dbsrc3
   component "import.py"  as import
   database  "Acts"       as db
   component "prepare.py" as prepare

   dbsrc1  --> import
   dbsrc2  --> import
   dbsrc3  --> import
   import  --> prepare
   prepare --> db

The databases for John and Mark are imported in a similar way.  Each team has a
different workflow, and uses a different structure in their input databases.
The import script tries to accomodate all those differences.


Applying the CBGM
=================

The `cbgm.py` script recalculates the CBGM.  Whenever a local stemma changes,
the CBGM coefficients have to be recalculated.  This process must be run
immediately after the `prepare.py` script.

To take the project from one phase to the next, make a copy of the database and
run this process on the new database.

.. uml::
   :align: center
   :caption: Applying the CBGM

   skinparam backgroundColor transparent

   component "cbgm script" as cbgm
   database  "Acts"        as db

   db -> cbgm
   db <- cbgm


Updating the Apparatus
======================

If the apparatus needs an update the whole CBGM database must be rebuilt from
scratch, the CBGM process must be run and the editorial decisions have to be
transferred to the new database:

1. the `save_edits.py` script is used to save the editorial decisions,
2. the `import.py` and `prepare.py` scripts are used to import and prepare a new
   apparatus, and
3. the `cbgm.py` script is run to apply the CBGM to the new data, and finally
4. the `load_edits.py` script is used to restore the editorial decisions into
   the new database.


Links
=====

The application is online at: http://ntg.cceh.uni-koeln.de/acts/ph4/

The source code is online at: https://github.com/cceh/ntg

Author: Marcello Perathoner <marcello.perathoner@uni-koeln.de>
