<template>
  <svg height="0" />
</template>

<script>
/**
 * This module converts a graph in .dot format into SVG.  The .dot file must be
 * pre-processed in order to contain coordinates for each node and bezier paths
 * for each edge.
 *
 * @component d3_stemma_layout
 * @author Marcello Perathoner
 */

import { select, selectAll } from 'd3-selection';

import d3_common from 'd3_common';

/**
 * Create an SVG graph from a dot file.
 *
 * @function load_dot
 *
 * @param {string} url - The url (must serve dot format).
 *
 * @returns {Promise} - A promise resolved when all SVG elements have been created.
 */
function load_dot (vm, dot) {
    const css_dpi = 96;
    const svg = select (vm.$el);

    const graph = d3_common.dot (dot);

    svg.selectAll ('g').remove ();

    // shrinkwrap + accomodate for the thick borders of ellipses
    const bbox = d3_common.inflate_bbox (graph.attrs.graph.attrs.bbox, 3);

    vm.graph = graph;

    const node_width  = graph.attrs.node.attrs.width;     // in inches
    const node_height = graph.attrs.node.attrs.height;    // in inches
    const font_size   = graph.attrs.graph.attrs.fontsize; // in points

    svg.style ('font-size', font_size + 'pt');

    // put id also inside node attrs
    for (const [k, v] of Object.entries (graph.nodes)) {
        v.attrs.id = k;
    }

    // give all links an id
    for (const [i, link] of Object.entries (graph.edges)) {
        link.id = vm.prefix + 'link_' + i;
    }

    const g = svg.append ('g')
    // shift a little bit to avoid 'shaving' nodes at the view boundary
        .attr ('transform', 'translate(' + -bbox.x + ',' + -bbox.y + ')');

    // draw the subgraphs: a rectangle with a label

    const sg = g.append ('g')
        .attr ('class', 'subgraphs');

    const subgraph = sg.selectAll ('.subgraph')
        .data (Object.values (graph.subgraphs).map (d => d.attrs.graph.attrs))
        .enter ();

    subgraph.append ('rect')
        .attr ('x',      d => d.bbox.x)
        .attr ('y',      d => d.bbox.y)
        .attr ('width',  d => d.bbox.width)
        .attr ('height', d => d.bbox.height)
        .attr ('class',  d => 'subgraph' + (/rounded/.test (d.style) ? ' rounded' : ''));

    subgraph.append ('text')
        .attr ('class', 'subgraph')
    // lp indicates the center of the label
        .attr ('x', d => d.lp.x)
        .attr ('y', d => d.lp.y)
        .style ('font-size', d => (d.fontsize || font_size) + 'pt')
        .text (d => d.label);

    // draw the links: a path and a text

    const lg = g.append ('g').attr ('class', 'links');

    const link = lg.selectAll ('.link')
        .data (graph.edges)
        .enter ();

    link.filter (d => d.attrs && d.attrs.head_lp)
        .each ((d) => {
            d.attrs.head_lp = d3_common.parse_pt (d.attrs.head_lp);
        });

    link.append ('path')
        .attr ('id', d => d.id)
        .attr ('data-labez', d => graph.nodes[d.elems[0].id].attrs.labez)
        .attr ('class', d => {
            return 'link fg_labez '
                + vm.prefix + 'sid-' + d.elems[0].id + ' '
                + vm.prefix + 'tid-' + d.elems[1].id
                + (/dashed/.test (d.attrs.style) ? ' dashed' : '');
        })
        .attr ('marker-end', 'url(#' + vm.prefix + 'triangle)')
        .attr ('d', d => d3_common.parse_path_svg (d.attrs.pos));

    link.filter (d => d.attrs && d.attrs.head_lp && d.attrs.headlabel)
        .append ('text')
        .attr ('data-labez', d => graph.nodes[d.elems[0].id].attrs.labez)
        .attr ('class', (d) => {
            return 'link bg_labez '
                + vm.prefix + 'sid-' + d.elems[0].id + ' '
                + vm.prefix + 'tid-' + d.elems[1].id;
        })
        .attr ('x', d => d.attrs.head_lp.x)
        .attr ('y', d => d.attrs.head_lp.y)
        .text (d => d.attrs.headlabel);

    // draw the nodes: a circle and a text in a group

    const ng = g.append ('g').attr ('class', 'nodes');

    const node = ng.selectAll ('g.node')
        .data (Object.values (graph.nodes).map (d => d.attrs))
        .enter ();

    node.filter (d => d.pos)
        .each (d => { d.pos = d3_common.parse_pt (d.pos); });

    const groups = node.append ('g')
        .attr ('data-ms-id',     d => d.ms_id)
        .attr ('data-label',     d => d.label ? d.label : d.id)
        .attr ('class', d => {
            return 'node node-'
                + (d.children   ? 'internal' : 'leaf')
                + (d.clickable  ? ' clickable' : '')
                + (d.draggable  ? ' draggable' : '')
                + (d.droptarget ? ' droptarget' : '');
        })
        .attr ('transform', d => 'translate(' + d.pos.x + ',' + d.pos.y + ')');

    const valid = new RegExp ('^[-_A-Za-z0-9]+$');

    groups.append ('ellipse')
        .attr ('class', 'node fg_labez bg_clique')
        .attr ('data-labez',        d => d.labez)
        .attr ('data-clique',       d => d.clique)
        .attr ('data-labez-clique', d => d.labez_clique)
        .attr ('rx', d => (d.width  || node_width)  * css_dpi / 2)
        .attr ('ry', d => (d.height || node_height) * css_dpi / 2)
        .on ('mouseenter', (d) => {
            if (valid.test (d.id)) {
                selectAll ('.link.' + vm.prefix + 'sid-' + d.id).classed ('hover hi-source', true);
                selectAll ('.link.' + vm.prefix + 'tid-' + d.id).classed ('hover hi-target', true);
            }
        })
        .on ('mouseleave', (d) => {
            if (valid.test (d.id)) {
                selectAll ('.link.' + vm.prefix + 'sid-' + d.id).classed ('hover hi-source', false);
                selectAll ('.link.' + vm.prefix + 'tid-' + d.id).classed ('hover hi-target', false);
            }
        });

    groups.append ('text')
        .attr ('class', 'node')
        .text (d => d.label ? d.label : d.id);

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
