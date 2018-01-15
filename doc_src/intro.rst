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

The program suite consists of scripts for setting up the CBGM database and an
application server for interactive graphic interrogation of the CBGM database.


Database preparation
====================

The input is 2 MySQL databases.  The ECM database contains an apparatus and the
VarGen database records editorial decisions about the priority of readings.

The preparation step copies and normalizes the input data into a new database
and computes an affinity matrix.

.. uml::
   :align: center
   :caption: Database Preparation

   skinparam handwritten true

   database db [
    ECM
   ....
   VarGen
   ]
   component "prepare4cbgm" as p4c
   database "Phase4" as db2

   db -r-> p4c
   p4c -> db2


Online Application
==================

A Javascript library calls an application server and displays the results
graphically.

.. uml::
   :align: center
   :caption: Online Application

   skinparam handwritten true
   skinparam NodeSep 100
   skinparam RankSep 50

   cloud "Application Server\n" as server {
      database "Phase4"
      [Python/Flask] as Flask
      file "JS\nCSS" AS JS
      [Apache]

      [Flask]  <--> Phase4
      [Flask]  <-> [Apache]
      [Apache]  <--> JS
   }

   rectangle "Application Client" as client {
      [Browser\nClient Library] as Browser
   }

   [Apache] <-> [Browser]


The application is online at: http://ntg.cceh.uni-koeln.de

The source code is online at: https://github.com/cceh/ntg

Author: Marcello Perathoner <marcello.perathoner@uni-koeln.de>
