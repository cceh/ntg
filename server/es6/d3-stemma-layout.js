/**
 * This module converts a graph in .dot format into SVG.  The .dot file must be
 * pre-processed in order to contain coordinates for each node and bezier paths
 * for each edge.
 *
 * @module d3-stemma-layout
 * @author Marcello Perathoner
 */

define ([
    'jquery',
    'd3',
    'd3-common',
    'lodash',
],

function ($, d3, d3_common, _) {
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
        let instance = this; // instance
        // let dot_dpi = 72;
        let css_dpi = 96;

        let svg = instance.svg;
        svg.selectAll ('g').transition ().duration (300).style ('opacity', 0.0)
            .remove ();
        let deferred = new $.Deferred ();

        d3_common.dot (url, (graph) => {
            // if we have subgraphs, retrieve their nodes too
            _.forEach (graph.subgraphs, (subgraph) => {
                let subgraph_nodes = _.keyBy (_.filter (subgraph.stmts,
                    o => o.type === 'node'), 'id');
                _.assign (graph.nodes, subgraph_nodes); // copy
                subgraph.attrs = _.keyBy (_.filter (subgraph.stmts,
                    o => o.type === 'attr'), 'attrType');
                subgraph.attrs.graph.attrs.bbox = d3_common.parse_bbox (subgraph.attrs.graph.attrs.bb);
                subgraph.attrs.graph.attrs.lp   = d3_common.parse_pt   (subgraph.attrs.graph.attrs.lp);
            });

            // shrinkwrap + accomodate for the thick borders of circles
            instance.bbox = d3_common.inflate_bbox (graph.attrs.graph.attrs.bbox, 3);

            instance.edges = graph.edges;

            let node_width  = graph.attrs.node.attrs.width;     // in inches
            let node_height = graph.attrs.node.attrs.height;    // in inches
            let font_size   = graph.attrs.graph.attrs.fontsize; // in points

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
            _.forEach (graph.nodes, (v, k) => { v.attrs.id = k; });

            // give all links an id
            _.forEach (graph.edges, (link, i) => {
                link.id = instance.id_prefix + 'link_' + i;
            });

            let g = svg.append ('g')
                // shift a little bit to avoid 'shaving' nodes at the view boundary
                .attr ('transform', 'translate(' + -instance.bbox.x + ',' + -instance.bbox.y + ')');

            // draw the subgraphs: a rectangle with a label

            let sg = g.append ('g')
                .attr ('class', 'subgraphs');

            let subgraph = sg.selectAll ('.subgraph')
                .data (_.map (graph.subgraphs, 'attrs.graph.attrs'))
                .enter ();

            subgraph.append ('rect')
                .attr ('x',      d => d.bbox.x)
                .attr ('y',      d => d.bbox.y)
                .attr ('width',  d => d.bbox.width)
                .attr ('height', d => d.bbox.height)
                .attr ('class',  d => 'subgraph' + (/rounded/.test (d.style) ? ' rounded' : ''));

            subgraph.append ('text')
                .attr ('class', 'subgraph')
                // lp indicates the center of the label
                .attr ('x', d => d.lp.x)
                .attr ('y', d => d.lp.y)
                .style ('font-size', d => (d.fontsize || font_size) + 'pt')
                .text (d => d.label);

            // draw the links: a path and a text

            let lg = g.append ('g').attr ('class', 'links');

            let link = lg.selectAll ('.link')
                .data (graph.edges)
                .enter ();

            link.filter (d => d.attrs && d.attrs.head_lp)
                .each ((d) => {
                    d.attrs.head_lp = d3_common.parse_pt (d.attrs.head_lp);
                });

            link.append ('path')
                .attr ('id', d => d.id)
                .attr ('data-labez', d => graph.nodes[d.elems[0].id].attrs.labez)
                .attr ('class', d => {
                    return 'link fg_labez ' +
                        instance.id_prefix + 'sid-' + d.elems[0].id + ' ' +
                        instance.id_prefix + 'tid-' + d.elems[1].id +
                        (/dashed/.test (d.attrs.style) ? ' dashed' : '');
                })
                .attr ('marker-end', 'url(#' + instance.id_prefix + 'triangle)')
                .attr ('d', d => d3_common.parse_path_svg (d.attrs.pos));

            link.filter (d => d.attrs && d.attrs.head_lp && d.attrs.headlabel)
                .append ('text')
                .attr ('data-labez', d => graph.nodes[d.elems[0].id].attrs.labez)
                .attr ('class', (d) => {
                    return 'link bg_labez ' +
                        instance.id_prefix + 'sid-' + d.elems[0].id + ' ' +
                        instance.id_prefix + 'tid-' + d.elems[1].id;
                })
                .attr ('x', d => d.attrs.head_lp.x)
                .attr ('y', d => d.attrs.head_lp.y)
                .text (d => d.attrs.headlabel);

            // draw the nodes: a circle and a text in a group

            let ng = g.append ('g').attr ('class', 'nodes');

            let node = ng.selectAll ('g.node')
                .data (_.map (graph.nodes, 'attrs'))
                .enter ();

            node.filter (d => d.pos)
                .each (d => { d.pos = d3_common.parse_pt (d.pos); });

            let groups = node.append ('g')
                .attr ('data-ms-id',     d => d.ms_id)
                .attr ('data-label',     d => d.label ? d.label : d.id)
                .attr ('class', d => {
                    return 'node node-'
                        + (d.children   ? 'internal' : 'leaf')
                        + (d.clickable  ? ' clickable' : '')
                        + (d.draggable  ? ' draggable' : '')
                        + (d.droptarget ? ' droptarget' : '');
                })
                .attr ('transform', d => 'translate(' + d.pos.x + ',' + d.pos.y + ')');

            let valid = new RegExp ('^[-_A-Za-z0-9]+$');

            groups.append ('ellipse')
                .attr ('class', 'node fg_labez bg_clique')
                .attr ('data-labez',        d => d.labez)
                .attr ('data-clique',       d => d.clique)
                .attr ('data-labez-clique', d => d.labez_clique)
                .attr ('rx', d => (d.width  || node_width)  * css_dpi / 2)
                .attr ('ry', d => (d.height || node_height) * css_dpi / 2)
                .on ('mouseenter', (d) => {
                    if (valid.test (d.id)) {
                        d3.selectAll ('.link.' + instance.id_prefix + 'sid-' + d.id).classed ('hover hi-source', true);
                        d3.selectAll ('.link.' + instance.id_prefix + 'tid-' + d.id).classed ('hover hi-target', true);
                    }
                })
                .on ('mouseleave', (d) => {
                    if (valid.test (d.id)) {
                        d3.selectAll ('.link.' + instance.id_prefix + 'sid-' + d.id).classed ('hover hi-source', false);
                        d3.selectAll ('.link.' + instance.id_prefix + 'tid-' + d.id).classed ('hover hi-target', false);
                    }
                });

            groups.append ('text')
                .attr ('class', 'node')
                .text (d => d.label ? d.label : d.id);

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
        let svg = d3.select ($wrapper.get (0)).append ('svg');

        d3_common.append_marker (svg, id_prefix);

        return {
            'id_prefix' : id_prefix,
            'wrapper'   : $wrapper,
            'svg'       : svg,
            'load_dot'  : load_dot,
            'bbox'      : null,
        };
    }

    return {
        'init' : init,
    };
});
