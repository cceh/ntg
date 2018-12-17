<template>
  <div class="local-stemma-vm card-slidable">
    <div class="card-header">
      <toolbar :toolbar="toolbar" />
    </div>

    <div :class="'wrapper svg-wrapper ' + cssclass"
         @contextmenu.prevent="on_contextmenu">
      <slot />
    </div>
  </div>
</template>

<script>
/**
 * This module implements the local stemma with drag-and-drop editing.
 *
 * @component local_stemma
 * @author Marcello Perathoner
 */

import { mapGetters } from 'vuex';
import $ from 'jquery';
import _ from 'lodash';
import tools from 'tools';
import * as d3 from 'd3';

/** @var {D3selector} dragged_node - The node being dragged or null */
let dragged_node = null;
/** @var {D3selector} target_node  - The node under the node being dragged or null */
let target_node  = null;

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

function return_to_base (node) {
    if (node !== null) {
        let t = d3.transition ().duration (500).ease (d3.easeLinear);
        node.transition (t).attrTween ('transform', function (d, dummy_i, dummy_a)  {
            let delta_x = d.pos.x - d.pos.orig_x;
            let delta_y = d.pos.y - d.pos.orig_y;
            d.pos.x = d.pos.orig_x;
            d.pos.y = d.pos.orig_y;
            return function (tt) {
                let x = d.pos.x + ((1.0 - tt) * delta_x);
                let y = d.pos.y + ((1.0 - tt) * delta_y);
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

function highlight (node, b) {
    if (node) {
        node.classed ('highlight', b);
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
 * @param {Object} vm - The Vue instance
 */

function dragListener (vm) {
    let passage = vm.$store.state.passage;

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
                // otherwise it will absorb the event and the underlying
                // node will not get it.
                dragged_node.attr ('pointer-events', 'none');
                dragged_node.raise ();
                target_node = null;
                // console.log ('dragging ' + dragged_node.datum ().label);
            }
            d.pos.x += d3.event.dx;
            d.pos.y += d3.event.dy;
            dragged_node.attr ('transform', 'translate(' + d.pos.x + ',' + d.pos.y + ')');
            // console.log (d3.event.shiftKey ? 'shift' : 'unshift');
        })
        .on ('end', function (dummy_d) {
            let dragged_node_ref = dragged_node;
            if (target_node) {
                // if dropped on another node, the default action is to
                // move, but if the shift key was held down, the action will
                // be to merge or to split
                let action = 'move';
                if (d3.event.sourceEvent.shiftKey) {
                    action = (dragged_node.datum ().labez === target_node.datum ().labez)
                        ? 'merge' : 'split';
                }
                let xhr = vm.post ('stemma-edit/' + passage.pass_id, {
                    'action'     : action,
                    'labez_old'  : dragged_node.datum ().labez,
                    'clique_old' : dragged_node.datum ().clique,
                    'labez_new'  : target_node.datum ().labez,
                    'clique_new' : target_node.datum ().clique,
                });
                xhr.then (() => {
                    $ (window).trigger ('hashchange');
                });
                xhr.catch ((reason) => {
                    tools.xhr_alert (reason, vm.$wrapper);
                    return_to_base (dragged_node_ref);
                });
                highlight (target_node, false);
            } else {
                // if dropped on no man's land
                return_to_base (dragged_node_ref);
            }
            if (dragged_node !== null) {
                dragged_node.attr ('pointer-events', 'auto');
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

function trow (data) {
    return $ (tools.format (
        '<tr data-action="{action}" data-labez_old="{labez_old}" data-clique_old="{clique_old}" '
            + 'data-labez_new="{labez_new}" data-clique_new="{clique_new}">'
            + '<td class="bg_labez" data-labez="{labez_bg}"></td>'
            + '<td>{msg}</td>'
            + '</tr>',
        data
    ));
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

function open_contextmenu (event, vm) {
    const $target = $ (event.target);
    if ($target.closest ('.node.draggable').length === 0) {
        return;
    }

    const passage = vm.passage;
    const dataset = event.target.dataset;
    const data = {
        'labez_old'  : dataset.labez,
        'clique_old' : dataset.clique,
    };

    // build the context menu
    let menu = $ ('<table class="contextmenu"></table>');
    menu.append ($ (tools.format (
        '<tr class="ui-state-disabled">'
            + '<td class="bg_labez" data-labez="{labez_old}"></td>'
            + '<td>{labez_old}{clique_old}</td>'
            + '</tr>',
        data
    )));
    menu.append ($ ('<tr><td>-</td><td>-</td></tr>'));

    // Split a clique

    data.action = 'split';
    data.msg = 'Split ' + data.labez_old + data.clique_old;
    data.labez_new  = '?';
    data.clique_new = '0';
    data.labez_bg   = dataset.labez;
    menu.append (trow (data));
    menu.append ($ ('<tr><td>-</td><td>-</td></tr>'));

    // Merge two cliques

    let cliques = _.filter (vm.$store.state.passage.cliques, function (o) { return o.labez[0] !== 'z'; });
    cliques = cliques.concat ([
        { 'labez' : '*', 'clique' : '0', 'labez_clique' : '*' },
        { 'labez' : '?', 'clique' : '0', 'labez_clique' : '?' },
    ]);
    _.forEach (cliques, function (value) {
        data.labez_new  = value.labez;
        data.clique_new = value.clique;
        data.labez_bg   = value.labez;

        if ((data.labez_new === data.labez_old) && (data.clique_old !== data.clique_new)) {
            data.action = 'merge';
            data.msg    = 'Merge into ' + data.labez_new + data.clique_new;
            menu.append (trow (data));
        }
    });
    menu.append ($ ('<tr><td>-</td><td>-</td></tr>'));

    // Reassign Source of clique

    _.forEach (cliques, function (value) {
        data.labez_new  = value.labez;
        data.clique_new = value.clique;
        data.labez_bg   = value.labez;

        if (data.labez_new !== data.labez_old) {
            data.action = 'move';
            data.msg    = 'Set Source to ' + data.labez_new + data.clique_new;
            menu.append (trow (data));
        }
    });

    // Display the menu

    menu.menu ({
        'select' : function (event2, ui) {
            let tr = ui.item[0];

            // console.log ('Selected: ' + $ (tr).text ());

            let xhr2 = vm.post ('stemma-edit/' + passage.pass_id, tr.dataset);
            xhr2.then (() => {
                $ (window).trigger ('hashchange');
            });
            xhr2.catch ((reason) => {
                tools.xhr_alert (reason, event.data.$wrapper);
            });
            menu.fadeOut (function () { menu.remove (); });
        },
    });
    tools.svg_contextmenu (menu, event.target);
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
function load_passage (vm, passage) {
    if (passage.pass_id === 0) {
        return Promise.resolve ();
    }

    const graph_vm = vm.get_graph_vm ();
    const p1 = graph_vm.load_dot (vm.build_url ('stemma.dot'));
    p1.then (() => {
        vm.$card.animate ({ 'width' : (graph_vm.bbox.width + 20) + 'px' });

        if (vm.$store.state.current_user.is_editor) {
            // Drag a node.
            d3.selectAll ('div.local-stemma-vm g.node.draggable')
                .call (dragListener (vm));
            d3.selectAll ('div.local-stemma-vm g.node.droptarget')
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
    return p1;
}

export default {
    'props' : ['cssclass', 'global', 'var_only'],
    'data'  : function () {
        return {
            'toolbar' : {
                'dot' : () => this.download ('stemma.dot'), // show a download dot button
                'png' : () => this.download ('stemma.png'), // show a download png button
            },
        };
    },
    'computed' : {
        ...mapGetters ([
            'passage',
        ]),
    },
    'watch' : {
        passage () {
            this.load_passage ();
        },
        'toolbar' : {
            handler () {
                this.load_passage ();
            },
            'deep' : true,
        },
    },
    'methods' : {
        load_passage () {
            return load_passage (this, this.passage);
        },
        get_graph_vm () {
            return this.$children[1];
        },
        build_url (page) {
            const vm = this;

            // provide a width and fontsize for GraphViz to format the graph
            const data = {};
            data.width = vm.$wrapper.width ();                            // in px
            data.fontsize = parseFloat (vm.$wrapper.css ('font-size'));   // in px

            return page + '/' + vm.passage.pass_id + '?' + $.param (data);
        },
        on_contextmenu (event) {
            open_contextmenu (event, this);
        },
        download (page) {
            window.open (this.build_full_api_url (this.build_url (page), '_blank'));
        },
    },
    'mounted' : function () {
        this.$card    = $ (this.$el).closest ('.card');
        this.$wrapper = $ (this.$el).find ('.wrapper');
        this.load_passage ();
    },
};
</script>
