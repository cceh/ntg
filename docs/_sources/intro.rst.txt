==============
 Introduction
==============

A program suite for doing CBGM.

The CBGM is a method for inferring global manuscript stemmata from local
stemmata in the manuscripts' texts.

..
   http://ntg.cceh.uni-koeln.de/ph4/coherence#51528030-4

.. pic:: dot local-stemma-example.dot
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
server <server>`. The client runs in the user's browser.  The API server is
written in Python.  The server can manage multiple databases.

.. pic:: uml
   :caption: Web Application

   skinparam backgroundColor transparent

   component "Web Client" as client
   note left of client: javascript
   component "API Server" as api
   note left of api: python
   database "Acts\nPhase 4" as db1
   note top of db1: Postgres
   database "Acts\nPhase 5" as db2
   database "John\nPhase 1" as db3
   database "Mark\nPhase 1" as db4
   database "Mark\nPhase 2" as db5
   database "..."  as db6


   client <--> api
   api <--> db1
   api <--> db2
   api <--> db3
   api <--> db4
   api <--> db5
   api <--> db6


Currently we host the CBGM for three books, namely Acts, John and Mark, by
different editorial teams and in different stages of completion.
Each book and phase gets its own database.


Scripts
=======

This is a set of scripts that the user can run manually on the server to
manage the whole :ref:`cbgm` process, that is:

- importing new books,
- doing the CBGM (passing from one phase to the next),
- and eventually updating the apparatus.


Links
=====

The application is online at: http://ntg.cceh.uni-koeln.de/acts/ph4/

The source code is online at: https://github.com/cceh/ntg

Author: Marcello Perathoner <marcello.perathoner@uni-koeln.de>
