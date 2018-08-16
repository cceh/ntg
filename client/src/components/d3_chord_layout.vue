<template>
  <svg height="0" />
</template>

<script>
/**
 * This module converts a graph in .dot format into a SVG chord layout.
 *
 * @component d3_chord_layout
 * @author Marcello Perathoner
 */

import _ from 'lodash';
import * as d3 from 'd3';
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
function load_dot (vm, url) {
    const css_dpi = 96;
    const svg = d3.select (vm.$el);

    const xhr = vm.get (url);
    const p1 = new Promise ((resolve, dummy_reject) => {
        svg.transition ('svg').duration (300).style ('opacity', 0.0).on ('end', resolve);
    });

    const promise = new Promise ((resolve, dummy_reject) => {
        Promise.all ([xhr, p1]).then (function (p) {
            svg.selectAll ('g').remove ();
            d3_common.dot (p[0].data, (graph) => {
                // copy subgraph nodes into the main graph
                _.forEach (graph.subgraphs, (subgraph) => {
                    let subgraph_nodes = _.keyBy (_.filter (
                        subgraph.stmts,
                        (o) => o.type === 'node'
                    ), 'id');
                    _.assign (graph.nodes, subgraph_nodes); // copy
                    subgraph.attrs = _.keyBy (_.filter (
                        subgraph.stmts,
                        (o) => o.type === 'attr'
                    ), 'attrType');
                });

                // hierarchify and cluster
                //
                // The idea is to build a hierarchy starting from a (fictional)
                // root, then going thru a tier of labez (or labez_clique) and finally
                // down to the manuscripts.

                let data = [];
                data.push ({
                    'id'        : 'root',
                    'parent_id' : null,
                    'attrs'     : {},
                });
                _.forEach (graph.subgraphs, (subgraph) => {
                    data.push ({
                        'id'        : subgraph.id,
                        'parent_id' : 'root',
                        'attrs'     : subgraph.attrs,
                    });
                    let subgraph_nodes = _.filter (
                        subgraph.stmts,
                        (o) => o.type === 'node'
                    );
                    _.forEach (subgraph_nodes, (node) => {
                        data.push ({
                            'id'        : node.id,
                            'parent_id' : subgraph.id,
                            'attrs'     : node.attrs,
                        });
                    });
                });

                let root = d3.stratify ()
                    .id (d => d.id)
                    .parentId (d => d.parent_id) (data);

                // sort nodes
                //
                // sort nodes in order to minimize link crossings

                _.forEach (graph.edges, (edge) => {
                    let n0 = graph.nodes[edge.elems[0].id];
                    let n1 = graph.nodes[edge.elems[1].id];
                    n0.attrs.other_labez = n1.attrs.labez;
                    n1.attrs.other_labez = n0.attrs.labez;
                    n0.attrs.other_hsnr  = n1.attrs.hsnr;
                    n1.attrs.other_hsnr  = n0.attrs.hsnr;
                });

                root.sort ((a, b) => {
                    // only sort leaf nodes
                    if (a.depth < 2) {
                        return 0;
                    }
                    //
                    let attrs_a = a.data.attrs;
                    let attrs_b = b.data.attrs;
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

                let node_width  = graph.attrs.node.attrs.width;      // in inch
                let node_height = graph.attrs.node.attrs.height;     // in pt
                let font_size   = graph.attrs.graph.attrs.fontsize;  // in pt

                let node_width_px  = node_width * css_dpi;
                let node_height_px = node_width * css_dpi;
                let n_nodes = root.leaves ().length;
                let n_groups = root.children.length;
                let radius = 1.2 * Math.max (
                    (((n_nodes * node_height_px) + (n_groups * node_height_px / 2)) / (2 * Math.PI)),
                    2 * node_height_px
                );
                let label_radius = radius + (1.5 * node_width_px);

                d3.cluster ()
                    .size ([360, radius])
                    .separation ((a, b) => a.parent === b.parent ? 1 : 1.5) (root);

                let id2node = {};
                root.each ((n) => {
                    id2node[n.id] = n;
                });

                svg.style ('font-size', font_size + 'pt');

                let g = svg.append ('g');

                // draw the nodes: an ellipse and a text in a group

                let ng = g.append ('g').attr ('class', 'nodes')
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

                let node = ng.selectAll ('g.node')
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
                        d3.selectAll ('.link.' + vm.prefix + 'sid-' + d.id).classed ('hover hi-source', true);
                        d3.selectAll ('.link.' + vm.prefix + 'tid-' + d.id).classed ('hover hi-target', true);
                    })
                    .on ('mouseleave', (d) => {
                        d3.selectAll ('.link.' + vm.prefix + 'sid-' + d.id).classed ('hover hi-source', false);
                        d3.selectAll ('.link.' + vm.prefix + 'tid-' + d.id).classed ('hover hi-target', false);
                    });

                node.append ('text')
                    .attr ('class', 'node')
                    .attr ('transform', d => d.x < 180 ? null : 'rotate(180)')
                    .text (d => d.data.attrs.hs);

                // draw the links: a path and a text

                let lg = g.append ('g').attr ('class', 'links');

                let link = lg.selectAll ('path.link')
                    .data (graph.edges)
                    .enter ()
                    .each ((d) => {
                        d.source = id2node[d.elems[0].id];
                        d.target = id2node[d.elems[1].id];
                    });

                let line = d3.radialLine ()
                    .radius (d => d.y - ((d.data.attrs.width || node_width) * css_dpi / 2))
                    .angle  (d => d.x / 180 * Math.PI)
                    .curve (d3.curveBundle.beta (0.5));

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
                /* .merge (graph.edges) */
                    .attr ('d', d => line (d.source.path (d.target)));

                // shrinkwrap + accomodate for the thick borders of ellipses
                // WARNING: This works only if the <g> and all its parents are visible.
                let bbox = d3_common.inflate_bbox (g.node ().getBBox (), 4);
                g.attr ('transform', 'translate(' + (-bbox.x) + ', ' + (-bbox.y) + ')');

                svg.transition ('svg')
                    .duration (300)
                    .attr ('height', bbox.height)
                    .attr ('width',  bbox.width)
                    .transition ()
                    .duration (300)
                    .style ('opacity', 1.0);

                // shrinkwrap
                vm.bbox = bbox;

                // done
                resolve ();
            });
        });
    });
    return promise;
}

export default {
    'props' : ['prefix'],
    'data'  : function () {
        return {
        };
    },
    'methods' : {
        'load_dot' : function (url) {
            return load_dot (this, url);
        },
    },
    'mounted' : function () {
        d3_common.append_marker (d3.select (this.$el), this.prefix);
    },
};
</script>
