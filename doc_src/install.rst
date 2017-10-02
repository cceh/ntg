==============
 Installation
==============

1. Install the software:

   .. code-block:: shell

      sudo apt-get install git make
      git clone https://github.com/cceh/ntg
      cd ntg
      make install-prerequisites


Database Access
===============


MySQL database
--------------

1. Edit (or create) your :file:`~/.my.cnf` and add this section:

   .. code-block:: ini

       [ntg]
       host='localhost'
       user='<username>'
       password='<password>'
       default-character-set='utf8'

   Replace *<username>* and *<password>* with your own MySQL username and password.

   .. warning::

      Make sure :file:`~/.my.cnf` is readable only by yourself!

2. Create databases for ECM and VarGenAtt:

   .. code-block:: shell

      sudo mysql -e "CREATE DATABASE VarGenAtt_ActPh4"
      sudo mysql -e "CREATE DATABASE ECM_ActsPh4"



Postgres database
-----------------

1. Create a postgres user and a foreign data wrapper for MySQL.  The FDW allows
   Postgres to access the MySQL databases.

   Login to postgres as superuser and say:

   .. code-block:: shell

      sudo -u postgres psql

   .. code-block:: psql

      CREATE USER ntg CREATEDB PASSWORD '<password>';
      CREATE DATABASE ntg_user OWNER ntg;
      CREATE DATABASE ntg_ph4 OWNER ntg;
      CREATE EXTENSION mysql_fdw;
      GRANT USAGE ON FOREIGN DATA WRAPPER mysql_fdw TO ntg;
      \q

   Replace <password> with a real password.

2. Edit (or create) your :file:`~/.pgpass` and add this line:

   .. code-block:: none

      localhost:5432:*:ntg:<password>

   .. warning::

      Make sure :file:`~/.pgpass` is readable only by yourself!

   .. note::

      You can now login to the Postgres database as user ntg without having
      to enter your password:

      .. code-block:: shell

         psql -h localhost -U ntg -d ntg_ph4



Application server
==================

1. Configure the global settings for the application server.  This concerns the
   user management database that holds user credentials and has to send
   confirmation mails.

   Edit (or create) your :file:`server/instance/_global.conf`

   .. code-block:: ini

      APPLICATION_NAME    = "Root"
      APPLICATION_ROOT    = "/"
      SESSION_COOKIE_PATH = "/"
      SECRET_KEY          = "<a random string>"

      PGHOST="localhost"
      PGPORT="5432"
      PGDATABASE="ntg_user"
      PGUSER="ntg"

      USER_APP_NAME="NTG"
      USER_PASSWORD_HASH="pbkdf2_sha512"
      USER_PASSWORD_SALT="<a random string>"

      MAIL_SERVER  = "smtp.domain.tld"
      MAIL_PORT    = 25
      MAIL_USE_TLS = True
      MAIL_DEFAULT_SENDER = "ntg appserver <noreply@domain.tld>"


2. Per-database setting of the application server.  The server can serve
   multiple databases from different mount points.  This concerns the CBGM
   database(s).

   Edit (or create) your :file:`server/instance/ph4.conf`

   .. code-block:: ini

      APPLICATION_NAME="Phase 4"
      APPLICATION_ROOT="/ph4"

      PGHOST="localhost"
      PGPORT="5432"
      PGDATABASE="ntg_ph4"
      PGUSER="ntg"

      MYSQL_GROUP="ntg"
      MYSQL_ECM_DB="ECM_ActsPh4"
      MYSQL_VG_DB="VarGenAtt_ActPh4"


3. Initialize the user management database and add an administrator user for the
   application server.  You'll need this user to login in the browser.

   .. note::

      This should not be the same username (and password) as the database user
      above!

   .. code-block:: shell

      python3 -m scripts.cceh.mk_user -e <email> -u <username> -p <password>


CBGM
====

1. Get database dumps from Münster (exercise left to the reader) and import
   them:

   .. code-block:: shell

      mysql -D "VarGenAtt_ActPh4" < VarGenAtt_ActPh4.dump
      mysql -D "ECM_ActsPh4"      < ECM_ActsPh4.dump

2. Now run the CBGM process. This will fill the Postgres database.

   .. code-block:: shell

      python3 -m scripts.cceh.prepare4cbgm -vvv server/instance/ph4.conf


Run Server
==========

1. Run the application server:

   .. code-block:: shell

      make server
