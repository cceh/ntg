/**
 * This module converts a graph in .dot format into SVG.  The .dot file must be
 * pre-processed in order to contain coordinates for each node and bezier paths
 * for each edge.
 *
 * @module d3-stemma-layout
 * @author Marcello Perathoner
 */

define (['jquery', 'd3', 'lodash', 'pegjs', 'text!/static/js/dot-grammar.pegjs'],

function ($, d3, _, peg, parser_src) {
    'use strict';

    var dot_parser = peg.generate (parser_src);

    /**
     * Parse bounding box coordinates from .dot format.
     *
     * @function parse_bbox
     *
     * @param commasep {string} The bbox as comma-separated values.
     *
     * @return {Object} The bbox as dictionary { x, y, width, height }
     */

    function parse_bbox (commasep) {
        var bb = commasep.split (',');
        return {
            'x'      : bb[0],
            'y'      : bb[1],
            'width'  : bb[2] - bb[0],
            'height' : bb[3] - bb[1],
        };
    }

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

        $.get (url, function (data) {
            var graph = instance.parser.parse (data);
            var stmts = graph[0].stmts;

            var subgraphs = _.keyBy (_.filter (stmts, function (o) { return o.type === 'subgraph'; }), 'id');
            var nodes     = _.keyBy (_.filter (stmts, function (o) { return o.type === 'node'; }), 'id');
            var links     = _.filter (stmts, function (o) { return o.type === 'edge'; });
            var attrs     = _.keyBy (_.filter (stmts, function (o) { return o.type === 'attr'; }), 'attrType');

            // if we have subgraphs, retrieve their nodes too
            _.forEach (subgraphs, function (subgraph) {
                var subgraph_nodes = _.keyBy (_.filter (subgraph.stmts,
                                                        function (o) { return o.type === 'node'; }), 'id');
                _.assign (nodes, subgraph_nodes);
                var subgraph_attrs = _.keyBy (_.filter (subgraph.stmts,
                                                        function (o) { return o.type === 'attr'; }), 'attrType');
                subgraph.bbox = parse_bbox (subgraph_attrs.graph.attrs.bb);
            });

            // shrinkwrap
            var graph_attrs = attrs.graph.attrs;
            instance.bbox = parse_bbox (graph_attrs.bb);

            var node_width = attrs.node.attrs.width;

            svg.style ('opacity', 0.0);
            svg.style ('font-size', graph_attrs.fontsize + 'pt');

            svg.transition ('svg')
                .duration (300)
                .attr ('height', instance.bbox.height)
                .attr ('width',  instance.bbox.width)
                .transition ()
                .duration (300)
                .style ('opacity', 1.0);

            // replace ids with node objects
            _.forEach (links, function (link, i) {
                link.source = nodes[link.elems[0].id];
                link.target = nodes[link.elems[1].id];
                link.id = instance.id_prefix + 'link_' + i;
            });

            // draw the subgraphs: a rectangle

            var sg = svg.append ('g').attr ('class', 'subgraphs');

            var subgraph = sg.selectAll ('.subgraph')
                .data (_.map (subgraphs, 'bbox'))
                .enter ();

            subgraph.append ('rect')
                .attr ('x',      function (d) { return d.x; })
                .attr ('y',      function (d) { return d.y; })
                .attr ('width',  function (d) { return d.width; })
                .attr ('height', function (d) { return d.height; })
                .attr ('class', 'subgraph')

            // draw the links: a path and a text

            var lg = svg.append ('g').attr ('class', 'links');

            var link = lg.selectAll ('.link')
                .data (links)
                .enter ();

            link.append ('path')
                .attr ('id', function (d) { return d.id; })
                .attr ('class', function (d) {
                    return 'link' + (d.attrs.broken ? ' broken' : '');
                })
                .attr ('marker-end', 'url(#' + instance.id_prefix + 'triangle)')
                .attr ('d', function (d) {
                    var path = '';
                    var arr = d.attrs.pos.split (' ');
                    path += 'M' + arr.shift ();
                    while (arr.length) {
                        path += 'C' + arr.shift () + ' ' + arr.shift () + ' ' + arr.shift ();
                    }
                    return path;
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

            var ng = svg.append ('g').attr ('class', 'nodes');

            var node = ng.selectAll ('.node')
                .data (_.map (nodes, 'attrs'))
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
                .attr ('r', function (d) { return (d.width || node_width) * graph_attrs.dpi / 2; });

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
     * @param {string} wrapper_selector - A d3|jQuery selector that points to
     * the element inside of which the graph will be placed.
     *
     * @param {string} id_prefix - The prefix to add to all ids.  Use if you have
     * more than one graph on a page.
     *
     * @returns {Graph} - A graph instance.
     */
    function init (wrapper_selector, id_prefix) {
        var wrapper = d3.select (wrapper_selector);
        wrapper.selectAll ('*').remove ();
        var svg = wrapper.append ('svg');

        svg
            .append ('defs')
            .append ('marker')
            .attr ('id',           id_prefix + 'triangle')
            .attr ('viewBox',      '0 0 10 10')
            .attr ('refX',         '10')
            .attr ('refY',         '5')
            .attr ('markerUnits',  'strokeWidth')
            .attr ('markerWidth',  '4')
            .attr ('markerHeight', '3')
            .attr ('orient',       'auto')
            .attr ('class',        'link')
            .append ('path')
            .attr ('d', 'M 0 0 L 10 5 L 0 10 z');

        return {
            'id_prefix' : id_prefix,
            'wrapper'   : wrapper,
            'svg'       : svg,
            'load_dot'  : load_dot,
            'parser'    : dot_parser,
            'bbox'      : null,
        };
    }

    return /** @alias module:d3-stemma-layout */ {
        'init' : init,
    };
});
