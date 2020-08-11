.. _vm:

=====================
 ntg.uni-muenster.de
=====================

This page describes the VM :code:`ntg.uni-muenster.de` where the main project is
hosted.

:code:`ntg.uni-muenster.de` is a Debian stable VM in the WWU OpenStack cloud.

.. pic:: uml
   :caption: Overview of VM
   :html-classes: pic-w100

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
   database  "2Sam\nPh 2"      as db9
   database  "CL\nPh 2"        as db10

   database  "JS Client\nFiles"  as client
   database  "Config\nFiles"     as config

   note left  of https:   https://ntg.uni-muenster.de/
   note right of pubapi:  https://ntg.uni-muenster.de/api/
   note left  of client:  /var/www/ntg
   note right of api:     http://localhost:5000/api/
   note left  of config:  ~ntg/prj/ntg/ntg/instance/*.conf

   https   --> apache
   pubapi  --> apache
   client  <-  apache
   apache  --> api
   api     --> app
   config  <-  app
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
   pg      --> db10


Apache
======

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


API Server
==========

The API server loads its configuration from the :file:`~ntg/prj/ntg/ntg/instance/`
directory, one config file for each project. See :ref:`api-server-config-files`.

The API server runs as systemd service, owned by the user "ntg" and controlled
by the file: :file:`/etc/systemd/system/ntg.service`.

The user "ntg" has sudo rights to control the API server:

.. code-block:: bash

   sudo /bin/systemctl start ntg
   sudo /bin/systemctl stop ntg
   sudo /bin/systemctl restart ntg
   sudo /bin/systemctl status ntg
   sudo /bin/journalctl -u ntg


Postgres
========

A standard PostgreSQL installation.

The Postgres server has one database for each project,
plus the :code:`ntg_user` database for :ref:`user credentials <user-management>`.

Postgres data resides in its own filesystem mounted at :file:`/var/lib/postgresql`.


Users
=====

The user "ntg" owns:

 - the API server and has sudo rights to restart it,
 - all Postgres databases shown above,
 - the :file:`/var/www/ntg` directory where the JS client files reside.

The user "postgres" is the database superuser.

.. note::

   You have to be a database superuser to create new project databases
   because the mysql_fdw extension says so.


Developers
----------

Developers have sudo rights on this VM, so they can gain user "ntg" or "postgres".

Ideally you should always login using SSH public key authentication and no user
password should be set on your account at all.  To be able to sudo without a
password you must forward your authentication agent when you ssh into this
machine:

.. code-block:: bash

   ssh -A username@ntg.uni-muenster.de

Then, if everything works, sudo should not ask you for a password.


Add a new developer to the VM
-----------------------------

You need the new developer to send you their public SSH key and
store it in the file :file:`/tmp/id_rsa.pub` on your local machine.
Then ssh into the VM and add the new user $NEWUSER
setting a temporary password:

.. code-block:: bash

   sudo adduser $NEWUSER

Open another shell on your local machine and say:

.. code-block:: bash

   ssh-copy-id -f -i /tmp/id_rsa.pub $NEWUSER@ntg.uni-muenster.de

Close this shell and on the VM again, disable the temp password and add the
developer to the sudoers.  To give sudo rights to a user without password add
their public key to the file :file:`/etc/security/authorized_keys`.

.. code-block:: bash

   sudo passwd -d -l $NEWUSER
   sudo usermod -aG sudo $NEWUSER
   sudo bash -c "cat ~$NEWUSER/.ssh/authorized_keys >> /etc/security/authorized_keys"


.. _vm-backups:

Backups
=======

The editorial decisions for all active databases are backed up every night and
the active databases are backed up weekly. See:

.. code-block:: bash

   sudo -u ntg crontab -l

Active databases are those that are not set read-only.
The active databases are configured in the file :file:`scripts/cceh/active_databases`.

Also full server backups are scheduled with backup2l. See: :file:`/etc/backup2l.conf`.

Backups reside in their own filesystem mounted at :file:`/backup`.

Manual Backups
--------------

Do a manual backup of all editorial decisions:

.. code-block:: bash

   sudo -u ntg ~ntg/prj/ntg/ntg/scripts/cceh/backup_active_edits.sh

Destination directory :file:`/backup/saved_edits/`.

Do a manual backup of all active databases:

.. code-block:: bash

   sudo -u ntg ~ntg/prj/ntg/ntg/scripts/cceh/backup_active_databases.sh

Destination directory :file:`/backup/saved_databases/`.

Do a manual backup of all databases inclusive user database:

.. code-block:: bash

   sudo -u postgres ~ntg/prj/ntg/ntg/scripts/cceh/backup_all_databases.sh

Destination directory :file:`/backup/postgres/`.


Icinga
======

Icinga is a monitoring software.  The VM is configured as Icinga satellite.

See under: :file:`/etc/icinga2/`


OpenStack Cloud
===============

To administer the VM in the cloud: add disks, memory, CPUs, snapshots, disaster recovery etc.

Point your browser to:

  https://openstack.wwu.de/

Select: :guilabel:`DFN AAI Single Sign-On` and go through the login process.

Then go to:

  :guilabel:`Project | Compute |  Instances`

You can now manage the VM.

For disaster recovery select :guilabel:`Console` from the :guilabel:`Actions` dropdown
and login using the 'debian' user.

.. note::

   There are issues with keyboard layout. It works best if you select the
   English (US) layout for your browser window.  Some keys (<>|) still don't
   work though.

Help chat:

  https://zivmattermost.uni-muenster.de/wwu/channels/wwucloud
