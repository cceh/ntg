// This is a RequireJS module.
define (['jquery', 'd3', 'lodash', 'relatives', 'jquery-ui'],

function ($, d3, _, relatives) {
    'use strict';

    var globals = {};

    var force = d3.forceSimulation ().alphaMin (0.01);

    function node_class (d) {
        return 'node group_' + d.group + ' hsnr_' + d.hsnr + ' fg_labez';
    }

    function node_data (d, labez_ord) {
        return labez_ord > 0 ? String.fromCharCode (labez_ord + 96) : 'lac';
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

    function init (wrapper_selector) {
        var width  = $ (wrapper_selector).width ();
        var height = width * 0.5;

        var svg = d3.select (wrapper_selector)
            .append ('svg')
            .attr ('width', width)
            .attr ('height', height);

        var g = svg.append ('g')
            .attr ('transform', 'translate(' + (width / 2) + ',' + (height / 2) + ')');

        var g_links = g.append ('g').attr ('id', 'links');
        var g_nodes = g.append ('g').attr ('id', 'nodes');

        globals.wrapper_selector = wrapper_selector;

        d3.json ('/affinity.json', function (error, json) {
            if (error) {
                throw error;
            }

            globals.links = json.links;

            // Keep A and MT on the horizontal center axis
            var A  = json.nodes[0];
            var MT = json.nodes[1];

            A.fx = -width / 4;
            A.fy = 0;
            MT.fx = width / 4;
            MT.fy = 0;

            force.nodes (json.nodes);
            force
                .force ('link', d3.forceLink (json.links).distance (20).strength (0.1))
                .force ('charge', d3.forceManyBody ().strength (-800))
                .force ('x', d3.forceX (0).strength (0.2))
                .force ('y', d3.forceY (0).strength (0.4));

            var link = g_links.selectAll ('.link')
                .data (json.links)
                .enter ().append ('line')
                .attr ('id', function (d) { return 's' + d.source.id + 't' + d.target.id; })
                .attr ('class', 'link');

            var node = g_nodes.selectAll ('.node')
                .data (json.nodes)
                .enter ().append ('g')
                .attr ('id',         function (d) { return 'n' + d.id; })
                .attr ('data-ms-id', function (d) { return d.id; })
                .attr ('class',      'node')
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

            // relatives.init_bootstrap_popup (node);
            relatives.init_jquery_popup (node);

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
                    A.fy = A.fx = null;
                    MT.fy = MT.fx = null;
                }
            });
        });

        // Content of popup changed.  Redo highlighting.
        $ (document).on ('ntg.popup.changed', function () {
            var sources = relatives.get_ms_ids_from_popups ('source');
            var targets = relatives.get_ms_ids_from_popups ('target');

            $ ('.highlight').removeClass ('highlight');
            $ ('.selected').removeClass ('selected');

            $ ('#nodes g[data-ms-id]')
                .filter (function () {
                    return $ (this).attr ('data-ms-id') in targets;
                })
                .addClass ('highlight');
            $ ('#nodes g[data-ms-id]')
                .filter (function () {
                    return $ (this).attr ('data-ms-id') in sources;
                })
                .addClass ('selected');
        });
    }

    function set_attestation (pass_id) {
        // Change the color of the nodes in the graph to reflect the attestation
        // of a passage.

        d3.json ('/coherence.json/' + pass_id, function (error, json) {
            if (error) {
                throw error;
            }

            d3.selectAll (globals.wrapper_selector + ' circle.node')
                .attr ('data-labez', function (d) {
                    d.labez = _.get (json.attestations, d.id, 1); // set labez on data!
                    return node_data (d, d.labez);
                });
        });
    }

    // return an object that defines this module
    return {
        'init'            : init,
        'set_attestation' : set_attestation,
    };
});
