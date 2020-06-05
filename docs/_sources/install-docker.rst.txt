.. _docker-install:

==========================
 Installation with Docker
==========================

This chapter describes how to install the CBGM installation on your own PC with
the help of `Docker <https://www.docker.com/>`_. Docker can run our
application on Linux, Mac, and Windows.

We plan to offer various Docker images preloaded with data.  The data is
editable so you can build your own scenarios.

.. warning::

   As of now (September 2019) this is a technology preview.
   More functionality will be added and bugs will be fixed later.
   Feedback is welcome at: https://github.com/cceh/ntg/issues

.. warning::

   These instructions are tested only on Linux.
   Feedback from Windows and Mac users is welcome:
   https://github.com/cceh/ntg/issues


Install
=======

1. Install the free community version of Docker:

   - for Windows see: https://docs.docker.com/docker-for-windows/install/

   - for Mac see: https://docs.docker.com/docker-for-mac/install/

   - for Debian Linux see: https://docs.docker.com/compose/install/

2. Create a new directory and change into it.

3. Download https://raw.githubusercontent.com/cceh/ntg/master/docker/docker-compose.yml

4. Run:

   .. code-block:: shell

      $ docker-compose up

   This will download the Docker containers and initialize the database.  It
   will take some time depending on your internet connection speed and your PC.

5. Test the installation: Point your browser to the url:
   http://localhost:5000/acts/ph4/ and use the application.

6. When satisfied, hit :kbd:`Ctrl+C` to stop the Docker service.

The Docker service is now installed.


Running the web application
===========================

To use the application point your browser to http://localhost:5000/acts/ph4/
while the Docker service is running.  To run the Docker service change into the
directory and say:

.. code-block:: shell

   $ docker-compose start

and to stop it again say:

.. code-block:: shell

   $ docker-compose stop


Running the CBGM
================

To run the CBGM say:

.. code-block:: shell

  $ docker-compose run ntg-app-server cbgm


Troubleshooting
===============

After upgrading to a new docker container, if you get the error message: "FATAL:
database files are incompatible with server", say:

.. code-block:: shell

  $	docker-compose down --volumes
  $ docker-compose up

.. warning::

  This will install a fresh database and overwrite all changes you made to the
  data.
