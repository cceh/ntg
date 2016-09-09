// This is a RequireJS module.
define (['jquery', 'd3', 'lodash', 'relatives', 'jquery-ui'],

function ($, d3, _, relatives) {
    'use strict';

    var globals = {};

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

    /*
    function get_nearest (id) {
        // Return the ids of the 10 nearest nodes

        var ids = [];
        var selected = 0;
        _.forEach (globals.links, function (o) {
            if (id == o.source.id && o.target.labez > 0) {
                ids.push (o.target.id);
                selected++;
                if (selected >= 10)
                    // Exit early.  Works because links are sorted by hsnr, affinity DESC.
                    return false;
            }
        });
        return ids;
    }

    function select_adjacent (source_id, target_ids) {
        // Select source and targets and all links from source to target.
        //
        // Also select assorted related items like table entries.
        //
        // source_id: id of source node
        // target_ids: array of target ids
        // Return a jQuery selection

        var selection = $();
        _.forEach (target_ids, function (target_id) {
            selection = selection.add ($('#n' + target_id));
            selection = selection.add ($('#s' + source_id + 't' + target_id));
            selection = selection.add ($('#attestations .ms[data-ms-id=' + target_id + ']'));
        });
        return selection;
    }

    function on_click (id) {
        // Select / deselect nodes
        $node = $('#n' + id);
        $node.toggleClass ('selected');
        $span = $('#attestations .ms[data-ms-id=' + id + ']');
        $span.toggleClass ('selected');

        $('.highlight').removeClass ('highlight');

        $('g.node.selected').each (function () {
            var id = d3.select (this).datum ().id;
            var ids = get_nearest (id);
            $(this).addClass ('highlight');
            $('#attestations .ms[data-ms-id=' + id + ']').addClass ('highlight');
            select_adjacent (id, ids).addClass ('highlight');
        });
        d3.selectAll ('line.highlight').raise ();
    }
    */

    function init () {
        var width  = $ ('#svg-wrapper').width ();
        var height = width * 0.5;

        var svg = d3.select ('#svg-wrapper')
            .append ('svg')
            .attr ('width', width)
            .attr ('height', height);

        var g = svg.append ('g')
            .attr ('transform', 'translate(' + (width / 2) + ',' + (height / 2) + ')');

        var g_links = g.append ('g').attr ('id', 'links');
        var g_nodes = g.append ('g').attr ('id', 'nodes');

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

            /*
              node.on ('click.highlight', function (d) {
                on_click (d.id);
                d3.event.stopPropagation ();
              });
            */

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

    // return an object that defines this module
    return {
        'init' : init,
    };
});
