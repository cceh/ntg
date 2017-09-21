====================
 Application Client
====================

.. default-domain:: js

The Javascript client on the browser.


.. module:: apparatus

Module apparatus
================

.. autofunction:: module:apparatus~load_passage(passage)
.. autofunction:: module:apparatus~goto_attestation(event)
.. autofunction:: module:apparatus~init(instance)


.. module:: coherence

Module coherence
================

.. autofunction:: module:coherence~init()


.. module:: comparison

Module comparison
=================

.. autofunction:: module:comparison~deparam(s)
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


.. module:: d3-chord-layout

Module d3-chord-layout
======================

.. autofunction:: module:d3-chord-layout~load_dot(url)
.. autofunction:: module:d3-chord-layout~init($wrapper, id_prefix)


.. module:: d3-common

Module d3-common
================

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
.. autofunction:: module:d3-common~bfs(edges, start)


.. module:: d3-stemma-layout

Module d3-stemma-layout
=======================

.. autofunction:: module:d3-stemma-layout~init($wrapper, id_prefix)

.. autofunction:: module:d3-stemma-layout~load_dot(url)



.. module:: local-stemma

Module local-stemma
===================

.. autofunction:: module:local-stemma~return_to_base(node)
.. autofunction:: module:local-stemma~highlight(node, b)
.. autofunction:: module:local-stemma~dragListener(panel)
.. autofunction:: module:local-stemma~trow(data)
.. autofunction:: module:local-stemma~open_contextmenu(event)
.. autofunction:: module:local-stemma~load_passage(passage)
.. autofunction:: module:local-stemma~init(instance, graph_module, id_prefix)


.. module:: navigator

Module navigator
================

.. autofunction:: module:navigator~set_passage(pass_id)
.. autofunction:: module:navigator~suggest(data, complete)
.. autofunction:: module:navigator~on_nav(event)
.. autofunction:: module:navigator~init()


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


.. module:: relatives

Module relatives
================

.. autofunction:: module:relatives~get_ms_ids_from_popups(what)
.. autofunction:: module:relatives~load_passage(passage)
.. autofunction:: module:relatives~create_panel(ms_id, target)
.. autofunction:: module:relatives~init(instance)


.. module:: textflow

.. _textflow:

Module textflow
===============

The javascript module that displays the textflow diagrams.

.. autofunction:: module:textflow~init(instance, graph_module, id_prefix, var_only)
.. autofunction:: module:textflow~load_passage(passage)
.. autofunction:: module:textflow~open_contextmenu(event)


.. module:: tools

Module tools
============

.. autofunction:: module:tools~format(s, data)
.. autofunction:: module:tools~natural_sort(s)
.. autofunction:: module:tools~get_query_params()
.. autofunction:: module:tools~svg_contextmenu(menu, target)
.. autofunction:: module:tools~xhr_alert(xhr, $panel)
.. autofunction:: module:tools~init()
