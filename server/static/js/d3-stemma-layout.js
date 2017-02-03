/**
 * This module converts a graph in .dot format into SVG.  The .dot file must be
 * pre-processed in order to contain coordinates for each node and bezier paths
 * for each edge.
 *
 * @module d3-stemma-layout
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
        var instance = this; // instance
        var dot_dpi = 72;
        var css_dpi = 96;

        var svg = this.svg;
        svg.selectAll ('g').transition ().duration (300).style ('opacity', 0.0)
            .remove ();
        var deferred = new $.Deferred ();

        d3_common.dot (url, function (graph) {
            // if we have subgraphs, retrieve their nodes too
            _.forEach (graph.subgraphs, function (subgraph) {
                var subgraph_nodes = _.keyBy (_.filter (subgraph.stmts,
                                                        function (o) { return o.type === 'node'; }), 'id');
                _.assign (graph.nodes, subgraph_nodes); // copy
                subgraph.attrs = _.keyBy (_.filter (subgraph.stmts,
                                                    function (o) { return o.type === 'attr'; }), 'attrType');
                subgraph.attrs.graph.attrs.bbox = d3_common.parse_bbox (subgraph.attrs.graph.attrs.bb);
                subgraph.attrs.graph.attrs.lp   = d3_common.parse_pt   (subgraph.attrs.graph.attrs.lp);
            });

            // shrinkwrap + accomodate for the thick borders of circles
            instance.bbox = d3_common.inflate_bbox (graph.attrs.graph.attrs.bbox, 3);

            var node_width  = graph.attrs.node.attrs.width;     // in inches
            var node_height = graph.attrs.node.attrs.height;    // in inches
            var font_size   = graph.attrs.graph.attrs.fontsize; // in points

            svg.style ('opacity', 0.0);
            svg.style ('font-size', font_size + 'pt');

            svg.transition ('svg')
                .duration (300)
                .attr ('height', instance.bbox.height)
                .attr ('width',  instance.bbox.width)
                .transition ()
                .duration (300)
                .style ('opacity', 1.0);

            // put id also inside node attrs
            _.forEach (graph.nodes, function (v, k) {
                v.attrs.id = k;
            });

            // give all links an id
            _.forEach (graph.edges, function (link, i) {
                link.id = instance.id_prefix + 'link_' + i;
            });

            var g = svg.append ('g')
                .attr ('transform', 'translate(' + -instance.bbox.x + ',' + -instance.bbox.y + ')');

            // draw the subgraphs: a rectangle with a label

            var sg = g.append ('g')
                .attr ('class', 'subgraphs');

            var subgraph = sg.selectAll ('.subgraph')
                .data (_.map (graph.subgraphs, 'attrs.graph.attrs'))
                .enter ();

            subgraph.append ('rect')
                .attr ('x',      function (d) { return d.bbox.x; })
                .attr ('y',      function (d) { return d.bbox.y; })
                .attr ('width',  function (d) { return d.bbox.width; })
                .attr ('height', function (d) { return d.bbox.height; })
                .attr ('class', 'subgraph');

            subgraph.append ('text')
                .attr ('class', 'subgraph')
                // lp indicates the center of the label
                .attr ('x', function (d) { return d.lp.x; })
                .attr ('y', function (d) { return d.lp.y; })
                .style ('font-size', function (d) {
                    return (d.fontsize || font_size) + 'pt';
                })
                .text (function (d) { return d.label; });

            // draw the links: a path and a text

            var lg = g.append ('g').attr ('class', 'links');

            var link = lg.selectAll ('.link')
                .data (graph.edges)
                .enter ();

            link.filter (function (d) { return d.attrs && d.attrs.head_lp })
                .each (function (d) {
                    d.attrs.head_lp = d3_common.parse_pt (d.attrs.head_lp);
                });

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
                .attr ('d', function (d) { return d3_common.parse_path_svg (d.attrs.pos); })

            link.filter (function (d) { return d.attrs && d.attrs.head_lp && d.attrs.headlabel; })
                .append ('text')
                .attr ('class', 'link')
                .attr ('x', function (d) { return d.attrs.head_lp.x; })
                .attr ('y', function (d) { return d.attrs.head_lp.y; })
                .text (function (d) { return d.attrs.headlabel; });

            // draw the nodes: a circle and a text in a group

            var ng = g.append ('g').attr ('class', 'nodes');

            var node = ng.selectAll ('g.node')
                .data (_.map (graph.nodes, 'attrs'))
                .enter ();

            node.filter (function (d) { return d.pos })
                .each (function (d) {
                    d.pos = d3_common.parse_pt (d.pos);
                });

            var groups = node.append ('g')
                .attr ('data-ms-id', function (d) { return d.ms_id; })
                .attr ('class', function (d) {
                    return 'node node-' + (d.children ? 'internal' : 'leaf');
                })
                .attr ('transform', function (d) {
                    return 'translate(' + d.pos.x + ',' + d.pos.y + ')';
                });

            groups.append ('ellipse')
                .attr ('class', 'node fg_labez')
                .attr ('data-labez', function (d) { return d.labez; })
                .attr ('rx', function (d) {
                    return (d.width  || node_width) * css_dpi / 2;
                })
                .attr ('ry', function (d) {
                    return (d.height || node_height) * css_dpi / 2;
                })
                .on ('mouseenter', function (d) {
                    d3.selectAll ('path.link.' + instance.id_prefix + 'sid-' + d.id).classed ('hi-source', true);
                    d3.selectAll ('path.link.' + instance.id_prefix + 'tid-' + d.id).classed ('hi-target', true);
                })
                .on ('mouseleave', function (d) {
                    d3.selectAll ('path.link.' + instance.id_prefix + 'sid-' + d.id).classed ('hi-source', false);
                    d3.selectAll ('path.link.' + instance.id_prefix + 'tid-' + d.id).classed ('hi-target', false);
                });

            groups.append ('text')
                .attr ('class', 'node')
                .text (function (d) { return d.label; });

            /*
            var r = node_width * css_dpi / 2;

            groups.append ('foreignObject')
                .attr ('x', -r)
                .attr ('y', -r)
                .attr ('width', 2 * r)
                .attr ('height', 2 * r)
                .append ('xhtml:body')
                .append ('div')
                .attr ('class', 'node')
                .text (function (d) { return d.label; });
            */

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
     * @param {jQuery} $wrapper - A jQuery selector that points to
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

    return /** @alias module:d3-stemma-layout */ {
        'init' : init,
    };
});
