==========================
 Installation with Docker
==========================

This chapter describes how to install the software on a Desktop computer with
Docker.

.. note::

   These instructions are tested only on Linux.   Feedback for Windows and Mac is welcome.

1. Install Docker.

   - For Windows see: https://docs.docker.com/docker-for-windows/install/

   - For Mac see: https://docs.docker.com/docker-for-mac/install/

   - For Debian Linux see: https://docs.docker.com/compose/install/

2. Create a new directory and change into it.

3. Download https://raw.githubusercontent.com/cceh/ntg/master/docker/docker-compose.yml

4. Run:

   .. code-block:: shell

      $ docker-compose up

   This will download the docker containers and initialize the database.  This
   make take some time depending on your internet connection speed and your PC.

5. Test the installation.
   Point your browser to the url: http://localhost:5000/acts/ph4/

   Use the application.

6. When satisfied, hit :kbd:`Ctrl+C` to stop the docker service.

The Docker service is now installed.


============================
 Running the Docker service
============================

Any time you want to run the docker service say:

.. code-block:: shell

   $ docker-compose start

and to stop it say:

.. code-block:: shell

   $ docker-compose stop

To use the application point your browser to http://localhost:5000/acts/ph4/
while the service is running.


======
 CBGM
======

To run the CBGM:

.. code-block:: shell

  $ docker-compose run ntg-app-server cbgm
