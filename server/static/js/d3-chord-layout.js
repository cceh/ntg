/**
 * This module converts a graph in .dot format into a SVG chord layout.
 *
 * @module d3-chord-layout
 * @author Marcello Perathoner
 */

define (['jquery', 'd3', 'd3-common', 'lodash'],

function ($, d3, d3_common, _) {
    'use strict';

    /**
     * Create an SVG graph from a dot file.
     *
     * @function load_dot
     *
     * @param {string} url - The url (must serve dot format).
     *
     * @returns {Promise} - A promise resolved when all SVG elements have been created.
     */
    function load_dot (url) {
        var instance = this;
        var dot_dpi = 72;
        var css_dpi = 96;

        var svg = instance.svg;
        svg.selectAll ('g').transition ().duration (300).style ('opacity', 0.0)
            .remove ();
        var deferred = new $.Deferred ();

        d3_common.dot (url, function (graph) {
            // copy subgraph nodes into the main graph
            _.forEach (graph.subgraphs, function (subgraph) {
                var subgraph_nodes = _.keyBy (_.filter (subgraph.stmts,
                                                        function (o) { return o.type === 'node'; }), 'id');
                _.assign (graph.nodes, subgraph_nodes); // copy
                subgraph.attrs = _.keyBy (_.filter (subgraph.stmts,
                                                    function (o) { return o.type === 'attr'; }), 'attrType');
            });

            // hierarchify and cluster
            //
            // The idea is to build a hierarchy starting from a (fictional)
            // root, then going thru a tier of labez (or varnew) and finally
            // down to the manuscripts.

            var data = [];
            data.push ({
                'id'        : 'root',
                'parent_id' : null,
                'attrs'     : {}
            });
            _.forEach (graph.subgraphs, function (subgraph) {
                data.push ({
                    'id'        : subgraph.id,
                    'parent_id' : 'root',
                    'attrs'     : subgraph.attrs
                });
                var subgraph_nodes = _.filter (
                    subgraph.stmts, function (o) { return o.type === 'node'; });
                _.forEach (subgraph_nodes, function (node) {
                    data.push ({
                        'id'        : node.id,
                        'parent_id' : subgraph.id,
                        'attrs'     : node.attrs
                    });
                });
            });

            var root = d3.stratify ()
                .id (function (d) { return d.id; })
                .parentId (function (d) { return d.parent_id; }) (data);

            // sort nodes
            //
            // sort nodes in order to minimize link crossings

            _.forEach (graph.edges, function (edge) {
                var n0 = graph.nodes[edge.elems[0].id];
                var n1 = graph.nodes[edge.elems[1].id];
                n0.attrs.other_labez = n1.attrs.labez;
                n1.attrs.other_labez = n0.attrs.labez;
                n0.attrs.other_hsnr  = n1.attrs.hsnr;
                n1.attrs.other_hsnr  = n0.attrs.hsnr;
            });

            root.sort (function (a, b) {
                // only sort leaf nodes
                if (a.depth < 2) {
                    return 0;
                }
                //
                var attrs_a = a.data.attrs;
                var attrs_b = b.data.attrs;
                if (attrs_a.labez === 'a') {
                    // order by other_labez DESC, hsnr
                    return (attrs_b.other_labez + attrs_a.hsnr).localeCompare (
                        attrs_a.other_labez + attrs_b.hsnr);
                }
                // order by other_labez DECS, other_hsnr DESC
                return (attrs_b.other_labez + attrs_b.other_hsnr).localeCompare (
                    attrs_a.other_labez + attrs_a.other_hsnr);
            });

            // calculate the radius, etc.

            var node_width  = graph.attrs.node.attrs.width;      // in inch
            var node_height = graph.attrs.node.attrs.height;     // in pt
            var font_size   = graph.attrs.graph.attrs.fontsize;  // in pt

            var node_width_px  = node_width * css_dpi;
            var node_height_px = node_width * css_dpi;
            var n_nodes = root.leaves ().length;
            var n_groups = root.children.length;
            var radius = 1.2 * Math.max (
                (((n_nodes * node_height_px) + (n_groups * node_height_px / 2)) / (2 * Math.PI)),
                2 * node_height_px
            );
            var label_radius = radius + (1.5 * node_width_px);

            d3.cluster ()
                .size ([360, radius])
                .separation (function (a, b) {
                    return a.parent === b.parent ? 1 : 1.5;
                }) (root);

            var id2node = {};
            root.each (function (n) {
                id2node[n.id] = n;
            });

            svg.style ('opacity', 0.0);
            svg.style ('font-size', font_size + 'pt');

            var g = svg.append ('g');

            // draw the nodes: an ellipse and a text in a group

            var ng = g.append ('g').attr ('class', 'nodes')
                .attr ('transform', 'rotate(-90)'); // put origin at 12 hours

            ng.selectAll ('g.group')
                .data (root.children)
                .enter ()
                .append ('g')
                .attr ('class', 'group')
                .attr ('transform', function (d) {
                    return 'rotate(' + d.x + ') translate(' + label_radius + ') rotate (' + (90 - d.x) + ')';
                })
                .append ('text')
                .attr ('class', 'group')
                .text (function (d) { return d.data.attrs.graph.attrs.label; });

            var node = ng.selectAll ('g.node')
                .data (root.leaves ())
                .enter ()
                .append ('g')
                .attr ('data-ms-id', function (d) {
                    return d.data.attrs.ms_id;
                })
                .attr ('class', 'node node-leaf')
                .attr ('transform', function (d) {
                    return 'rotate(' + d.x + ') translate(' + radius + ')';
                });

            node.append ('ellipse')
                .attr ('class', 'node fg_labez')
                .attr ('data-labez', function (d) { return d.data.attrs.labez; })
                .attr ('rx', function (d) {
                    return (d.data.attrs.width  || node_width) * css_dpi / 2;
                })
                .attr ('ry', function (d) {
                    return (d.data.attrs.height || node_height) * css_dpi / 2;
                })
                .on ('mouseenter', function (d) {
                    d3.selectAll ('path.link.' + instance.id_prefix + 'sid-' + d.id).classed ('hi-source', true);
                    d3.selectAll ('path.link.' + instance.id_prefix + 'tid-' + d.id).classed ('hi-target', true);
                })
                .on ('mouseleave', function (d) {
                    d3.selectAll ('path.link.' + instance.id_prefix + 'sid-' + d.id).classed ('hi-source', false);
                    d3.selectAll ('path.link.' + instance.id_prefix + 'tid-' + d.id).classed ('hi-target', false);
                });

            node.append ('text')
                .attr ('class', 'node')
                .attr ('transform',   function (d) { return d.x < 180 ? null : 'rotate(180)'; })
                .text (function (d) { return d.data.attrs.hs; });

            // draw the links: a path and a text

            var lg = g.append ('g').attr ('class', 'links');

            var link = lg.selectAll ('path.link')
                .data (graph.edges)
                .enter ()
                .each (function (d) {
                    d.source = id2node[d.elems[0].id];
                    d.target = id2node[d.elems[1].id];
                });

            var line = d3.radialLine ()
                .radius (function (d) {
                    return d.y - (d.data.attrs.width || node_width) * css_dpi / 2;
                })
                .angle  (function (d) { return d.x / 180 * Math.PI; })
                .curve (d3.curveBundle.beta (0.5));

            link.append ('path')
                .attr ('id', function (d) { return d.id; })
                .attr ('data-labez', function (d) {
                    return graph.nodes[d.elems[0].id].attrs.labez;
                })
                .attr ('class', function (d) {
                    return 'link fg_labez ' +
                        instance.id_prefix + 'sid-' + d.elems[0].id + ' ' +
                        instance.id_prefix + 'tid-' + d.elems[1].id +
                        (d.attrs.broken ? ' broken' : '');
                })
                .attr ('marker-end', 'url(#' + instance.id_prefix + 'triangle)')
                /* .merge (graph.edges) */
                .attr ('d', function (d) {
                    return line (d.source.path (d.target));
                });

            // WARNING: This works only if the <g> and all its parents are visible.
            var bbox = g.node ().getBBox ();
            g.attr ('transform', 'translate(' + (-bbox.x) + ', ' + (-bbox.y) + ')');

            svg.transition ('svg')
                .duration (300)
                .attr ('height', bbox.height)
                .attr ('width',  bbox.width)
                .transition ()
                .duration (300)
                .style ('opacity', 1.0);

            // shrinkwrap
            instance.bbox = bbox;

            // done
            deferred.resolve ();
        });
        return deferred.promise ();
    }

    /**
     * Initialize the module.
     *
     * @function init
     *
     * @param {string} wrapper_selector - A d3|jQuery selector that points to
     * the element inside of which the graph will be placed.
     *
     * @param {string} id_prefix - The prefix to add to all ids.  Use if you have
     * more than one graph on a page.
     *
     * @returns {Graph} - A graph instance.
     */
    function init ($wrapper, id_prefix) {
        var svg = d3.select ($wrapper.get (0)).append ('svg');

        d3_common.append_marker (svg, id_prefix);

        return {
            'id_prefix' : id_prefix,
            'wrapper'   : $wrapper,
            'svg'       : svg,
            'load_dot'  : load_dot,
            'bbox'      : null,
        };
    }

    return /** @alias module:d3-chord-layout */ {
        'init' : init,
    };
});
