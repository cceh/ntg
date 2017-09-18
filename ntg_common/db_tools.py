# -*- encoding: utf-8 -*-

""" This module contains some useful functions. """

import collections

import networkx as nx

from ntg_common.db import execute


def local_stemma_to_nx (conn, pass_id, show_empty_roots = False):
    """ Load a passage from the database into an nx Graph. """

    res = execute (conn, """
    SELECT labez,
           clique,
           labez_clique (labez, clique) AS labez_clique,
           source_labez,
           source_clique,
           labez_clique (source_labez, source_clique) AS source_labez_clique,
           original
    FROM locstem l
    WHERE labez !~ '^z' AND pass_id = :pass_id
    ORDER BY labez, clique
    """, dict (pass_id = pass_id))

    Variant = collections.namedtuple ('stemma_json_variant',
                                      'labez clique labez_clique source_labez source_clique source_labez_clique original')

    rows = list (map (Variant._make, res))

    G = nx.DiGraph ()

    for row in rows:
        more_params = dict ()
        if show_empty_roots:
            more_params['draggable'] = '1';
            more_params['droptarget'] = '1';
        G.add_node (row.labez_clique, label = row.labez_clique,
                    labez = row.labez, clique = row.clique, labez_clique = row.labez_clique,
                    **more_params)

        if row.source_labez_clique is None:
            if row.original:
                G.add_edge ('*', row.labez_clique)
            else:
                G.add_edge ('?', row.labez_clique)
        else:
            G.add_edge (row.source_labez_clique, row.labez_clique)

    more_params = dict ()
    if show_empty_roots:
        # Add '*' and '?' nodes
        G.add_node ('*')
        G.add_node ('?')
        more_params['droptarget'] = '1';

    if '*' in G:
        G.node['*'].update (label = '*', labez='*', clique='0', labez_clique='*', **more_params)
    if '?' in G:
        G.node['?'].update (label = '?', labez='?', clique='0', labez_clique='?', **more_params)

    return G
