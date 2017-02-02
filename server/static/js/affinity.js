/**
 * This module displays an affinity cloud using the D3 force layout.  It
 * retrieves the data, a sparse affinity matrix, in JSON format.
 *
 * @module affinity
 * @author Marcello Perathoner
 */

define (['jquery', 'd3', 'lodash'],

function ($, d3, _) {
    'use strict';

    var force = d3.forceSimulation ().alphaMin (0.01);

    function node_class (d) {
        return 'node group_' + d.group + ' hsnr_' + d.hsnr + ' fg_labez';
    }

    function dragged (d) {
        d.fx = d3.event.x;
        d.fy = d3.event.y;
    }

    function dragstarted (d) {
        if (!d3.event.active) {
            force.alphaTarget (0.3).restart ();
        }
        dragged (d);
    }

    function dragended (d) {
        if (!d3.event.active) {
            force.alphaTarget (0);
        }
        d.fx = null;
        d.fy = null;
    }

    /**
     * @summary Set the attestation color of the nodes.
     *
     * Change the color of the nodes in the graph to reflect the attestation of
     * a passage.  If the graph topology does not change between passages
     * (currently it does not), we only need to change node colors.
     *
     * @function load_passage
     *
     * @param {Object} passage - Which passage to load.
     */

    function load_passage (passage) {
        var wrapper = d3.select (this.$wrapper.get (0));

        d3.json ('attestation.json/' + passage.id, function (error, json) {
            if (error) {
                throw error;
            }

            wrapper.selectAll ('circle.node')
                .attr ('data-labez', function (d) {
                    d.labez = _.get (json.attestations, d.ms_id, 'a')[0]; // set labez on data!
                    return d.labez;
                });
        });
    }

    /**
     * Highlight nodes in the force graph.
     *
     * @function highlight
     *
     * @param {Array} sources - Ids of the source nodes
     * @param {Array} targets - Ids of the target nodes
     */
    function highlight (sources, targets) {
        $ ('.highlight').removeClass ('highlight');
        $ ('.selected').removeClass ('selected');

        var $nodes = $ ('#' + this.id_prefix + 'nodes g[data-ms-id]');

        $nodes.filter (function () {
            return $ (this).attr ('data-ms-id') in targets;
        }).addClass ('highlight');

        $nodes.filter (function () {
            return $ (this).attr ('data-ms-id') in sources;
        }).addClass ('selected');
    }

    /**
     * Create an SVG graph from a json file.
     *
     * @function load_json
     *
     * @param {url} - The url of the JSON file.
     *
     * @returns {Promise} - A promise resolved when all SVG elements have been created.
     */
    function load_json (url) {
        var instance = this;
        var deferred = new $.Deferred ();

        var width  = instance.$wrapper.width ();
        var height = width * 0.5;

        instance.svg.attr ('width', width).attr ('height', height);

        var g = instance.svg.append ('g')
            .attr ('transform', 'translate(' + (width / 2) + ',' + (height / 2) + ')');

        var g_links = g.append ('g').attr ('id', instance.id_prefix + 'links');
        var g_nodes = g.append ('g').attr ('id', instance.id_prefix + 'nodes');

        d3.json (url, function (error, json) {
            if (error) {
                deferred.reject ();
                return;
            }

            // Fix A and MT on the horizontal center axis
            var A  = json.nodes[0];
            var MT = json.nodes[1];
            A.fx = -width / 4;
            A.fy = 0;
            MT.fx = width / 4;
            MT.fy = 0;

            force.nodes (json.nodes);
            force
                .force ('link', d3.forceLink (json.links).distance (20).strength (0.2))
                .force ('charge', d3.forceManyBody ().strength (-800))
                .force ('x', d3.forceX (0).strength (0.2))
                .force ('y', d3.forceY (0).strength (0.4));

            var link = g_links.selectAll ('.link')
                .data (json.links)
                .enter ().append ('line')
                .attr ('data-id', function (d) { return d.source.id + '-' + d.target.id; })
                .attr ('class', 'link');

            var node = g_nodes.selectAll ('.node')
                .data (json.nodes)
                .enter ().append ('g')
                .attr ('id',         function (d) { return instance.id_prefix + 'n' + d.ms_id; })
                .attr ('data-ms-id', function (d) { return d.ms_id; })
                .attr ('class',   'node')
                .call (d3.drag ()
                       .on ('start', dragstarted)
                       .on ('drag', dragged)
                       .on ('end', dragended));

            node.append ('circle')
                .attr ('r',     function (d) { return d.radius; })
                .attr ('class', function (d) { return node_class (d); });

            node.append ('text')
                .attr ('class', 'node')
                .text (function (d) { return d.hs; });

            force.on ('tick', function () {
                link
                    .attr ('x1', function (d) { return d.source.x; })
                    .attr ('y1', function (d) { return d.source.y; })
                    .attr ('x2', function (d) { return d.target.x; })
                    .attr ('y2', function (d) { return d.target.y; });
                node.attr ('transform',
                           function (d) { return 'translate(' + d.x + ',' + d.y + ')'; });

                // Turn on collision detection when simulation is quite cool
                if (force.alpha () < 0.1 && !force.force ('collide')) {
                    force.force ('collide', d3.forceCollide (16));
                    // Release A and MT nodes.
                    A.fy = A.fx = null;
                    MT.fy = MT.fx = null;
                }
            });
            deferred.resolve ();
        });
        return deferred.promise ();
    }

    /**
     * Initialize the module.
     *
     * @function init
     *
     * @param {Object} instance  - The panel instance to inherit from.
     *
     * @param {string} id_prefix - The prefix to use for all generated ids.
     *
     * @returns {Graph} - The graph object.
     */
    function init (instance, id_prefix) {
        var $wrapper = instance.$panel.find ('.panel-content');
        var svg = d3.select ($wrapper.get (0)).append ('svg');

        instance.$wrapper     = $wrapper;
        instance.svg          = svg;
        instance.id_prefix    = id_prefix;
        instance.load_json    = load_json;
        instance.load_passage = load_passage;
        instance.highlight    = highlight;
        instance.data         = {};

        return instance;
    }

    return /** @alias module:affinity */ {
        'init' : init,
    };
});
