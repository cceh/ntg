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
2. a set of scripts for setting up the CBGM database.


Web Application
===============

The web application consists of a client and an API server. The client runs in
the user's browser.  The API server runs on a CCeH server and can manage
multiple databases.

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


The client is written in Javascript using the Vue.js and D3.js libraries.  The
API server is written in Python using the Flask framework.  The database is a
PostgreSQL database.


Database Setup
==============

Currently we host the CBGM for three books, namely Acts, John and Mark, by
different editorial teams and in different stages of completion.  Each book gets
its own database.

As raw input we use the database that contains the apparatus of the *Editio
Critica Maior* publication.  Supplemental data comes from a database of
editorial decisions (VarGen) regarding the priority of the readings.  The Nestle
database contains the "Leitzeile".

The preparation step transforms the many input databases into one database
suitable for the API server.

.. uml::
   :align: center
   :caption: Database Preparation

   skinparam backgroundColor transparent

   database "ECM"    as dbsrc1
   database "VarGen" as dbsrc2
   database "Nestle" as dbsrc3
   component "prepare4cbgm script" as p4c
   database "Acts"   as db

   dbsrc1 --> p4c
   dbsrc2 --> p4c
   dbsrc3 --> p4c
   p4c --> db


The databases for John and Mark are prepared in a similar way.  Each team has a
different workflow, and uses a different structure in their input databases.
The preparation script tries to accomodate all those differences.


Links
=====

The application is online at: http://ntg.cceh.uni-koeln.de/acts/ph4/

The source code is online at: https://github.com/cceh/ntg

Author: Marcello Perathoner <marcello.perathoner@uni-koeln.de>
