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

            var node_width = graph.attrs.node.attrs.width;

            svg.style ('opacity', 0.0);
            svg.style ('font-size', graph.attrs.graph.attrs.fontsize + 'pt');

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

            var sg = g.append ('g').attr ('class', 'subgraphs');

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
                .attr ('x', function (d) { return d.lp.x; })
                .attr ('y', function (d) { return d.lp.y + (parseFloat (d.lheight) * graph.attrs.graph.attrs.dpi); })
                .text (function (d) { return d.label; });

            // draw the links: a path and a text

            var lg = g.append ('g').attr ('class', 'links');

            var link = lg.selectAll ('.link')
                .data (graph.edges)
                .enter ();

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
                .attr ('d', function (d) {
                    var pos = d.attrs.pos.replace ('\\\n', '');
                    var arr = pos.split (/\s+/);
                    arr[0] = 'M' + arr[0];
                    arr[1] = 'C' + arr[1];
                    // console.log (pos);
                    return arr.join (' ');
                });

            link.filter (function (d) { return d.attrs.rank; })
                .append ('text')
                .attr ('class', 'link')
                .attr ('text-anchor', 'end')
                .append ('textPath')
                .attr ('startOffset', '100%')
                .attr ('xlink:href', function (d) { return '#' + d.id; })
                .append ('tspan')
                .attr ('dy', '-5')
                .attr ('dx', '-5')
                .attr ('rotate', '-90')
                .text (function (d) { return d.attrs.rank; });

            // draw the nodes: a circle and a text in a group

            var ng = g.append ('g').attr ('class', 'nodes');

            var node = ng.selectAll ('g.node')
                .data (_.map (graph.nodes, 'attrs'))
                .enter ().append ('g')
                .attr ('data-ms-id', function (d) { return d.ms_id; })
                .attr ('class', function (d) {
                    return 'node node-' + (d.children ? 'internal' : 'leaf');
                })
                .attr ('transform', function (d) {
                    return 'translate(' + d.pos + ')';
                });

            node.append ('circle')
                .attr ('class', 'node fg_labez')
                .attr ('data-labez', function (d) { return d.labez; })
                .attr ('r', function (d) { return (d.width || node_width) * graph.attrs.graph.attrs.dpi / 2; })
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
                .text (function (d) { return d.label; });

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
