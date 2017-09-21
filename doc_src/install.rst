==============
 Installation
==============

Database Access
===============


MySQL database
--------------

Edit (or create) your :file:`~/.my.cnf` and add these sections:

.. code-block:: ini

    [ntg-local]
    host='localhost'
    database='apparat'
    user='username'
    password='password'
    default-character-set='utf8'

    [ntg-remote]
    host='remote'
    database='apparat'
    user='username'
    password='password'
    default-character-set='utf8'

Replace *username* and *password* with your own username and password.

.. warning::

   Make sure :file:`~/.my.cnf` is readable only by yourself!


Postgres database
-----------------

1. Create a postgres user. Login to postgres as superuser and say:

   .. code-block:: psql

      CREATE USER <username> CREATEDB PASSWORD '<password>';

2. Edit (or create) your :file:`~/.pgpass` and add this line:

   .. code-block:: none

      localhost:5432:ntg:<username>:<password>

   Replace <username> and <password> with your own username and password.

   .. warning::

      Make sure :file:`~/.pgpass` is readable only by yourself!

   .. note::

      You can now login to the Postgres database as user <username> without having
      to enter your password:

      .. code-block:: shell

         psql -h localhost -U <username> -d <database>


3. Create MySQL Foreign Data Wrapper

   Allows Postgres to access the MySQL databases in the prepare4cbgm.py script.

   As postgres superuser do:

   .. code-block:: shell

      $ psql -U postgres -h /var/run/postgresql/ -d ntg

   .. code-block:: psql

      CREATE EXTENSION mysql_fdw;
      GRANT USAGE ON FOREIGN DATA WRAPPER mysql_fdw TO <username>;



Application server
------------------

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


3. Add an administrator for the application server.

   .. note::

      This is not the same user (and password) as the database user above!

   .. code-block:: shell

      python3 -m scripts.mk_user -e <email> -u <username> -p <password>
