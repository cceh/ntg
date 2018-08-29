========
 Client
========

The client is just a bunch of javascript files that run in your browser.  Start
the `server.py` and then point your browser to the client's :file:`index.html`.

The only thing the client needs to know is where to find the API.  That is
configured in :file:`api.conf.js`:

.. code-block:: javascript

   var api_base_url = 'http://localhost:5000/';
