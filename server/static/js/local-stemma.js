/**
 * This module is just a wrapper around d3stemma for symmetry with the textflow
 * module.  Implements the local stemma drag-and-drop editing.
 *
 * @module local-stemma
 * @author Marcello Perathoner
 */

define ([
    'jquery',
    'lodash',
    'd3',
    'navigator',
    'tools',
],

function ($, _, d3, navigator, tools) {
    'use strict';

    function changed () {
        // currently unused
        $ (document).trigger ('changed.ntg.local-stemma');
    }

    /** @var dragged_node {D3.selector} The node being dragged or null */
    var dragged_node = null;
    /** @var target_node {D3.selector}  The node under the node being dragged or null */
    var target_node  = null;

    /**
     * Moves the node back to the original position.
     *
     * If the user drops the node 'nowhere' then this function slides the node
     * back to the original position.
     *
     * @see: https://github.com/d3/d3-transition#transition_attrTween
     *
     * @return A D3 interpolator function.
     */

    function return_to_base () {
        return function (d, i, a)  {
            var delta_x = d.pos.x - d.pos.orig_x;
            var delta_y = d.pos.y - d.pos.orig_y;
            d.pos.x = d.pos.orig_x;
            d.pos.y = d.pos.orig_y;
            return function (t) {
                var x = d.pos.x + (1.0 - t) * delta_x;
                var y = d.pos.y + (1.0 - t) * delta_y;
                return 'translate(' + x + ',' + y + ')';
            };
        };
    }

    function cancel (node) {
        var t = d3.transition ().duration (500).ease (d3.easeLinear);
        node.transition (t).attrTween ('transform', return_to_base ());
    }

    function highlight (node, b) {
        if (node) {
            node.classed ('highlight', b);
        }
    }

    /**
     * @var dragListener
     *
     * Implements the drag-and-drop local stemma editor.
     */

    var dragListener = d3.drag ()
        .on ('start', function (d) {
            // do nothing (yet)
        })
        .on ('drag', function (d) {
            if (dragged_node === null) {
                dragged_node = d3.select (this);
                d.pos.orig_x = d.pos.x;
                d.pos.orig_y = d.pos.y;
                // Suppress the mouseover event on the node being dragged
                // otherwise it will absorb the event and the underlying node
                // will not detect it.
                dragged_node.attr ('pointer-events', 'none');
                dragged_node.raise ();
                target_node = null;
                console.log ('dragging ' + dragged_node.datum ().label);
            }
            d.pos.x += d3.event.dx;
            d.pos.y += d3.event.dy;
            dragged_node.attr ('transform', 'translate(' + d.pos.x + ',' + d.pos.y + ')');
        })
        .on ('end', function (d) {
            var dragged_node_ref = dragged_node;
            if (target_node) {
                // if dropped on another node
                console.log (dragged_node.datum ().label + ' dropped on ' + target_node.datum ().label);
                var xhr = $.getJSON ('stemma-edit/' + navigator.passage.id, {
                    'action' : 'move',
                    'parent' : target_node.datum ().label,
                    'child'  : dragged_node.datum ().label
                });
                xhr.done (function (json) {
                    $ (document).trigger ('ntg.passage.changed', json.data);
                    done = true;
                });
                xhr.fail (function () {
                    cancel (dragged_node_ref);
                });
                highlight (target_node, false);
            } else {
                // if dropped in no man's land or server error
                cancel (dragged_node_ref);
            };
            dragged_node.attr ('pointer-events', 'auto');
            dragged_node = null;
            target_node = null;
        });

    /**
     * Implements the context menu.
     *
     * The context menu can be used to split the attestation, reassign source
     * nodes or to merge a split.
     *
     * @param event
     */

    function open_contextmenu (event) {
		event.preventDefault ();

        var xhr = $.getJSON ('splits.json/' + navigator.passage.id);
        xhr.done (function (json) {
            var splits = _.filter (json.data, function (o) { return o[0][0] != 'z'; } );

            var target_varnew = event.target.dataset.varnew || '';
            var target_labez  = target_varnew[0];

            // build the menu contents
            var menu = $ ('<table class="contextmenu"></table>');
            var item;

            // Split

            item = $ ('<tr data-action="split" data-target-varnew="' + target_varnew + '">' +
                      '<td class="bg_labez" data-labez="' + target_labez + '"></td>' +
                      '<td>Split ' + target_varnew + '</td></tr>');
            item.toggleClass ('ui-state-disabled', target_varnew == '?');
            menu.append (item);

            // Reassign Source or Merge

            item = $ ('<tr><td>-</td><td>-</td></tr>');
            menu.append (item);
            _.forEach (splits.concat ([['*', '*'],['?', '?']]), function (value) {
                var varnew = value[0];
                var labez = varnew[0];
                var msg = 'Set Source of ' + target_varnew + ' to ' + varnew;
                var action = 'move';
                if (target_labez == labez) {
                    msg = 'Merge ' + target_varnew + ' into ' + varnew;
                    action = 'merge';
                }
                if (varnew != target_varnew) {
                    item = $ ('<tr data-varnew="' + varnew + '" data-action="' + action +
                              '" data-target-varnew = "' + target_varnew + '">' +
                              '<td class="bg_labez" data-labez="' + labez + '"></td>' +
                              '<td>' + msg + '</td></tr>');
                }
                menu.append (item);
            });

            // Display the menu

            menu.menu ({
                'select' : function (event, ui) {
                    var tr = ui.item[0];
                    console.log ('Selected: ' + $ (tr).text ());

                    var xhr = $.getJSON ('stemma-edit/' + navigator.passage.id, {
                        'action' : tr.dataset.action,
                        'parent' : tr.dataset.varnew,
                        'child'  : tr.dataset.targetVarnew
                    });
                    menu.fadeOut (function () { menu.remove () });
                    xhr.done (function (json) {
                        $ (document).trigger ('ntg.passage.changed', json.data);
                    });
                },
            });
            tools.svg_contextmenu (menu, event.target);
        });
    }

    /**
     * Load a new passage.
     *
     * @function load_passage
     *
     * @param {Object} passage - Which passage to load.
     */
    function load_passage (passage) {
        var instance = this;

        var params = ['width', 'fontsize'];

        // provide a width and fontsize for GraphViz to format the graph
        instance.data.width = instance.$wrapper.width ();                            // in px
        instance.data.fontsize = parseFloat (instance.$wrapper.css ('font-size'));   // in px

        instance.graph.load_dot (
            'stemma.dot/' + passage.id + '?' + $.param (_.pick (instance.data, params))
        ).done (function () {
            instance.dirty = false;
            instance.$panel.animate ({ 'width' : (instance.graph.bbox.width + 20) + 'px' });

            if (logged_in) {
                // Drag a node.
                d3.selectAll ('div.panel-local-stemma g.node')
                    .call (dragListener)
                    .on ('mouseover', function (d) {
                        if (dragged_node && d3.select (this) != dragged_node) {
                            target_node = d3.select (this);
                            highlight (target_node, true);
                        }
                    })
                    .on ('mouseout', function (d) {
                        if (dragged_node && d3.select (this) != dragged_node) {
                            highlight (target_node, false);
                            target_node = null;
                        }
                    })
                $ ('div.panel-local-stemma g.node').droppable ({
                    drop: function (event, ui) {
                        alert ('dropped: ' + $(this).attr ('data-label') + ' on ' + ui.draggable.attr ('data-label'));
                    }
                });
            }
        });
        changed ();
    }

    /**
     * Initialize the module.
     *
     * @function init
     *
     * @param {Object} instance     - The panel module instance to inherit from.
     * @param {Object} graph_module - The graph module to use.
     * @param {string} id_prefix    - The prefix to use for all generated ids.
     *
     * @returns {Object} - The module instance object.
     */
    function init (instance, graph_module, id_prefix) {
        instance.load_passage = load_passage;
        $.extend (instance.data, {});
        instance.$wrapper = instance.$panel.find ('.panel-content');

        instance.graph = graph_module.init (instance.$wrapper, id_prefix);

        if (logged_in) {
            instance.$panel.on ('contextmenu', 'g.node', instance, open_contextmenu);
        }

        return instance;
    }

    return {
        'init' : init,
    };
});
