/**
 * This module implements the local stemma drag-and-drop editing.
 *
 * @module local-stemma
 * @author Marcello Perathoner
 */

define ([
    'jquery',
    'lodash',
    'd3',
    'd3-common',
    'navigator',
    'tools',
],

function ($, _, d3, d3common, navigator, tools) {
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
        return function (d, i, dummy_a)  {
            var delta_x = d.pos.x - d.pos.orig_x;
            var delta_y = d.pos.y - d.pos.orig_y;
            d.pos.x = d.pos.orig_x;
            d.pos.y = d.pos.orig_y;
            return function (t) {
                var x = d.pos.x + ((1.0 - t) * delta_x);
                var y = d.pos.y + ((1.0 - t) * delta_y);
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
     * @function dragListener
     *
     * Creates a d3-drag object that implements the drag-and-drop local stemma
     * editor.
     */

    function dragListener (panel) {
        return d3.drag ()
            .on ('start', function (dummy_d) {
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
                    // console.log ('dragging ' + dragged_node.datum ().label);
                }
                d.pos.x += d3.event.dx;
                d.pos.y += d3.event.dy;
                dragged_node.attr ('transform', 'translate(' + d.pos.x + ',' + d.pos.y + ')');
            })
            .on ('end', function (dummy_d) {
                var dragged_node_ref = dragged_node;
                if (target_node) {
                    // if dropped on another node
                    // console.log (dragged_node.datum ().label + ' dropped on ' + target_node.datum ().label);
                    var xhr = $.getJSON ('stemma-edit/' + navigator.passage.id, {
                        'action' : 'move',
                        'parent' : target_node.datum ().label,
                        'child'  : dragged_node.datum ().label,
                    });
                    xhr.done (function (json) {
                        $ (document).trigger ('ntg.passage.changed', json.data);
                    });
                    xhr.fail (function (xhrobj) {
                        tools.xhr_alert (xhrobj, panel);
                        cancel (dragged_node_ref);
                    });
                    highlight (target_node, false);
                } else {
                    // if dropped in no man's land
                    cancel (dragged_node_ref);
                }
                dragged_node.attr ('pointer-events', 'auto');
                dragged_node = null;
                target_node = null;
            });
    }

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
            var splits = _.filter (json.data, function (o) { return o[0][0] !== 'z'; });

            // build the menu contents
            var menu = $ ('<table class="contextmenu"></table>');

            var data = {};
            data.target_varnew = event.target.dataset.varnew || '';
            data.target_labez  = data.target_varnew[0];

            // Split

            var $item = $ (tools.format (
                '<tr data-action="split" data-target-varnew="{target_varnew}">' +
                    '<td class="bg_labez" data-labez="{target_labez}"></td>' +
                    '<td>Split {target_varnew}</td>' +
                    '</tr>',
                data
            ));
            $item.toggleClass ('ui-state-disabled', data.target_varnew === '?' || data.target_varnew === '*');
            menu.append ($item);

            // Reassign Source or Merge

            $item = $ ('<tr><td>-</td><td>-</td></tr>');
            menu.append ($item);
            _.forEach (splits.concat ([['*', '*'], ['?', '?']]), function (value) {
                data.varnew = value[0];
                data.labez  = data.varnew[0];
                data.msg = 'Set Source of ' + data.target_varnew + ' to ' + data.varnew;
                data.action = 'move';
                if (data.target_labez === data.labez) {
                    data.msg = 'Merge ' + data.target_varnew + ' into ' + data.varnew;
                    data.action = 'merge';
                }
                if (data.varnew !== data.target_varnew) {
                    menu.append ($ (tools.format (
                        '<tr data-varnew="{varnew}" data-action="{action}" data-target-varnew="{target_varnew}">' +
                            '<td class="bg_labez" data-labez="{labez}"></td>' +
                            '<td>{msg}</td>' +
                            '</tr>',
                        data
                    )));
                }
            });

            // Display the menu

            menu.menu ({
                'select' : function (event2, ui) {
                    var tr = ui.item[0];
                    // console.log ('Selected: ' + $ (tr).text ());

                    var xhr = $.getJSON ('stemma-edit/' + navigator.passage.id, {
                        'action' : tr.dataset.action,
                        'parent' : tr.dataset.varnew,
                        'child'  : tr.dataset.targetVarnew,
                    });
                    xhr.done (function (json) {
                        $ (document).trigger ('ntg.passage.changed', json.data);
                    });
                    xhr.fail (function (xhrobj) {
                        tools.xhr_alert (xhrobj, event.data.$wrapper);
                    });
                    menu.fadeOut (function () { menu.remove (); });
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

        var url = 'stemma.dot/' + passage.id + '?' + $.param (_.pick (instance.data, params));
        var name = $.trim (instance.$panel.find ('.panel-caption').text ());
        instance.$toolbar.find ('a[name="dot"]').attr ('href', url).attr ('download', name + '.dot');

        instance.graph.load_dot (url).done (function () {
            instance.dirty = false;
            instance.$panel.animate ({ 'width' : (instance.graph.bbox.width + 20) + 'px' });

            if (is_editor) {
                // Drag a node.
                d3.selectAll ('div.panel-local-stemma g.node')
                    .call (dragListener (instance.$wrapper))
                    .on ('mouseover', function (dummy_d) {
                        if (dragged_node && d3.select (this) !== dragged_node) {
                            target_node = d3.select (this);
                            highlight (target_node, true);
                        }
                    })
                    .on ('mouseout', function (dummy_d) {
                        if (dragged_node && d3.select (this) !== dragged_node) {
                            highlight (target_node, false);
                            target_node = null;
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

        if (is_editor) {
            instance.$panel.on ('contextmenu', 'g.node', instance, open_contextmenu);
        }

        return instance;
    }

    return {
        'init' : init,
    };
});
