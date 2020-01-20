/**
 * This module contains common functions built around the D3 library.
 *
 * @module client/d3_common
 * @author Marcello Perathoner
 */

import { zip }          from 'lodash';
import { scaleOrdinal } from 'd3-scale';
import { range }        from 'd3-array';

import dot_parser from 'dot-grammar.pegjs';

/**
 * Conversion factor from standard .dot resolution to standard css resolution.
 *
 * Why 96? See: https://www.w3.org/TR/css3-values/#reference-pixel
 *
 * Why 72? All output of GraphViz assumes 72 dpi regardless of the value of
 * the 'dpi' field.  The 'dpi' field is used only for bitmap and svg output.
 *
 * @const {float} dot2css
 */
const dot2css = 96.0 / 72.0;

/* A color palette for labez. */
const Labez = '8888881f77b42ca02cd62728e7ba52ff7f0e9467bd8c564be377c217becf'
            + 'aec7e8ffbb7898df8aff9896c5b0d5c49c94f7b6d2dbdb8d9edae57f7f7f';

/* A color palette for cliques.  Pilfered from d3-scale-chromatic.js */
const Greys = 'fffffff0f0f0d9d9d9bdbdbd969696737373525252252525000000';

/**
 * Convert a string of hex RGB to a D3 scale.
 *
 * @function color_string_to_palette
 *
 * @param {String} s - The color palette as string
 *
 * @returns {Object} The color palette as D3 scale.
 */

function color_string_to_palette (s) {
    const no_of_colors = s.length / 6;
    const rg = s.match (/.{6}/g).map (x => '#' + x);
    return scaleOrdinal (rg).domain (range (no_of_colors));
}

/**
 * A D3 color palette suitable for attestations.
 *
 * @const {d3.scale} labez_palette
 */
const labez_palette = color_string_to_palette (Labez);

/**
 * A D3 color palette suitable for cliques.
 *
 * @const {d3.scale} cliques_palette
 */
const cliques_palette = color_string_to_palette (Greys);

/**
 * Generates a CSS color palette from a D3 scale.
 *
 * @function generate_css_palette
 *
 * @param {d3.scale} labez_scale  - The color palette for labez as D3 scale.
 * @param {d3.scale} clique_scale - The color palette for cliques as D3 scale.
 *
 * @returns {String} The color palette as CSS
 */
function generate_css_palette (labez_scale, clique_scale) {
    function labezFromCharCode (code) {
        return code > 0 ? String.fromCharCode (code + 96) : 'zz';
    }

    const style = [
        '.fg_labez              { color:            black !important; stroke: black !important; }',
        '.bg_labez              { background-color: white !important; fill:   white !important; }',

        '.fg_clique             { color:            black !important; stroke: black !important; }',
        '.bg_clique             { background-color: white !important; fill:   white !important; }',

        '.fg_labez[data-labez]  { color:            grey  !important; stroke: grey  !important; }',
        '.bg_labez[data-labez]  { background-color: grey  !important; fill:   grey  !important; }',

        '[data-labez] .bgp_labez { background-color: grey  !important; fill:   grey  !important; }',
    ];

    /* colors for labez */

    for (const z of zip (labez_scale.domain (), labez_scale.range ())) {
        const [code, rgb] = [labezFromCharCode (z[0]), z[1] + ' !important'];
        style.push (`.fg_labez[data-labez="${code}"] { color:            ${rgb}; stroke: ${rgb}; }`);
        style.push (`.bg_labez[data-labez="${code}"] { background-color: ${rgb}; fill:   ${rgb}; }`);

        // for labezator.vue
        style.push (`[data-labez="${code}"] .bgp_labez { background-color: ${rgb}; fill:   ${rgb}; }`);
    }

    /* colors for cliques */

    for (const z of zip (clique_scale.domain (), clique_scale.range ())) {
        const [code, rgb] = [z[0], z[1] + ' !important'];
        style.push (`.fg_clique[data-clique="${code}"] { color:            ${rgb}; stroke: ${rgb}; }`);
        style.push (`.bg_clique[data-clique="${code}"] { background-color: ${rgb}; fill:   ${rgb}; }`);
    }

    return style.join ('\n');
}

/**
 * Insert a CSS color palette into the DOM making it active.
 *
 * @function insert_css_palette
 *
 * @param {String} css - The color palette as CSS.
 */
function insert_css_palette (css) {
    const style = document.createElement ('style');
    style.setAttribute ('type', 'text/css');
    style.appendChild (document.createTextNode (css));
    document.querySelector ('head').appendChild (style);
}

/**
 * Append a triangular marker def to the SVG.
 *
 * @function append_marker
 *
 * @param {d3.selection} svg       - The SVG element.
 * @param {String}       id_prefix - The id prefix.
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
 * @param {String} commasep - The pt as comma-separated values.
 *
 * @returns {Object} The point as dictionary { x, y }
 */
