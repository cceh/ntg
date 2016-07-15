// This is a RequireJS module.
define (['jquery', 'd3', 'lodash', 'jquery-ui'], function ($, d3, _) {

    var globals = {};

    var attestation_color = d3.scaleOrdinal ()
        .domain (d3.range(20))
        .range (['#cccccc', '#1f77b4', '#2ca02c', '#d62728', '#e7ba52', '#ff7f0e', '#9467bd', '#8c564b',
                 '#e377c2', '#17becf', '#aec7e8', '#ffbb78', '#98df8a', '#ff9896', '#c5b0d5', '#c49c94',
                 '#f7b6d2', '#dbdb8d', '#9edae5', '#7f7f7f']);

    function generate_attestation_colors_css (d3_scale) {
        var style = _.map (_.zip (d3_scale.domain (), d3_scale.range ()), function (pair) {
            return '.labez.labez_' + (pair[0] > 0 ? String.fromCharCode (pair[0] + 96) : 'lac') +
                ' { color: ' + pair[1] + ' !important; fill: ' + pair[1] + '; }';
        });
        return style.join ('\n');
    }

    // For D3 and jQuery Interoperability see:
    //   http://collaboradev.com/2014/03/18/d3-and-jquery-interoperability/

    function to_jquery (d3_selection) {
        return $(d3_selection.nodes ());
    }

    function to_d3 (jquery_selection) {
        return d3.selectAll (jquery_selection.toArray ());
    }

    function node_class (d, labez_ord) {
        return 'node group_' + d.group + ' hsnr_' + d.hsnr + ' ' + 'labez labez_' +
            (labez_ord > 0 ? String.fromCharCode (labez_ord + 96) : 'lac');
    }

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
            selection = selection.add ($('#attestations .ms[data-id=' + target_id + ']'));
        });
        return selection;
    }

    function on_click (id) {
        // Select / deselect nodes
        $node = $('#n' + id);
        $node.toggleClass ('selected');
        $span = $('#attestations .ms[data-id=' + id + ']');
        $span.toggleClass ('selected');

        $('.highlight').removeClass ('highlight');

        $('g.node.selected').each (function () {
            var id = d3.select (this).datum ().id;
            var ids = get_nearest (id);
            $(this).addClass ('highlight');
            $('#attestations .ms[data-id=' + id + ']').addClass ('highlight');
            select_adjacent (id, ids).addClass ('highlight');
        });
        d3.selectAll ('line.highlight').raise ();
    }

    $.widget ("custom.d3_tooltip", $.ui.tooltip, {
        _create: function () {
            this._super ();
            this._off (this.element, "mouseover focusin");
        },
        _open: function (event, target, content) {
            this._superApply (arguments);
            this._off (target, "mouseleave focusout");

            // Reposition the popup manually because jquery doesn't grok the SVG
            // DOM.
            var rect = target.get (0).getBoundingClientRect ();
            var bodyRect = document.body.getBoundingClientRect (); // account for scrolling
            var tooltipData = this._find (target);
		    var $tooltip = tooltipData.tooltip;
            event = $.Event ("click");
            event.pageY = rect.top - bodyRect.top;
            event.pageX = rect.left - bodyRect.left + rect.width / 2.0;
            $tooltip.position ({
                my: "center bottom-3",
                collision: "flipfit flip",
                of: event
            });

            $tooltip.draggable ();
        }
    });

    function init_jquery_popup (node) {
        // Implement node popups with jquery-ui.
        //
        node.on ('click.jquery_ui', function (d) {
            var $this = $(this);
            if (!$this.attr ('aria-describedby')) {
                $this.d3_tooltip ({
                    items: 'g.node',
                    classes: { 'ui-tooltip' : 'tooltip-relatives' },
                    position: {
                        my: "center bottom-3"
                    },
                    content: function (callback) {
                        var hsnr = to_d3 ($(this)).datum ().hsnr;
                        $.get ('/relatives/' + globals.pass_id + '/' + hsnr, function (data) {
                            callback (data);
                        });
                    }
                });
                $this.d3_tooltip ("open");
            } else {
                $this.d3_tooltip ("close");
            }
        });
    }

    function close_jquery_popups () {
        $('g.node[aria-describedby]').d3_tooltip ("close");
    }

    function popup_to_elem ($popup) {
        var id = $popup.attr ('id');
        return $('[aria-describedby=' + id + ']');
    }

    function init_bootstrap_popup (node) {
        // Implement node popups with bootstrap.
        //
        // We have to manage popups manually because bootstrap makes it
        // impossible to have the popup content loaded by XHR.  The 'content'
        // function is unusable because it requires a synchronous call to XHR in
        // the main thread.  The same holds for 'show.bs.popover' event, because
        // if we do XHR asynchronously in it, we will not manage to set the new
        // content before the popup is already displayed, producing a 'flash of
        // old content'.  (Error message: XMLHttpRequest on the main thread is
        // deprecated because of its detrimental effects to the end user's
        // experience. For more help, check https://xhr.spec.whatwg.org/.)  The
        // only solution found so far is to manage the popup manually
        // ourselves. jquery-ui handles XHR easily.
        //
        // N.B. Also needs a patch in Tooltip.prototype.getPosition to make
        // bootstrap grok the SVG DOM.

        node.on ('click.bootstrap', function (d) {
            var $this = $(this);
            if (!$this.data ('bs.popover')) {
                $.get ('/relatives/' + globals.pass_id + '/' + d.hsnr, function (data) {
                    var $data = $(data);
                    $('body').on ('inserted.bs.popover', function (e) {
                        $(e.target).data ('bs.popover').$tip.draggable ();
                    });
                    $this.popover ({
                        trigger: 'manual',
                        title: $("div.panel-heading", $data).html (),
                        content: $("table.relatives", $data)[0].outerHTML,
                        container: 'body',
                        html: true,
                        placement: 'auto top',
                        template: '<div class="popover popover-relatives" role="tooltip"><div class="arrow"></div><h3 class="popover-title"></h3><div class="popover-content"></div></div>'
                    }).popover ('show');
                });
            } else {
                $this.popover ('destroy');
            }
        });
    }

    function close_bootstrap_popups () {
        $('g.node').filter (function () {
            return $(this).data ('bs.popover');
        }).popover ('destroy');
    }

    var force = d3.forceSimulation ().alphaMin (0.01);

    function init () {

        var width  = $('#svg-wrapper').width ();
        var height = width * 0.5;

        var last_x, last_y, last_mousemove;

        var svg = d3.select ('#svg-wrapper')
            .append ('svg')
            .attr ('width', width)
            .attr ('height', height);

        var g = svg.append ('g')
            .attr ('transform', 'translate(' + width / 2 + ',' + height / 2 + ')');

        var g_links = g.append ('g').attr ('id', 'links');
        var g_nodes = g.append ('g').attr ('id', 'nodes');

        d3.json ('/affinity.json', function (error, json) {
            if (error) throw error;

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
                .enter().append('line')
                .attr ('id', function (d) { return 's' + d.source.id + 't' + d.target.id; })
                .attr ('class', 'link');

            var node = g_nodes.selectAll ('.node')
                .data(json.nodes)
                .enter().append('g')
                .attr ('id',      function (d) { return 'n' + d.id; })
                .attr ('data-id', function (d) { return d.id; })
                .attr ('class', 'node')
                .call (d3.drag ()
                       .on ('start', dragstarted)
                       .on ('drag', dragged)
                       .on ('end', dragended));

            node.append ('circle')
                .attr ('r',     function(d) { return d.radius; })
                .attr ('class', function (d) { return node_class (d, 0); });

            node.append ('text')
                .attr ('class', 'node')
                .text (function (d) { return d.hs; });

            node.on ('click.highlight', function (d) {
                on_click (d.id);
                d3.event.stopPropagation ();
            });

            // init_bootstrap_popup (node);
            init_jquery_popup (node);

            force.on ('tick', function (e) {
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

        var css = generate_attestation_colors_css (attestation_color);
        $('<style type="text/css">' + css + '</style>').appendTo ('head');

        // clicks

        // click anywhere
        $(document).on ('click', function () {
            $('.highlight').removeClass ('highlight selected');
            // close_bootstrap_popups ();
            close_jquery_popups ();
        });
        // click on close icon in jquery-ui popup
        $(document).on ('click', '.ui-tooltip .close' , function (event) {
            $popup = $(this).parents ('.ui-tooltip');
            popup_to_elem ($popup).d3_tooltip ('close');
            event.stopPropagation ();
        });
        // click on close icon in bootstrap popup
        $(document).on ('click', '.popover .close' , function (event) {
            $popup = $(this).parents ('.popover');
            popup_to_elem ($popup).popover ('destroy');
            event.stopPropagation ();
        });
        // click on ms in list of labez
        $(document).on ('click', '#attestations .ms[data-id]', function (event) {
            on_click ($(this).attr ('data-id'));
            event.stopPropagation ();
        });
    }

    function dragstarted (d) {
        if (!d3.event.active)
            force.alphaTarget (0.3).restart ();
        dragged (d);
    }

    function dragged (d) {
        d.fx = d3.event.x;
        d.fy = d3.event.y;
    }

    function dragended (d) {
        if (!d3.event.active)
            force.alphaTarget (0);
        d.fx = null;
        d.fy = null;
    }

    function set_attestation (pass_id) {
        // Change the color of the nodes in the graph to reflect the attestation
        // of a passage.  Also change the color of the items in the attestation
        // list which functions as legend.

        globals.pass_id = pass_id;

        d3.json ('/coherence/attestation.json/' + pass_id, function (error, json) {
            if (error) throw error;

            var circles = d3.selectAll ('#svg-wrapper circle.node')
                .attr ("class", function (d) {
                    d.labez = _.get (json.attestations, d.id, 1); // set labez on data!
                    return node_class (d, d.labez);
                });
        });
    }

    // return an object that defines this module
    return {
        init: init,
        set_attestation : set_attestation
    };
});
