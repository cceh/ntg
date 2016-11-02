// This is a RequireJS module.
define (['jquery', 'd3', 'lodash', 'relatives', 'jquery-ui'],

function ($, d3, _, relatives) {
    'use strict';

    var radius = 15;

    function init_json (url, selector, id_prefix) {
        // Display a precomputed DAG
        //
        // Load a precomputed GraphViz DAG in JSON format and convert it into a
        // SVG, then append the SVG to the element specified by the selector.

        var root = d3.select (selector);
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

        var g = svg.append ('g');

        d3.json (url, function (error, json) {
            if (error) {
                throw error;
            }

            // replace indices with node objects
            _.forEach (json.links, function (link) {
                link.source = json.nodes[link.source];
                link.target = json.nodes[link.target];
            });

            var link = g.selectAll ('.link')
                .data (json.links)
                .enter ();

            link.append ('path')
                // .filter (function (d) { return d.depth > 1; })
                .attr ('id', function (d, i) { return id_prefix + 'link_' + i; })
                .attr ('class', 'link')
                .attr ('marker-end', 'url(#triangle)')
                .attr ('d', function (d) {
                    var path = '';
                    var arr = d.pos.split (' ');
                    // var endp = arr.shift ().substring (2); // arrow endpoint
                    path += 'M' + arr.shift ();
                    while (arr.length) {
                        path += 'C' + arr.shift () + ' ' + arr.shift () + ' ' + arr.shift ();
                    }
                    // path += 'L' + endp;
                    return path;
                });

            link.append ('text')
                .attr ('text-anchor', 'end')
                .append ('textPath')
                .attr ('startOffset', '100%')
                .attr ('xlink:href', function (d, i) { return '#' + id_prefix + 'link_' + i; })
                .text (function (d) { return d.rank ? d.rank + '      ' : ''; }); // <-- &nbsp; !!!


            var node = g.selectAll ('.node')
                .data (json.nodes)
                .enter ().append ('g')
                // .filter (function (d) { return d.depth > 0; })
                .attr ('data-ms-id', function (d) { return d['data-ms-id']; })
                .attr ('class', function (d) {
                    return 'node node-' + (d.children ? 'internal' : 'leaf');
                })
                .attr ('transform', function (d) {
                    return 'translate(' + d.x + ',' + d.y + ')';
                });

            node.append ('circle')
                .attr ('class', 'node fg_labez')
                // .attr ('data-href',  function (d) { return d.href; })
                .attr ('data-labez', function (d) { return d.labez; })
                .attr ('r', radius);

            node.append ('text')
                .attr ('class', 'node')
                .text (function (d) { return d.label; });

            // relatives.init_bootstrap_popup (node);
            relatives.init_jquery_popup (node);

            // shrinkwrap
            var bbox = g.node ().getBBox ();
            svg.attr ('width',  bbox.width)
                .attr ('height', bbox.height);
            g.attr ('transform', 'translate(' + -bbox.x + ',' + -bbox.y + ')');
        });
    }

    // return an object that defines this module
    return {
        'init_json' : init_json,
    };
});
