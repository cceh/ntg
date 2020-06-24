.. module:: client
   :synopsis: Web Client

.. _web-client:

============
 Web Client
============

The web client runs on the user's browser.

The web client is written in Javascript with Vue.js, D3.js, and bootstrap.  It
uses internal routing of URLs.  Most of the application is placed inside Vue.js
components.

You probably want to start looking at the :js:mod:`client/coherence` or
:js:mod:`client/comparison` components.

.. pic:: tree ../client/src
   :caption: Client directory structure


.. contents::
   :local:


.. default-domain:: js


Modules
=======

.. js:automodule:: client/app client/(?!widgets/) client/
