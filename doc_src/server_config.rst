.. _api-server-config-files:

================================
 API Server Configuration Files
================================

.. _app-config-files:

Per-Application Configuration Files
===================================

The API server can serve multiple applications.  "Application" is synonymous
with "project".  An application (or project) typically is about one book of the
New Testament.

Each application has one configuration file.  The API server looks for
configuration files in the :file:`instance/` directory.  The files themselves
must be named :file:`*.conf` and the name must not begin with an underscore.

See also: Flask Configuration Handling [#f2]_ and
Werkzeug Serving WSGI Applications [#f3]_.

API Server
~~~~~~~~~~

.. attribute:: APPLICATION_NAME

   The name of the application (Project). eg. "Acts Phase 5"

   The name appears in title bar in the client.

.. attribute:: APPLICATION_ROOT

   The api entrypoint. [#f2]_ eg. "acts/ph5/".

   This value is appended to the APPLICATION_ROOT configured in the global
   configuration file to yield the API entry point for this application.

   This value must have exactly 2 segments, eg. "<project>/<phase>/".

   With the example values the API entrypoint for this application would be
   "http://localhost:5000/api/acts/ph5/".  The API entrypoint is typically
   proxied through an Apache or nginx server that does the TLS handling.

.. attribute:: APPLICATION_DESCRIPTION

   An optional longer description of the application. eg. "(= Phase 4 + CBGM)".

   It appears in the project selection list in the client.

.. attribute:: BOOK

   The book this application is about. eg. "Mark".

   For a list of books see: :file:`ntg_common/tools.py`

.. attribute:: READ_ACCESS

   The role that has read access. eg. "editor"

   For a description of roles see: :ref:`user-management`.

.. attribute:: READ_ACCESS_PRIVATE

   The role that can read editor's notes. eg. "editor_acts"

.. attribute:: WRITE_ACCESS

   The role that can modify the project. eg. "editor_acts"

.. attribute:: PGHOST

   The Postgres host. eg. "localhost"

.. attribute:: PGPORT

   The Postgres port. eg. "5432"

.. attribute:: PGDATABASE

   The Postgres database. eg. "acts_ph5"

   Each project is stored in its own database.

.. attribute:: PGUSER

   The Postgres user.  eg. "ntg"

   The server connects to the database as this user.  The password for this user
   (and database) should be configured in the standard Postgres
   :file:`~/.pgpass` [#f1]_ file in the home directory of the user that owns the API
   server.


Import
~~~~~~

The following entries are used by the `import.py` script only:

.. attribute:: MYSQL_CONF

   The mysql client configuration file.
   eg. :file:`~/.my.cnf.ntg`

   This file contains the credentials to connect to the local mysql server.
   It should be readable only by the users that run the `import.py` script.
   The API server itself only connects to the Postgres
   and never to the mysql server.
   Example of file contents:

   .. code-block:: ini

      [mysql]
      host="localhost"
      user="ntg"
      password="123456"
      default-character-set="utf8"

.. attribute:: MYSQL_GROUP

   The group to read in the MYSQL_CONF file.
   eg. :code:`mysql`

.. attribute:: MYSQL_ECM_DB

   The name of the :code:`ECM` database.
   eg. :code:`ECM_Mark_Ph2`

.. attribute:: MYSQL_ATT_TABLES

   A regular expression to find all "att" tables in the :code:`ECM` database.
   eg. :regexp:`Mk\\d+`

.. attribute:: MYSQL_LAC_TABLES

   A regular expression to find all "lac" tables in the :code:`ECM` database.
   eg. :regexp:`Mk\\d+lac`

.. attribute:: MYSQL_NESTLE_DB

   The name of the :code:`Leitzeile` database.
   eg. :code:`Nestle29`

.. attribute:: MYSQL_NESTLE_TABLE

   A regular expression to find all "leitzeile" tables in the :code:`Leitzeile` database.
   eg. :regexp:`Nestle29`

.. attribute:: MYSQL_VG_DB

   The name of the :code:`VarGen` database.  eg. :code:`VarGen_Mark_Ph2`

   .. note::

      The :code:`VarGen` database is optional.
      Without it, default priorities will be used.
      In this case set this variable to the same as
      the MYSQL_ECM_DB variable
      and do not set any of the following variables.

.. attribute:: MYSQL_LOCSTEM_TABLES

   A regular expression to find all "locstemed" tables in the :code:`VarGen` database.
   eg. :regexp:`LocStemEdMark\\d+`

.. attribute:: MYSQL_RDG_TABLES

   A regular expression to find all "rdg" tables in the :code:`VarGen` database.
   eg. :regexp:`RdgMark\\d+`

.. attribute:: MYSQL_VAR_TABLES

   A regular expression to find all "var" tables in the :code:`VarGen` database.
   eg. :regexp:`VarGenAttMark\\d+`

.. attribute:: MYSQL_MEMO_TABLE

   A regular expression to find all "memo" tables in the :code:`VarGen` database.
   eg. :regexp:`Memo`


.. _global-config-file:

Global Configuration File
=========================

This is the configuration file for the whole application server. The global
configuration file must be named :file:`instance/_global.conf`.

.. attribute:: APPLICATION_HOST

   The app server DNS name: eg. "localhost"

.. attribute:: APPLICATION_PORT

   The app server port. eg. 5000

.. attribute:: APPLICATION_ROOT

   The root API entrypoint. [#f2]_ eg. "/api/"

   With the above mentioned values the API root entrypoint would be
   "http://localhost:5000/api/".  Application-specific entrypoints are appended
   to this root.  The API entrypoint is typically proxied through an Apache or
   nginx server that does the TLS handling.

.. attribute:: AFTER_LOGIN_URL

   The URL to redirect the user to after she has logged in.
   eg. "https://ntg.uni-muenster.de/"

.. attribute:: SECRET_KEY

   Session cookie encryption. [#f2]_ eg. "a_long_random_secret_phrase"

.. attribute:: USE_RELOADER

   Should the server automatically restart the python process if modules were
   changed? [#f3]_  eg. True

   Development only. Do not use in production servers.

.. attribute:: USE_DEBUGGER

   Should the werkzeug debugging system be used? [#f3]_ eg. True

   Starts the web-debugger on Python exceptions. Development only. Do not use in
   production servers.


.. attribute:: PGHOST

   The Postgres host. eg. "localhost"

.. attribute:: PGPORT

   The Postgres port. eg. "5432"

.. attribute:: PGDATABASE

   The Postgres database that holds user login information. eg. "ntg_user"

   This should be the database that holds only the user login information.

.. attribute:: PGUSER

   The Postgres user eg. "ntg"

   The server connects to the database as this user.  The password for this user
   (and database) should be configured in the standard Postgres
   :file:`~/.pgpass` [#f1]_ file in the home directory of the user that owns the API
   server.


.. attribute:: USER_PASSWORD_HASH

   The hash algorithm used to encrypt user passwords in the database.
   eg. "pbkdf2_sha512"

.. attribute:: USER_PASSWORD_SALT

   The salt used to encrypt the user passwords stored in the database.
   eg. "a_different_long_random_secret_phrase"


.. attribute:: MAIL_SERVER

   The mail server used to send user registration confirmation email.
   eg.  "smtp.uni-muenster.de"

.. attribute:: MAIL_PORT

   The mail server port. eg.  25

.. attribute:: MAIL_USE_TLS

   Send mail using TLS. eg.  True

.. attribute:: MAIL_DEFAULT_SENDER

   The sender name to use in the user registration confirmation emails.
   eg. "ntg appserver <noreply@uni-muenster.de>"


.. attribute:: CORS_ALLOW_ORIGIN

   Restricts API usage to specified hosts. eg. "*"


Footnotes
=========

.. [#f1] PostgreSQL Documentation: The Password File.
         https://www.postgresql.org/docs/current/libpq-pgpass.html

.. [#f2] Flask Documentation: Configuration Handling.
         https://flask.palletsprojects.com/en/1.1.x/config/

.. [#f3] Werkzeug Documentation: Serving WSGI Applications.
         https://werkzeug.palletsprojects.com/en/1.0.x/serving/