function parse_pt (commasep) {
    let pt = commasep.split (',');
    if (pt[0] === 's' || pt[0] === 'e') {
        // remove start, end marker
        pt = pt.slice (1);
    }
    return {
        'x' : parseFloat (pt[0]) * dot2css,
        'y' : parseFloat (pt[1]) * -dot2css,
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
 * @param {String} commasep - The bbox as comma-separated values.
 *
 * @returns {Object} The bbox as dictionary { x, y, width, height }
 */
function parse_bbox (commasep) {
    const bb = commasep.split (',');
    const llx = parseFloat (bb[0]) * dot2css;
    const lly = parseFloat (bb[1]) * dot2css;
    const urx = parseFloat (bb[2]) * dot2css;
    const ury = parseFloat (bb[3]) * dot2css;
    return {
        'x'      : llx,
        'y'      : -ury,
        'width'  : urx - llx,
        'height' : ury - lly,
    };
}

/**
 * Parse edge path .dot format.
 *
 * @function parse_path
 *
 * @param {String} path - The path in .dot format
 *
 * @returns {Array} The path as array of objects  { x, y }
 */
function parse_path (path) {
    path = path.replace ('\\\n', '').trim ();
    return path.split (/\s+/).map ((point) => parse_pt (point));
}

/**
 * Parse edge path .dot format.
 *
 * @function parse_path_svg
 *
 * @param {String} path - The path in .dot format
 *
 * @returns {String} The path as 'Mx,y Cx,y x,y x,y ...'
 */

function parse_path_svg (path) {
    let ppath = parse_path (path);
    let prefix = 'M';
    let suffix = '';

    if (/e,/.test (path)) {
        suffix = 'L' + ppath[0].x + ',' + ppath[0].y;
        ppath = ppath.slice (1);
    }
    if (/s,/.test (path)) {
        prefix += ppath[0].x + ',' + ppath[0].y + 'L';
        ppath = ppath.slice (1);
    }
    prefix += ppath[0].x + ',' + ppath[0].y + 'C';
    ppath = ppath.slice (1);

    return prefix + ppath.map (pt => pt.x + ',' + pt.y).join (' ') + suffix;
}

/**
 * Inflate a bbox.
 *
 * @function inflate_bbox
 *
 * @param {Object} bbox - The bbox as dictionary of x, y, width, height
 * @param {float}  len  - The bbox will be twice this wider and taller.
 *
 * @returns {Object} The bbox as dictionary of x, y, width, height
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
 * Create an object from an array of objects.
 *
 * The keys are taken from a specified attribute of the array elements.
 *
 * @function key_by
 *
 * @param {Array}  a    - The input array of objects
 * @param {String} attr - The attribute to take the key from.
 *
 * @returns {Object} The object.
 */

export function key_by (a, attr) {
    return Object.fromEntries (a.map (item => [item[attr], item]));
}

/**
 * Parse a .dot file into lists of subgraphs, nodes, edges, and graph attributes.
 *
 * @function dot
 *
 * @param {String} data - The data in .dot format
 *
 * @returns {Object}
 */
function dot (data) {
    const graph = dot_parser.parse (data);
    const stmts = graph[0].stmts;

    const attrs     = key_by (stmts.filter (o => o.type === 'attr'),     'attrType');
    const subgraphs = key_by (stmts.filter (o => o.type === 'subgraph'), 'id');
    const nodes     = key_by (stmts.filter (o => o.type === 'node'),     'id');
    const edges     =         stmts.filter (o => o.type === 'edge');

    attrs.graph.attrs.bbox = parse_bbox (attrs.graph.attrs.bb);

    // if we have subgraphs, retrieve their nodes too
    for (const subgraph of Object.values (subgraphs)) {
        const subgraph_nodes = key_by (subgraph.stmts.filter (o => o.type === 'node'), 'id');
        Object.assign (nodes, subgraph_nodes); // copy
        subgraph.attrs = key_by (subgraph.stmts.filter (o => o.type === 'attr'), 'attrType');
        subgraph.attrs.graph.attrs.bbox = parse_bbox (subgraph.attrs.graph.attrs.bb);
        subgraph.attrs.graph.attrs.lp   = parse_pt   (subgraph.attrs.graph.attrs.lp);
    }

    return {
        'subgraphs' : subgraphs,
        'nodes'     : nodes,
        'edges'     : edges,
        'attrs'     : attrs,
    };
}

export default {
    append_marker,
    cliques_palette,
    dot,
    generate_css_palette,
    inflate_bbox,
    insert_css_palette,
    labez_palette,
    parse_bbox,
    parse_path,
    parse_path_svg,
    parse_pt,
    key_by,
};
