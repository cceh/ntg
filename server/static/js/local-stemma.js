'use strict';

/**
 * This module implements the local stemma drag-and-drop editing.
 *
 * @module local-stemma
 * @author Marcello Perathoner
 */

define(['jquery', 'lodash', 'd3', 'tools'], function ($, _, d3, tools) {
    function changed() {
        // currently unused
        $(document).trigger('changed.ntg.local-stemma');
    }

    /** @var {D3selector} dragged_node - The node being dragged or null */
    var dragged_node = null;
    /** @var {D3selector} target_node  - The node under the node being dragged or null */
    var target_node = null;

    /**
     * Moves the node back to the original position.
     *
     * If the user drops the node 'nowhere' then this function slides the node
     * back to the original position.
     *
     * @see: https://github.com/d3/d3-transition#transition_attrTween
     *
     * @function return_to_base
     *
     * @param {Object} node - The node to slide back.
     */

    function return_to_base(node) {
        if (node !== null) {
            var t = d3.transition().duration(500).ease(d3.easeLinear);
            node.transition(t).attrTween('transform', function (d, dummy_i, dummy_a) {
                var delta_x = d.pos.x - d.pos.orig_x;
                var delta_y = d.pos.y - d.pos.orig_y;
                d.pos.x = d.pos.orig_x;
                d.pos.y = d.pos.orig_y;
                return function (tt) {
                    var x = d.pos.x + (1.0 - tt) * delta_x;
                    var y = d.pos.y + (1.0 - tt) * delta_y;
                    return 'translate(' + x + ',' + y + ')';
                };
            });
        }
    }

    /**
     * Highlight or unhighlight a node
     *
     * @function highlight
     *
     * @param {Object} node - The node to highlight
     * @param {bool} b      - Whether to highlight or unhighlight
     */

    function highlight(node, b) {
        if (node) {
            node.classed('highlight', b);
        }
    }

    /**
     * Drag and drop handler
     *
     * Creates a d3-drag object that implements the drag-and-drop local stemma
     * editor.
     *
     * @function dragListener
     *
     * @param {Object} instance - The instance
     */

    function dragListener(instance) {
        var $panel = instance.$wrapper;
        var passage = instance.passage;

        return d3.drag().on('start', function (dummy_d) {
            // do nothing (yet)
        }).on('drag', function (d) {
            if (dragged_node === null) {
                dragged_node = d3.select(this);
                d.pos.orig_x = d.pos.x;
                d.pos.orig_y = d.pos.y;
                // Suppress the mouseover event on the node being dragged
                // otherwise it will absorb the event and the underlying
                // node will not get it.
                dragged_node.attr('pointer-events', 'none');
                dragged_node.raise();
                target_node = null;
                // console.log ('dragging ' + dragged_node.datum ().label);
            }
            d.pos.x += d3.event.dx;
            d.pos.y += d3.event.dy;
            dragged_node.attr('transform', 'translate(' + d.pos.x + ',' + d.pos.y + ')');
            // console.log (d3.event.shiftKey ? 'shift' : 'unshift');
        }).on('end', function (dummy_d) {
            var dragged_node_ref = dragged_node;
            if (target_node) {
                // if dropped on another node, the default action is to
                // move, but if the shift key was held down, the action will
                // be to merge or to split
                var action = 'move';
                if (d3.event.sourceEvent.shiftKey) {
                    action = dragged_node.datum().labez === target_node.datum().labez ? 'merge' : 'split';
                }
                var xhr = $.getJSON('stemma-edit/' + passage.pass_id, {
                    'action': action,
                    'labez_old': dragged_node.datum().labez,
                    'clique_old': dragged_node.datum().clique,
                    'labez_new': target_node.datum().labez,
                    'clique_new': target_node.datum().clique
                });
                xhr.done(function (json) {
                    // stemma-edit returns the changed passage
                    $(document).trigger('ntg.panel.reload', json.data);
                });
                xhr.fail(function (xhrobj) {
                    tools.xhr_alert(xhrobj, $panel);
                    return_to_base(dragged_node_ref);
                });
                highlight(target_node, false);
            } else {
                // if dropped on no man's land
                return_to_base(dragged_node_ref);
            }
            if (dragged_node !== null) {
                dragged_node.attr('pointer-events', 'auto');
            }
            dragged_node = null;
            target_node = null;
        });
    }

    /**
     * Output one menu item
     *
     * @function trow
     *
     * @param {Object} data - A dictionary
     *
     * @returns {jQuery} The table row object.
     */

    function trow(data) {
        return $(tools.format('<tr data-action="{action}" data-labez_old="{labez_old}" data-clique_old="{clique_old}" ' + 'data-labez_new="{labez_new}" data-clique_new="{clique_new}">' + '<td class="bg_labez" data-labez="{labez_bg}"></td>' + '<td>{msg}</td>' + '</tr>', data));
    }

    /**
     * Implements the context menu.
     *
     * The context menu can be used to split the attestation, reassign source
     * nodes or to merge a split.
     *
     * @function open_contextmenu
     *
     * @param {Object} event - The event
     */

    function open_contextmenu(event) {
        event.preventDefault();

        var passage = event.data.passage;
        var xhr = $.getJSON('cliques.json/' + passage.pass_id);
        xhr.done(function (json) {
            var dataset = event.target.dataset;
            var data = {
                'labez_old': dataset.labez,
                'clique_old': dataset.clique
            };

            // build the context menu
            var menu = $('<table class="contextmenu"></table>');
            menu.append($(tools.format('<tr class="ui-state-disabled">' + '<td class="bg_labez" data-labez="{labez_old}"></td>' + '<td>{labez_old}{clique_old}</td>' + '</tr>', data)));
            menu.append($('<tr><td>-</td><td>-</td></tr>'));

            // Split a clique

            data.action = 'split';
            data.msg = 'Split ' + data.labez_old + data.clique_old;
            data.labez_new = '?';
            data.clique_new = '0';
            data.labez_bg = dataset.labez;
            menu.append(trow(data));
            menu.append($('<tr><td>-</td><td>-</td></tr>'));

            // Merge two cliques

            var cliques = _.filter(json.data, function (o) {
                return o[0][0] !== 'z';
            });
            cliques = cliques.concat([['*', '0', '*'], ['?', '0', '?']]);
            _.forEach(cliques, function (value) {
                data.labez_new = value[0];
                data.clique_new = value[1];
                data.labez_bg = value[0];

                if (data.labez_new === data.labez_old && data.clique_old !== data.clique_new) {
                    data.action = 'merge';
                    data.msg = 'Merge into ' + data.labez_new + data.clique_new;
                    menu.append(trow(data));
                }
            });
            menu.append($('<tr><td>-</td><td>-</td></tr>'));

            // Reassign Source of clique

            _.forEach(cliques, function (value) {
                data.labez_new = value[0];
                data.clique_new = value[1];
                data.labez_bg = value[0];

                if (data.labez_new !== data.labez_old) {
                    data.action = 'move';
                    data.msg = 'Set Source to ' + data.labez_new + data.clique_new;
                    menu.append(trow(data));
                }
            });

            // Display the menu

            menu.menu({
                'select': function select(event2, ui) {
                    var tr = ui.item[0];

                    // console.log ('Selected: ' + $ (tr).text ());

                    var xhr2 = $.getJSON('stemma-edit/' + passage.pass_id, tr.dataset);
                    xhr2.done(function (json2) {
                        // stemma-edit returns the changed passage
                        $(document).trigger('ntg.panel.reload', json2.data);
                    });
                    xhr2.fail(function (xhrobj) {
                        tools.xhr_alert(xhrobj, event.data.$wrapper);
                    });
                    menu.fadeOut(function () {
                        menu.remove();
                    });
                }
            });
            tools.svg_contextmenu(menu, event.target);
        });
    }

    /**
     * Load a new passage.
     *
     * @function load_passage
     *
     * @param {Object} passage - Which passage to load.
     *
     * @return {Promise} Promise, resolved when the new passage has loaded.
     */
    function load_passage(passage) {
        var instance = this;
        instance.passage = passage;

        var params = ['width', 'fontsize'];

        // provide a width and fontsize for GraphViz to format the graph
        instance.data.width = instance.$wrapper.width(); // in px
        instance.data.fontsize = parseFloat(instance.$wrapper.css('font-size')); // in px

        var url = 'stemma.dot/' + passage.pass_id + '?' + $.param(_.pick(instance.data, params));
        var png_url = 'stemma.png/' + passage.pass_id + '?' + $.param(_.pick(instance.data, params));

        var name = $.trim(instance.$panel.find('.panel-caption').text());
        instance.$toolbar.find('a[name="dot"]').attr('href', url).attr('download', name + '.dot');
        instance.$toolbar.find('a[name="png"]').attr('href', png_url);

        var xhr = instance.graph.load_dot(url);
        xhr.done(function () {
            instance.$panel.animate({ 'width': instance.graph.bbox.width + 20 + 'px' });

            if (is_editor) {
                // Drag a node.
                d3.selectAll('div.panel-local-stemma g.node.draggable').call(dragListener(instance));
                d3.selectAll('div.panel-local-stemma g.node.droptarget').on('mouseover', function (dummy_d) {
                    if (dragged_node && d3.select(this) !== dragged_node) {
                        target_node = d3.select(this);
                        highlight(target_node, true);
                    }
                }).on('mouseout', function (dummy_d) {
                    if (dragged_node && d3.select(this) !== dragged_node) {
                        highlight(target_node, false);
                        target_node = null;
                    }
                });
            }
        });
        changed();
        return xhr;
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
    function init(instance, graph_module, id_prefix) {
        instance.load_passage = load_passage;
        $.extend(instance.data, {});
        instance.$wrapper = instance.$panel.find('.panel-content');
        instance.graph = graph_module.init(instance.$wrapper, id_prefix);

        if (is_editor) {
            instance.$panel.on('contextmenu', 'g.node.draggable', instance, open_contextmenu);
        }

        return instance;
    }

    return {
        'init': init
    };
});

//# sourceMappingURL=local-stemma.js.map