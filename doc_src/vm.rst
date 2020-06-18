.. _vm:

=====================
 ntg.uni-muenster.de
=====================


Overview
========

.. pic:: uml
   :caption: Overview of VM

   skinparam backgroundColor transparent

   interface " "               as https
   interface " "               as pubapi
   component "Apache"          as apache
   interface " "               as api
   component "API server"      as app
   component "Postgres"        as pg

   database  "User"            as dba #yellow

   database  "Acts\nPh 4"      as db1
   database  "Acts\nPh 5"      as db2
   database  "Mark\nPh 1.2"    as db3
   database  "Mark\nPh 2"      as db4
   database  "Mark\nPh 2.2"    as db5
   database  "John\nPh 1"      as db6
   database  "John Fam\nPh 1"  as db7
   database  "2Sam\nPh 1"      as db8
   database  "CL\nPh 2"        as db9

   database  "JS Client"       as client

   note left  of https:   "https://ntg.uni-muenster.de/"
   note right of pubapi:  "https://ntg.uni-muenster.de/api/"
   note left  of client:  "/var/www/ntg"
   note right of api:     "http://localhost:5000/api/"

   https   --> apache
   pubapi  --> apache
   client  <-  apache
   apache  --> api
   api     --> app
   app     --> pg

   pg      --> dba

   pg      --> db1
   pg      --> db2
   pg      --> db3
   pg      --> db4
   pg      --> db5
   pg      --> db6
   pg      --> db7
   pg      --> db8
   pg      --> db9

The Apache server has 2 functions:

- to serve the javascript client files and
- to proxy the public API endpoint to the local App server.

The javascript client files are served from :file:`/var/www/ntg/`.
The javascript client also needs to know where to find the world-visible API endpoint.
That is configured in the file :file:`/var/www/ntg/api.conf.js`:

.. code-block:: javascript

   var api_base_url = 'https://ntg.uni-muenster.de/api/';

Apache also proxies all api requests from the client to the API server.
The world-visible API endpoint "https://ntg.uni-muenster.de/api/" is proxied
to the internal "http://localhost:5000/api/" using mod_rewrite.
Apache does all SSL stuff.

.. note::

   This is not hardwired: as an alternative the API server could be made
   world-visible on an URL of its own, eg. "https://api.ntg.uni-muenster.de/"
   but that would require an extra DNS entry and certificate.


Users
=====

The user "ntg" owns:

 - the API server and has sudo rights to restart it,
 - all Postgres databases shown above,
 - the :file:`/var/www/ntg` directory where the JS client files reside.
