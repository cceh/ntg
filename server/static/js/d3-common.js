'use strict';

/**
 * This module contains common functions built around the D3 library.
 *
 * @module d3-common
 * @author Marcello Perathoner
 */

define(['jquery', 'd3', 'lodash', 'pegjs', 'text!/static/js/dot-grammar.pegjs'], function ($, d3, _, peg, parser_src) {
    var dot_parser = peg.generate(parser_src);

    /**
     * Conversion factor from standard .dot resolution to standard css resolution.
     *
     * Why 96? See: https://www.w3.org/TR/css3-values/#reference-pixel
     *
     * Why 72? All output of GraphViz assumes 72 dpi regardless of the value of
     * the 'dpi' field.  The 'dpi' field is used only for bitmap and svg output.
     *
     * @var {float} dot2css
     */
    var dot2css = 96.0 / 72.0;

    /* A color palette for labez. */
    var Labez = '8888881f77b42ca02cd62728e7ba52ff7f0e9467bd8c564be377c217becf' + 'aec7e8ffbb7898df8aff9896c5b0d5c49c94f7b6d2dbdb8d9edae57f7f7f';

    /* A color palette for cliques.  Pilfered from d3-scale-chromatic.js */
    var Greys = 'fffffff0f0f0d9d9d9bdbdbd969696737373525252252525000000';

    /**
     * Convert a string of hex RGB to a D3 scale.
     *
     * @function color_string_to_palette
     *
     * @param {string} s - The color palette as string
     *
     * @returns {Object} The color palette as D3 scale.
     */

    function color_string_to_palette(s) {
        var no_of_colors = s.length / 6;
        var range = s.match(/.{6}/g).map(function (x) {
            return '#' + x;
        });
        return d3.scaleOrdinal(range).domain(d3.range(no_of_colors));
    }

    /**
     * A D3 color palette suitable for attestations.
     *
     * @var {d3.scale} labez_palette
     */
    var labez_palette = color_string_to_palette(Labez);

    /**
     * A D3 color palette suitable for cliques.
     *
     * @var {d3.scale} cliques_palette
     */
    var cliques_palette = color_string_to_palette(Greys);

    /**
     * Generates a CSS color palette from a D3 scale.
     *
     * @function generate_css_palette
     *
     * @param {d3.scale} labez_scale  - The color palette for labez as D3 scale.
     * @param {d3.scale} clique_scale - The color palette for cliques as D3 scale.
     *
     * @return {string} - The color palette as CSS
     */
    function generate_css_palette(labez_scale, clique_scale) {
        var style;
        function labezFromCharCode(code) {
            return code > 0 ? String.fromCharCode(code + 96) : 'zz';
        }

        /* colors for labez */

        style = _.map(_.zip(labez_scale.domain(), labez_scale.range()), function (pair) {
            var code = labezFromCharCode(pair[0]);
            return '.fg_labez[data-labez="' + code + '"] {\n' + '    color: ' + pair[1] + ' !important;\n' + '    stroke: ' + pair[1] + ';\n' + '}\n' + '.bg_labez[data-labez="' + code + '"] {\n' + '    background-color: ' + pair[1] + ' !important;\n' + '    fill: ' + pair[1] + ';\n' + '}';
        });
        style.unshift('.fg_labez[data-labez] { color: grey !important; stroke: grey; }');
        style.unshift('.bg_labez[data-labez] { background-color: grey !important; fill: grey; }');
        style.unshift('.fg_labez { color: black !important; stroke: black; }');
        style.unshift('.bg_labez { background-color: black !important; fill: black; }');

        /* colors for cliques */

        style = style.concat(_.map(_.zip(clique_scale.domain(), clique_scale.range()), function (pair) {
            var code = pair[0];
            return '.fg_clique[data-clique="' + code + '"] {\n' + '    color: ' + pair[1] + ' !important;\n' + '    stroke: ' + pair[1] + ';\n' + '}\n' + '.bg_clique[data-clique="' + code + '"] {\n' + '    background-color: ' + pair[1] + ' !important;\n' + '    fill: ' + pair[1] + ';\n' + '}';
        }));

        return style.join('\n');
    }

    /**
     * Insert a CSS color palette into the DOM making it active.
     *
     * @function insert_css_palette
     *
     * @param {string} css - The color palette as CSS.
     */
    function insert_css_palette(css) {
        $('<style type="text/css">' + css + '</style>').appendTo('head');
    }

    /**
     * Convert a D3 selection object into a jQuery selection object.
     *
     * @function to_jquery
     *
     * @param {d3.selection} d3_selection - The D3 selection object
     *
     * @return {jQuery.selection} - The jQuery selection object.
     *
     * @see http://collaboradev.com/2014/03/18/d3-and-jquery-interoperability/
     */
    function to_jquery(d3_selection) {
        return $(d3_selection.nodes());
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
    function to_d3(jquery_selection) {
        return d3.selectAll(jquery_selection.toArray());
    }

    /**
     * Append a triangular marker def to the SVG.
     *
     * @function append_marker
     *
     * @param {jQuery.selection|d3.selection} svg - The SVG element.
     * @param {string} id_prefix                  - The id prefix.
     */
    function append_marker(svg, id_prefix) {
        svg.append('defs').append('marker').attr('id', id_prefix + 'triangle').attr('viewBox', '0 0 10 10').attr('refX', '10').attr('refY', '5').attr('markerUnits', 'strokeWidth').attr('markerWidth', '4').attr('markerHeight', '3').attr('orient', 'auto').attr('class', 'link').append('path').attr('d', 'M 0 0 L 10 5 L 0 10 z');
    }

    /**
     * Parse point coordinates from .dot format.
     *
     * @function parse_pt
     *
     * @param {string} commasep - The pt as comma-separated values.
     *
     * @return {Object} The point as dictionary { x, y }
     */
    function parse_pt(commasep) {
        var pt = commasep.split(',');
        if (pt[0] === 's' || pt[0] === 'e') {
            // remove start, end marker
            pt = pt.slice(1);
        }
        return {
            'x': parseFloat(pt[0]) * dot2css,
            'y': parseFloat(pt[1]) * -dot2css
        };
    }

    /**
     * Parse bounding box coordinates from .dot format.
     *
     * From the .dot format docs: rect: "%f,%f,%f,%f" The rectangle
     * llx,lly,urx,ury gives the coordinates, in points, of the lower-left
     * corner \(llx,lly\) and the upper-right corner \(urx,ury\).
     *
     * @function parse_bbox
     *
     * @param {string} commasep - The bbox as comma-separated values.
     *
     * @return {Object} The bbox as dictionary { x, y, width, height }
     */
    function parse_bbox(commasep) {
        var bb = commasep.split(',');
        var llx = parseFloat(bb[0]) * dot2css;
        var lly = parseFloat(bb[1]) * dot2css;
        var urx = parseFloat(bb[2]) * dot2css;
        var ury = parseFloat(bb[3]) * dot2css;
        return {
            'x': llx,
            'y': -ury,
            'width': urx - llx,
            'height': ury - lly
        };
    }

    /**
     * Parse edge path .dot format.
     *
     * @function parse_path
     *
     * @param {string} path - The path in .dot format
     *
     * @return {Array} The path as array of objects  { x, y }
     */
    function parse_path(path) {
        path = $.trim(path.replace('\\\n', ''));
        return _.map(path.split(/\s+/), function (point) {
            return parse_pt(point);
        });
    }

    /**
     * Parse edge path .dot format.
     *
     * @function parse_path_svg
     *
     * @param {string} path - The path in .dot format
     *
     * @return {string} The path as 'Mx,y Cx,y x,y x,y ...'
     */

    function parse_path_svg(path) {
        var ppath = parse_path(path);
        var prefix = 'M';
        var suffix = '';

        if (/e,/.test(path)) {
            suffix = 'L' + ppath[0].x + ',' + ppath[0].y;
            ppath = ppath.slice(1);
        }
        if (/s,/.test(path)) {
            prefix += ppath[0].x + ',' + ppath[0].y + 'L';
            ppath = ppath.slice(1);
        }
        prefix += ppath[0].x + ',' + ppath[0].y + 'C';
        ppath = ppath.slice(1);

        return prefix + _.map(ppath, function (pt) {
            return pt.x + ',' + pt.y;
        }).join(' ') + suffix;
    }

    /**
     * Inflate a bbox.
     *
     * @function inflate_bbox
     *
     * @param {Object} bbox - The bbox as dictionary of x, y, width, height
     * @param {float}  len  - The bbox will be twice this wider and taller.
     *
     * @return {Object} The bbox as dictionary of x, y, width, height
     */
    function inflate_bbox(bbox, len) {
        return {
            'x': bbox.x - len,
            'y': bbox.y - len,
            'width': bbox.width + 2 * len,
            'height': bbox.height + 2 * len
        };
    }

    /**
     * Parse a .dot file into lists of subgraphs, nodes, edges, and graph attributes.
     *
     * @function dot
     *
     * @param {string} url        - The url
     * @param {function} callback - The callback function.
     *
     * @return {Promise}
     */
    function dot(url, callback) {
        return $.get(url, function (data) {
            var graph = dot_parser.parse(data);
            var stmts = graph[0].stmts;

            var attrs = _.keyBy(_.filter(stmts, function (o) {
                return o.type === 'attr';
            }), 'attrType');
            var subgraphs = _.keyBy(_.filter(stmts, function (o) {
                return o.type === 'subgraph';
            }), 'id');
            var nodes = _.keyBy(_.filter(stmts, function (o) {
                return o.type === 'node';
            }), 'id');
            var edges = _.filter(stmts, function (o) {
                return o.type === 'edge';
            });

            attrs.graph.attrs.bbox = parse_bbox(attrs.graph.attrs.bb);

            callback({
                'subgraphs': subgraphs,
                'nodes': nodes,
                'edges': edges,
                'attrs': attrs
            });
        });
    }

    /**
     * Breadth first search in graph
     *
     * @function bfs
     *
     * @param {Object} edges - The edges list
     * @param {string} start - The start node id
     *
     * @return A list of node ids in breadth-first order
     */

    function bfs(edges, start) {
        var ids = [start];
        var queue = [];
        var cur = start;
        function is_adjacent(edge) {
            return edge.elems[0].id === cur;
        }
        while (cur) {
            _.forEach(_.filter(edges, is_adjacent), function (n) {
                var id = n.elems[1].id;
                if (_.indexOf(ids, id) === -1) {
                    ids.push(id);
                    queue.push(id);
                }
            });
            cur = queue.shift();
        }
        return ids;
    }

    return {
        'append_marker': append_marker,
        'bfs': bfs,
        'cliques_palette': cliques_palette,
        'dot': dot,
        'generate_css_palette': generate_css_palette,
        'inflate_bbox': inflate_bbox,
        'insert_css_palette': insert_css_palette,
        'labez_palette': labez_palette,
        'parse_bbox': parse_bbox,
        'parse_path': parse_path,
        'parse_path_svg': parse_path_svg,
        'parse_pt': parse_pt,
        'to_d3': to_d3,
        'to_jquery': to_jquery
    };
});

//# sourceMappingURL=d3-common.js.map