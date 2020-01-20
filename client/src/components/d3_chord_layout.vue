<template>
  <svg />
</template>

<script>
/**
 * This module converts a graph in .dot format into a SVG chord layout.
 *
 * @component client/d3_chord_layout
 * @author Marcello Perathoner
 */

import { stratify, cluster }       from 'd3-hierarchy';
import { select, selectAll }       from 'd3-selection';
import { radialLine, curveBundle } from 'd3-shape';

import d3_common from 'd3_common';

/**
 * Create an SVG graph from a dot program.
 *
 * @param {Vue}    vm  - The Vue instance
 * @param {string} dot - A Graphviz .dot program text
 *
 * @returns {Promise} - A promise resolved when all SVG elements have been created.
 */
function load_dot (vm, dot) {
    const css_dpi = 96;
    const svg = select (vm.$el);

    const graph = d3_common.dot (dot);

    svg.selectAll ('g').remove ();

    // hierarchify and cluster
    //
    // The idea is to build a hierarchy starting from a (fictional)
    // root, then going thru a tier of labez (or labez_clique) and finally
    // down to the manuscripts.

    const data = [];
    data.push ({
        'id'        : 'root',
        'parent_id' : null,
        'attrs'     : {},
    });
    for (const subgraph of Object.values (graph.subgraphs)) {
        data.push ({
            'id'        : subgraph.id,
            'parent_id' : 'root',
            'attrs'     : subgraph.attrs,
        });
        const subgraph_nodes = subgraph.stmts.filter (o => o.type === 'node');
        for (const node of subgraph_nodes) {
            data.push ({
                'id'        : node.id,
                'parent_id' : subgraph.id,
                'attrs'     : node.attrs,
            });
        }
    }

    const root = stratify ()
        .id (d => d.id)
        .parentId (d => d.parent_id) (data);

    // sort nodes
    //
    // sort nodes in order to minimize link crossings

    for (const edge of graph.edges) {
        const n0 = graph.nodes[edge.elems[0].id];
        const n1 = graph.nodes[edge.elems[1].id];
        n0.attrs.other_labez = n1.attrs.labez;
        n1.attrs.other_labez = n0.attrs.labez;
        n0.attrs.other_hsnr  = n1.attrs.hsnr;
        n1.attrs.other_hsnr  = n0.attrs.hsnr;
    }

    root.sort ((a, b) => {
        // only sort leaf nodes
        if (a.depth < 2) {
            return 0;
        }
        //
        const attrs_a = a.data.attrs;
        const attrs_b = b.data.attrs;
        if (attrs_a.labez === 'a') {
            // order by other_labez DESC, hsnr
            return (attrs_b.other_labez + attrs_a.hsnr).localeCompare (
                attrs_a.other_labez + attrs_b.hsnr
            );
        }
        // order by other_labez DECS, other_hsnr DESC
        return (attrs_b.other_labez + attrs_b.other_hsnr).localeCompare (
            attrs_a.other_labez + attrs_a.other_hsnr
        );
    });

    // calculate the radius, etc.

    const node_width  = graph.attrs.node.attrs.width;      // in inch
    const node_height = graph.attrs.node.attrs.height;     // in pt
    const font_size   = graph.attrs.graph.attrs.fontsize;  // in pt

    const node_width_px  = node_width * css_dpi;
    const node_height_px = node_width * css_dpi;
    const n_nodes = root.leaves ().length;
    const n_groups = root.children.length;
    const radius = 1.2 * Math.max (
        (((n_nodes * node_height_px) + (n_groups * node_height_px / 2)) / (2 * Math.PI)),
        2 * node_height_px
    );
    const label_radius = radius + (1.5 * node_width_px);

    cluster ()
        .size ([360, radius])
        .separation ((a, b) => a.parent === b.parent ? 1 : 1.5) (root);

    const id2node = {};
    root.each ((n) => {
        id2node[n.id] = n;
    });

    svg.style ('font-size', font_size + 'pt');

    const g = svg.append ('g');

    // draw the nodes: an ellipse and a text in a group

    const ng = g.append ('g').attr ('class', 'nodes')
        .attr ('transform', 'rotate(-90)'); // put origin at 12 hours

    ng.selectAll ('g.group')
        .data (root.children)
        .enter ()
        .append ('g')
        .attr ('class', 'group')
        .attr (
            'transform',
            d => 'rotate(' + d.x + ') translate(' + label_radius + ') rotate (' + (90 - d.x) + ')'
        )
        .append ('text')
        .attr ('class', 'group')
        .text (d => d.data.attrs.graph.attrs.label);

    const node = ng.selectAll ('g.node')
        .data (root.leaves ())
        .enter ()
        .append ('g')
        .attr ('data-ms-id', d => d.data.attrs.ms_id)
        .attr ('class', 'node node-leaf')
        .attr ('transform', d => 'rotate(' + d.x + ') translate(' + radius + ')');

    node.append ('ellipse')
        .attr ('class', 'node fg_labez bg_clique')
        .attr ('data-labez',        d => d.data.attrs.labez)
        .attr ('data-clique',       d => d.data.attrs.clique)
        .attr ('data-labez-clique', d => d.data.attrs.labez_clique)
        .attr ('rx', d => (d.data.attrs.width  || node_width)  * css_dpi / 2)
        .attr ('ry', d => (d.data.attrs.height || node_height) * css_dpi / 2)
        .on ('mouseenter', (d) => {
            selectAll ('.link.' + vm.prefix + 'sid-' + d.id).classed ('hover hi-source', true);
            selectAll ('.link.' + vm.prefix + 'tid-' + d.id).classed ('hover hi-target', true);
        })
        .on ('mouseleave', (d) => {
            selectAll ('.link.' + vm.prefix + 'sid-' + d.id).classed ('hover hi-source', false);
            selectAll ('.link.' + vm.prefix + 'tid-' + d.id).classed ('hover hi-target', false);
        });

    node.append ('text')
        .attr ('class', 'node')
        .attr ('transform', d => d.x < 180 ? null : 'rotate(180)')
        .text (d => d.data.attrs.hs);

    // draw the links: a path and a text

    const lg = g.append ('g').attr ('class', 'links');

    const link = lg.selectAll ('path.link')
        .data (graph.edges)
        .enter ()
        .each ((d) => {
            d.source = id2node[d.elems[0].id];
            d.target = id2node[d.elems[1].id];
        });

    const line = radialLine ()
        .radius (d => d.y - ((d.data.attrs.width || node_width) * css_dpi / 2))
        .angle  (d => d.x / 180 * Math.PI)
        .curve (curveBundle.beta (0.5));

    link.append ('path')
        .attr ('id', d => d.id)
        .attr ('data-labez', d => graph.nodes[d.elems[0].id].attrs.labez)
        .attr ('class', (d) => {
            return 'link fg_labez '
                + vm.prefix + 'sid-' + d.elems[0].id + ' '
                + vm.prefix + 'tid-' + d.elems[1].id
                + (/dashed/.test (d.attrs.style) ? ' dashed' : '');
        })
        .attr ('marker-end', 'url(#' + vm.prefix + 'triangle)')
        .attr ('d', d => line (d.source.path (d.target)));

    // shrinkwrap + accomodate for the thick borders of ellipses
    // WARNING: This works only if the <g> and all its parents are visible.
    const bbox = d3_common.inflate_bbox (g.node ().getBBox (), 4);
    g.attr ('transform', 'translate(' + (-bbox.x) + ', ' + (-bbox.y) + ')');

    svg.attr ('height', bbox.height).attr ('width', bbox.width);

    return bbox;
}

export default {
    'props' : ['prefix'],
    'data'  : function () {
        return {
        };
    },
    'methods' : {
        'load_dot' : function (dot) {
            return load_dot (this, dot);
        },
    },
    'mounted' : function () {
        d3_common.append_marker (select (this.$el), this.prefix);
    },
};
</script>
