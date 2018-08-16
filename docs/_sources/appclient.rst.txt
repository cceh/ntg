====================
 Application Client
====================

.. default-domain:: js

The Javascript client on the browser.  Written with Vue.js, D3.js and bootstrap.
It uses internal roting of URLs.

Most of the application is placed inside Vue.js components.

You probably want to start looking at the :mod:`coherence` or :mod:`comparison`
components.


The Main Module
===============

.. module:: main


The Application Component
=========================

.. module:: app


The Coherence Page Component
============================

.. module:: coherence


The Comparison Page Component
=============================

.. module:: comparison


The Page Header Component
=========================

.. module:: page_header


The Navigator Component
=======================

.. module:: navigator


The Apparatus Component
=======================

.. module:: apparatus


The Local Stemma Component
==========================

.. module:: local_stemma


The Notes Component
===================

Displays an editable textarea for editor notes.

.. module:: notes


.. _textflow:

The 3 Coherence and the General Textual Flow Cards
==================================================

.. module:: textflow

The javascript module that displays the textflow diagrams.


The Relatives Popup Component
=============================

.. module:: relatives


The Relatives Metrics Component
===============================

.. module:: relatives_metrics


The Comparison Table Component
==============================

.. module:: comparison_table


The Comparison Details Table Component
======================================

.. module:: comparison_details_table


The Card Component
==================

.. module:: card


The Card Caption Component
==========================

.. module:: card_caption


The Toolbar Component
=====================

.. module:: toolbar


The Chord Layout Engine Component
=================================

.. module:: d3_chord_layout


The Stemma Layout Engine Component
==================================

.. module:: d3_stemma_layout



Various functions for D3
========================

.. module:: d3_common

Useful functions for wrestling with D3.

.. autofunction:: module:d3_common~color_string_to_palette
.. autofunction:: module:d3_common~generate_css_palette
.. autofunction:: module:d3_common~insert_css_palette
.. autofunction:: module:d3_common~to_jquery
.. autofunction:: module:d3_common~to_d3
.. autofunction:: module:d3_common~append_marker
.. autofunction:: module:d3_common~parse_pt
.. autofunction:: module:d3_common~parse_bbox
.. autofunction:: module:d3_common~parse_path
.. autofunction:: module:d3_common~parse_path_svg
.. autofunction:: module:d3_common~inflate_bbox
.. autofunction:: module:d3_common~dot


Various Functions
=================

.. module:: tools

Useful functions that don't fit anywhere else.

.. autofunction:: module:tools~format
.. autofunction:: module:tools~natural_sort
.. autofunction:: module:tools~deparam
.. autofunction:: module:tools~svg_contextmenu
.. autofunction:: module:tools~xhr_alert
.. autofunction:: module:tools~bfs
