====================
 Application Client
====================

.. default-domain:: js

The Javascript client on the browser.


.. module:: apparatus

Module apparatus
================

.. autofunction:: module:apparatus~load_passage(passage)


.. module:: d3-stemma-layout

Module d3-stemma-layout
=======================

.. autofunction:: module:d3-stemma-layout~init($wrapper, id_prefix)

.. autofunction:: module:d3-stemma-layout~load_dot(url)



.. module:: panel

Module panel
============

.. autofunction:: module:panel~init($panel)
.. autofunction:: module:panel~load_labez_dropdown($group, pass_id, name, prefixes, suffixes)
.. autofunction:: module:panel~load_range_dropdown($group, name, prefixes, suffixes)
.. autofunction:: module:panel~handle_toolbar_events(event)
.. autofunction:: module:panel~set_toolbar_buttons($toolbar, new_status)
.. autofunction:: module:panel~create_panel_controls($panels)
.. autofunction:: module:panel~setup_button_event_handlers()


.. module:: textflow

.. _textflow:

Module textflow
===============

The javascript module that displays the textflow diagrams.

.. autofunction:: module:textflow~init(instance, graph_module, id_prefix, var_only)

.. autofunction:: module:textflow~load_passage(passage)

.. autofunction:: module:textflow~open_contextmenu(event)
