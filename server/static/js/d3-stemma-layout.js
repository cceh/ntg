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
     * Create an SVG graph from a dot file.
     *
     * @function load_dot
     *
     * @param {string} url - The url (must serve dot format).
     *
     * @returns {Promise} - A promise resolved when all SVG elements have been created.
     */
    function load_dot (url) {
        var that = this; // instance
        var svg = this.svg;
        svg.selectAll ('g').transition ().duration (300).style ('opacity', 0.0)
            .remove ();
        var deferred = new $.Deferred ();

        $.get (url, function (data) {
            var graph = that.parser.parse (data);
            var stmts = graph[0].stmts;

            var attrs = _.keyBy (_.filter (stmts, function (o) { return o.type === 'attr'; }), 'attrType');
            var nodes = _.keyBy (_.filter (stmts, function (o) { return o.type === 'node'; }), 'id');
            var links = _.filter (stmts, function (o) { return o.type === 'edge'; });

            // shrinkwrap
            var bb = attrs.graph.attrs.bb.split (',');
            var bbox = {
                'x'      : bb[0],
                'y'      : bb[1],
                'width'  : bb[2],
                'height' : bb[3],
            };
            var g = svg.append ('g');

            svg.attr ('width',  bbox.width).style ('opacity', 0.0);

            svg.transition ()
                .duration (300)
                .attr ('height', bbox.height)
                .transition ()
                .duration (300)
                .style ('opacity', 1.0);

            // g.attr ('transform', 'translate(' + -bbox.x + ',' + -bbox.y + ')');

            // replace ids with node objects
            _.forEach (links, function (link, i) {
                link.source = nodes[link.elems[0].id];
                link.target = nodes[link.elems[1].id];
                link.id = that.id_prefix + 'link_' + i;
            });

            var link = g.selectAll ('.link')
                .data (links)
                .enter ();

            link.append ('path')
                .attr ('id', function (d) { return d.id; })
                .attr ('class', function (d) {
                    return 'link' + (d.attrs.broken ? ' broken' : '');
                })
                // .attr ('marker-end', 'url(#triangle)')
                .attr ('d', function (d) {
                    var path = '';
                    var arr = d.attrs.pos.split (' ');
                    path += 'M' + arr.shift ();
                    while (arr.length) {
                        path += 'C' + arr.shift () + ' ' + arr.shift () + ' ' + arr.shift ();
                    }
                    return path;
                });

            link.filter (function (d) {
                return d.attrs.rank;
            })
                .append ('text')
                .attr ('text-anchor', 'end')
                .append ('textPath')
                .attr ('startOffset', '100%')
                .attr ('xlink:href', function (d) { return '#' + d.id; })
                .append ('tspan')
                .attr ('dy', '-5')
                .text (function (d) { return d.attrs.rank ? d.attrs.rank + '      ' : ''; }); // <-- &nbsp; !!!


            var node = g.selectAll ('.node')
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
                .attr ('r', that.radius);

            node.append ('text')
                .attr ('class', 'node')
                .text (function (d) { return d.label; });

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
        var root = d3.select (wrapper_selector);
        root.selectAll ('*').remove ();
        var svg = root.append ('svg');

        svg
            .append ('defs')
            .append ('marker')
            .attr ('id',           'triangle')
            .attr ('viewBox',      '0 0 10 10')
            .attr ('refX',         '0')
            .attr ('refY',         '5')
            .attr ('markerUnits',  'strokeWidth')
            .attr ('markerWidth',  '4')
            .attr ('markerHeight', '3')
            .attr ('orient',       'auto')
            .append ('path')
            .attr ('d', 'M 0 0 L 10 5 L 0 10 z');

        return {
            'id_prefix' : id_prefix,
            'svg'       : svg,
            'load_dot'  : load_dot,
            'parser'    : dot_parser,
            'radius'    : 15,
        };
    }

    return /** @alias module:d3-stemma-layout */ {
        'init' : init,
    };
});
