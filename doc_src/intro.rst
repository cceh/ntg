==============
 Introduction
==============

A program suite for doing CBGM.

The CBGM is a method for inferring global manuscript stemmata from local
stemmata in the manuscripts' texts.

.. graphviz:: local-stemma-example.dot
   :align: center
   :caption: A example of local stemma

In the CBGM we assume that a manuscript is prior to another manuscript if it
contains a greater percentage of prior readings than posterior readings.  Then
we build a global stemma of manuscripts by using the most similar prior
manuscripts as the parent manuscript.

The program suite consists of scripts for setting up the CBGM database and an
application server for interactive graphic interrogation of the CBGM database.

The application is online at: http://ntg.cceh.uni-koeln.de

The source code can be found at: https://github.com/cceh/ntg

Author: Marcello Perathoner <marcello.perathoner@uni-koeln.de>
