====================
 Application Client
====================

.. default-domain:: js

The Javascript client on the browser.

There are two main entry points: the :mod:`coherence` page and the
:mod:`comparison` page.


:mod:`coherence` --- The Coherence Page
=======================================

.. module:: coherence

.. graphviz:: coherence.nolibs.jsgraph.dot
   :caption: Module dependencies for :mod:`coherence`.
   :align: center

.. autofunction:: module:coherence~init()


:mod:`navigator` --- The Navigator Gadget
=========================================

.. module:: navigator

.. autofunction:: module:navigator~set_passage(pass_id)
.. autofunction:: module:navigator~suggest(data, complete)
.. autofunction:: module:navigator~on_nav(event)
.. autofunction:: module:navigator~init()


:mod:`apparatus` --- The Apparatus Panel
========================================

.. module:: apparatus

.. autofunction:: module:apparatus~load_passage(passage)
.. autofunction:: module:apparatus~goto_attestation(event)
.. autofunction:: module:apparatus~init(instance)


:mod:`notes` --- The Notes Panel
================================

.. module:: notes

.. autofunction:: module:notes~load_passage(passage)
.. autofunction:: module:notes~save_passage(instance)
.. autofunction:: module:notes~init(instance, dummy_id_prefix)


:mod:`local-stemma` --- The Local Stemma Panel
==============================================

.. module:: local-stemma

.. autofunction:: module:local-stemma~return_to_base(node)
.. autofunction:: module:local-stemma~highlight(node, b)
.. autofunction:: module:local-stemma~dragListener(panel)
.. autofunction:: module:local-stemma~trow(data)
.. autofunction:: module:local-stemma~open_contextmenu(event)
.. autofunction:: module:local-stemma~load_passage(passage)
.. autofunction:: module:local-stemma~init(instance, graph_module, id_prefix)


.. _textflow:

:mod:`textflow` --- The 3 Coherence and the General Textual Flow Panels
=======================================================================

.. module:: textflow

The javascript module that displays the textflow diagrams.

.. autofunction:: module:textflow~init(instance, graph_module, id_prefix, var_only)
.. autofunction:: module:textflow~load_passage(passage)
.. autofunction:: module:textflow~open_contextmenu(event)


:mod:`relatives` --- The Relatives Popup
========================================

.. module:: relatives

.. autofunction:: module:relatives~get_ms_ids_from_popups(what)
.. autofunction:: module:relatives~load_passage(passage)
.. autofunction:: module:relatives~create_popup(ms_id, passage, target)
.. autofunction:: module:relatives~position_popup(target)
.. autofunction:: module:relatives~init(instance)


:mod:`panel` --- The Panel Module
=================================

.. module:: panel

.. autofunction:: module:panel~init($panel)
.. autofunction:: module:panel~load_labez_dropdown($group, pass_id, name, prefixes, suffixes)
.. autofunction:: module:panel~load_range_dropdown($group, name, prefixes, suffixes)
.. autofunction:: module:panel~handle_toolbar_events(event)
.. autofunction:: module:panel~set_toolbar_buttons($toolbar, new_status)
.. autofunction:: module:panel~create_panel_controls($panels)
.. autofunction:: module:panel~setup_button_event_handlers()


:mod:`d3-chord-layout` --- The Chord Layout Engine
==================================================

.. module:: d3-chord-layout

.. autofunction:: module:d3-chord-layout~load_dot(url)
.. autofunction:: module:d3-chord-layout~init($wrapper, id_prefix)


:mod:`d3-stemma-layout` --- The Stemma Layout Engine
====================================================

.. module:: d3-stemma-layout

.. autofunction:: module:d3-stemma-layout~init($wrapper, id_prefix)
.. autofunction:: module:d3-stemma-layout~load_dot(url)



:mod:`comparison` --- The Comparison Page
=========================================

.. module:: comparison

.. graphviz:: comparison.nolibs.jsgraph.dot
   :caption: Module dependencies for :mod:`comparison`.
   :align: center

.. autofunction:: module:comparison~dir(older, newer)
.. autofunction:: module:comparison~main_row_conversion(d)
.. autofunction:: module:comparison~detail_row_conversion(d)
.. autofunction:: module:comparison~init_details_table($detailsTable)
.. autofunction:: module:comparison~toggle_details_table()
.. autofunction:: module:comparison~create_main_table()
.. autofunction:: module:comparison~create_details_table(ms1, ms2, range)
.. autofunction:: module:comparison~init_main_table()
.. autofunction:: module:comparison~on_navigation()
.. autofunction:: module:comparison~init_nav()
.. autofunction:: module:comparison~init()


:mod:`d3-common` --- Various functions for D3
=============================================

.. module:: d3-common

Useful functions for wrestling with D3.

.. autofunction:: module:d3-common~color_string_to_palette(s)
.. autofunction:: module:d3-common~generate_css_palette(labez_scale, clique_scale)
.. autofunction:: module:d3-common~insert_css_palette(css)
.. autofunction:: module:d3-common~to_jquery(d3_selection)
.. autofunction:: module:d3-common~to_d3(jquery_selection)
.. autofunction:: module:d3-common~append_marker(svg, id_prefix)
.. autofunction:: module:d3-common~parse_pt(commasep)
.. autofunction:: module:d3-common~parse_bbox(commasep)
.. autofunction:: module:d3-common~parse_path(path)
.. autofunction:: module:d3-common~parse_path_svg(path)
.. autofunction:: module:d3-common~inflate_bbox(bbox, len)
.. autofunction:: module:d3-common~dot(url, callback)


:mod:`tools` --- Various Functions
==================================

.. module:: tools

Useful functions that don't fit anywhere else.

.. autofunction:: module:tools~format(s, data)
.. autofunction:: module:tools~natural_sort(s)
.. autofunction:: module:tools~deparam(s)
.. autofunction:: module:tools~svg_contextmenu(menu, target)
.. autofunction:: module:tools~xhr_alert(xhr, $panel)
.. autofunction:: module:tools~bfs(edges, start)
.. autofunction:: module:tools~init()
