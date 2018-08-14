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

1. scripts for setting up the CBGM database, and an
2. API server, and a
3. client for interactive graphic interrogation of the CBGM database.


Database preparation
====================

As input we use the database that contains the apparatus of the *Editio Critica
Maior* publication.  Supplemental data comes from a database of editorial
decisions (VarGen) regarding the priority of the readings.  The Nestle database
contains the "Leitzeile".

The preparation step transforms the input databases into the CBGM database.

.. uml::
   :align: center
   :caption: Database Preparation

   database "ECM"    as dbsrc1
   database "VarGen" as dbsrc2
   database "Nestle" as dbsrc3
   component "prepare4cbgm script" as p4c
   database "CBGM"   as db

   dbsrc1 --> p4c
   dbsrc2 --> p4c
   dbsrc3 --> p4c
   p4c --> db


Online Application
==================

A client / server architecture.  The client in the user's browser uses the API server
to interrogate the CBGM database.

.. uml::
   :align: center
   :caption: Online Application

   skinparam NodeSep 100
   skinparam RankSep 50

   database "CBGM"
   [API Server] as api
   [Client] as client

   CBGM  <-> api
   api <-> client

The client is written in Javascript using the Vue.js and D3.js libraries.  The
API server is written in Python using the Flask framework.  The CBGM database is
a PostgreSQL database.


Links
=====

The application is online at: http://ntg.cceh.uni-koeln.de/acts/ph4/

The source code is online at: https://github.com/cceh/ntg

Author: Marcello Perathoner <marcello.perathoner@uni-koeln.de>
