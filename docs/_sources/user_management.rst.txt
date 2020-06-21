.. _user-management:

=================
 User Management
=================

.. note::

   User management needs to be implemented as web interface.  See Github issue
   #145.


The user login page is found at:

https://ntg.uni-muenster.de/user/sign-in


Manual User Management
======================

New user must first register themselves through the web interface at:
https://ntg.uni-muenster.de/user/register
After they have succesfully registered, their roles must be set manually.

User credentials are held in the :code:`ntg_user` database.

ssh into the VM and:

.. code:: bash

   sudo -u ntg psql -d ntg_user

To see current users and roles and their ids:

.. code:: sql

   SELECT id, username, email FROM "user" ORDER BY username;

   SELECT * FROM role ORDER BY name;

To see current permissions:

.. code:: sql

   SELECT * FROM role_view;

To give a user a new role:

.. code:: sql

   INSERT INTO roles_users (id, user_id, role_id) VALUES (DEFAULT, :user_id, :role_id)

Replace :user_id and :role_id with the actual user id and role id.

To revoke a role:

.. code:: sql

   DELETE FROM roles_users WHERE (user_id, role_id) = (:user_id, :role_id)


The role names are arbitrary strings.  They must match the roles configured in
the :ref:`application configuration files <app-config-files>` .
