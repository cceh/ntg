/**
 * This module contains common functions built around the D3 library.
 *
 * @module d3-common
 * @author Marcello Perathoner
 */

define ([
    'jquery',
    'd3',
    'lodash',
    'pegjs',
    'text!/static/js/dot-grammar.pegjs',
], function ($, d3, _, peg, parser_src) {
    'use strict';

    var dot_parser = peg.generate (parser_src);

    /**
     * Conversion factor from standard .dot resoolution to standard css resolution.
     *
     * Why 96? See: https://www.w3.org/TR/css3-values/#reference-pixel
     *
     * Why 72? All output of GraphViz assumes 72 dpi regardless of the value of
     * the 'dpi' field.  The 'dpi' field is used only for bitmap and svg output.
     *
     * @var {float} dot2css
     */
    var dot2css = 96.0 / 72.0;

    function brighten_range (range, dummy_k) {
        return range.map (function (c) {
            var clr = d3.color (c);
            clr.opacity = 0.2;
            return clr.toString ();
        });
    }

    /* pilfered from d3-scale-chromatic.js */
    var Greys = 'fffffff0f0f0d9d9d9bdbdbd969696737373525252252525000000';

    function color_string_to_range (s) {
        return s.match (/.{6}/g).map (function (x) {
            return '#' + x;
        });
    }

    /**
     * A D3 color palette suitable for attestations.
     *
     * @var {d3.scale} labez_palette
     */
    var labez_palette = d3.scaleOrdinal ()
        .domain (d3.range (20))
        .range (['#888888', '#1f77b4', '#2ca02c', '#d62728',
                 '#e7ba52', '#ff7f0e', '#9467bd', '#8c564b',
                 '#e377c2', '#17becf', '#aec7e8', '#ffbb78',
                 '#98df8a', '#ff9896', '#c5b0d5', '#c49c94',
                 '#f7b6d2', '#dbdb8d', '#9edae5', '#7f7f7f']);

    /**
     * A D3 color palette suitable for splits.
     *
     * @var {d3.scale} splits_palette
     */
    var splits_palette = d3.scaleOrdinal (color_string_to_range (Greys)).domain (d3.range (9));

    /**
     * Generates a CSS color palette from a D3 scale.
     *
     * @function generate_css_palette
     *
     * @param labez_scale {d3.scale} - The color palette for labez as D3 scale.
     * @param split_scale {d3.scale} - The color palette for splits as D3 scale.
     *
     * @return {string} - The color palette as CSS
     */
    function generate_css_palette (labez_scale, split_scale) {
        var style;
        function labezFromCharCode (code) {
            return code > 0 ? String.fromCharCode (code + 96) : 'z';
        }
        style = _.map (_.zip (labez_scale.domain (), labez_scale.range ()), function (pair) {
            var code = labezFromCharCode (pair[0]);
            return (
                '.fg_labez[data-labez="' + code + '"] {\n' +
                '    color: ' + pair[1] + ' !important;\n' +
                '    stroke: ' + pair[1] + ';\n' +
                '}\n' +
                '.bg_labez[data-labez="' + code + '"] {\n' +
                '    background-color: ' + pair[1] + ' !important;\n' +
                '    fill: ' + pair[1] + ';\n' +
                '}'
            );
        });
        style.unshift ('.fg_labez { color: black !important; stroke: black; }');
        style.unshift ('.bg_labez { background-color: black !important; fill: black; }');

        style = style.concat (_.map (_.zip (split_scale.domain (), split_scale.range ()), function (pair) {
            var code = pair[0];
            return (
                '.fg_split[data-split="' + code + '"] {\n' +
                '    color: ' + pair[1] + ' !important;\n' +
                '    stroke: ' + pair[1] + ';\n' +
                '}\n' +
                '.bg_split[data-split="' + code + '"] {\n' +
                '    background-color: ' + pair[1] + ' !important;\n' +
                '    fill: ' + pair[1] + ';\n' +
                '}'
            );
        }));

        return style.join ('\n');
    }

    /**
     * Insert a CSS color palette into the DOM making it active.
     *
     * @function insert_css_palette
     *
     * @param css {string} - The color palette as CSS.
     */
    function insert_css_palette (css) {
        $ ('<style type="text/css">' + css + '</style>').appendTo ('head');
    }

    // For D3 and jQuery Interoperability see:
    //   http://collaboradev.com/2014/03/18/d3-and-jquery-interoperability/

    /**
     * Convert a D3 selection object into a jQuery selection object.
     *
     * @function to_jquery
     *
     * @param {d3.selection} d3_selection - The D3 selection object
     *
     * @return {jQuery.selection} - The jQuery selection object.
     */
    function to_jquery (d3_selection) {
        return $ (d3_selection.nodes ());
    }

    /**
     * Convert a jQuery selection object into a D3 selection object.
     *
     * @function to_d3
     *
     * @param {jQuery.selection} jquery_selection - The jQuery selection object
     *
     * @return {D3.selection} - The D3 selection object.
     */
    function to_d3 (jquery_selection) {
        return d3.selectAll (jquery_selection.toArray ());
    }

    /**
     * Append a triangular marker def to the SVG.
     *
     * @function append_marker
     *
     * @param svg {jQuery.selection|d3.selection} The SVG element.
     * @param id_prefix The id prefix.
     */
    function append_marker (svg, id_prefix) {
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
    }

    /**
     * Parse point coordinates from .dot format.
     *
     * @function parse_pt
     *
     * @param commasep {string} The pt as comma-separated values.
     *
     * @return {Object} The point as dictionary { x, y }
     */
    function parse_pt (commasep) {
        var pt = commasep.split (',');
        return {
            'x' : parseFloat (pt[0]) * dot2css,
            'y' : parseFloat (pt[1]) * dot2css,
        };
    }

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
            'x'      : parseFloat (bb[0] * dot2css),
            'y'      : parseFloat (bb[1] * dot2css),
            'width'  : (parseFloat (bb[2]) - parseFloat (bb[0])) * dot2css,
            'height' : (parseFloat (bb[3]) - parseFloat (bb[1])) * dot2css,
        };
    }

    /**
     * Parse edge path .dot format.
     *
     * @function parse_path
     *
     * @param path {string} The path in .dot format
     *
     * @return {Array} The path as array of objects  { x, y }
     */
    function parse_path (path) {
        path = path.replace ('\\\n', '');
        return _.map (path.split (/\s+/), function (point) {
            return parse_pt (point);
        });
    }

    /**
     * Parse edge path .dot format.
     *
     * @function parse_path_svg
     *
     * @param path {string} The path in .dot format
     *
     * @return {string} The path as 'Mx,y Cx,y x,y x,y ...'
     */

    function parse_path_svg (path) {
        path = parse_path (path);
        var s = 'M' + path[0].x + ',' + path[0].y + 'C';

        return s + _.map (path.slice (1), function (pt) {
            return pt.x + ',' + pt.y;
        }).join (' ');
    }

    /**
     * Inflate a bbox.
     *
     * @function inflate_bbox
     *
     * @param bbox The bbox as dictionary { x, y, width, height }
     * @param len  The bbox will be twice this wider and taller.
     *
     * @return {Object} The bbox as dictionary { x, y, width, height }
     */
    function inflate_bbox (bbox, len) {
        return {
            'x'      : bbox.x - len,
            'y'      : bbox.y - len,
            'width'  : bbox.width  + (2 * len),
            'height' : bbox.height + (2 * len),
        };
    }

    /**
     * Parse a .dot file.
     *
     * @function dot
     *
     * @param url {string}        The url
     * @param callback {function} The callback function.
     *
     * @return {Promise}
     */
    function dot (url, callback) {
        return $.get (url, function (data) {
            var graph = dot_parser.parse (data);
            var stmts = graph[0].stmts;

            var attrs     = _.keyBy (_.filter (stmts, function (o) { return o.type === 'attr';     }), 'attrType');
            var subgraphs = _.keyBy (_.filter (stmts, function (o) { return o.type === 'subgraph'; }), 'id');
            var nodes     = _.keyBy (_.filter (stmts, function (o) { return o.type === 'node';     }), 'id');
            var edges     =          _.filter (stmts, function (o) { return o.type === 'edge';     });

            attrs.graph.attrs.bbox = parse_bbox (attrs.graph.attrs.bb);

            callback ({
                'subgraphs' : subgraphs,
                'nodes'     : nodes,
                'edges'     : edges,
                'attrs'     : attrs,
            });
        });
    }

    /**
     * Breadth first search in graph
     *
     * @function bfs
     *
     * @param edges The edges list
     * @param start The start node id
     *
     * @return A list of node ids in breadth-first order
     */

    function bfs (edges, start) {
        var ids   = [start];
        var queue = [];
        var cur   = start;
        function is_adjacent (edge) {
            return edge.elems[0].id === cur;
        }
        while (cur) {
            _.forEach (_.filter (edges, is_adjacent), function (n) {
                var id = n.elems[1].id;
                if (_.indexOf (ids, id) === -1) {
                    ids.push (id);
                    queue.push (id);
                }
            });
            cur = queue.shift ();
        }
        return ids;
    }

    return {
        'append_marker'        : append_marker,
        'bfs'                  : bfs,
        'brighten_range'       : brighten_range,
        'dot'                  : dot,
        'generate_css_palette' : generate_css_palette,
        'inflate_bbox'         : inflate_bbox,
        'insert_css_palette'   : insert_css_palette,
        'labez_palette'        : labez_palette,
        'parse_bbox'           : parse_bbox,
        'parse_path'           : parse_path,
        'parse_path_svg'       : parse_path_svg,
        'parse_pt'             : parse_pt,
        'splits_palette'       : splits_palette,
        'to_d3'                : to_d3,
        'to_jquery'            : to_jquery,
    };
});
