<template>
  <div class="local-stemma-vm card-slidable">
    <div :class="'wrapper svg-wrapper ' + cssclass"
         @contextmenu.prevent="on_contextmenu" @click="on_click">
      <slot />
    </div>
    <context-menu ref="menu" @menu-click="on_menu_click" />
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
import $       from 'jquery';
import _       from 'lodash';
import tools   from 'tools';
import * as d3 from 'd3';
import context_menu from 'widgets/context_menu.vue';
import { mkmsg }    from 'widgets/context_menu.vue';


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
        const t = d3.transition ().duration (500).ease (d3.easeLinear);
        node.transition (t).attrTween ('transform', function (d, dummy_i, dummy_a)  {
            const delta_x = d.pos.x - d.pos.orig_x;
            const delta_y = d.pos.y - d.pos.orig_y;
            d.pos.x = d.pos.orig_x;
            d.pos.y = d.pos.orig_y;
            return function (tt) {
                const x = d.pos.x + ((1.0 - tt) * delta_x);
                const y = d.pos.y + ((1.0 - tt) * delta_y);
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
    const passage = vm.$store.state.passage;

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
            const dragged_node_ref = dragged_node;
            if (target_node) {
                // if dropped on another node, the default action is to
                // move, but if the shift key was held down, the action will
                // be to merge or to split
                let action = 'move';
                if (d3.event.sourceEvent.ctrlKey) {
                    action = 'add';
                }
                if (d3.event.sourceEvent.shiftKey) {
                    action = (dragged_node.datum ().labez === target_node.datum ().labez)
                        ? 'merge' : 'split';
                }
                const xhr = vm.post ('stemma-edit/' + passage.pass_id, {
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
 * Implements the context menu.
 *
 * The context menu can be used to split the attestation, reassign source
 * nodes or to merge a split.
 *
 * @function build_contextmenu
 *
 * @param {Object} event - The event
 */

function build_contextmenu (event, vm) {
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
    const cliques = _.filter (vm.$store.state.passage.cliques, o => o.labez[0] !== 'z')
          .concat ([
              { 'labez' : '*', 'clique' : '1', 'labez_clique' : '*' },
              { 'labez' : '?', 'clique' : '1', 'labez_clique' : '?' },
          ]);

    const actions = [];

    // Menu Header
    actions.push ({
        'msg'   : mkmsg ('Reading', data.labez_old, data.clique_old),
        'bg'    : data.labez_old,
        'class' : 'disabled',
        'data' : {
            ... data,
            'action'   : '',
            'disabled' : true,
        }
    });

    // Split one clique

    actions.push ({
        'msg'   : mkmsg ('Split', data.labez_old, data.clique_old),
        'bg'    : data.labez_old,
        'class' : '',
        'data' : {
            ... data,
            'action'     : 'split',
            'labez_new'  : '?',
            'clique_new' : '1',
        }
    });

    // Merge two cliques

    _.forEach (cliques, function (c) {
        if ((c.labez === data.labez_old) && (c.clique !== data.clique_old)) {
            actions.push ({
                'msg'   : mkmsg ('Merge into', c.labez, c.clique),
                'bg'    : data.labez_old,
                'class' : '',
                'data'  : {
                    ... data,
                    'action'     : 'merge',
                    'labez_new'  : c.labez,
                    'clique_new' : c.clique,
                },
            });
        }
    });

    // Reassign Source of clique

    _.forEach (cliques, function (c) {
        if (c.labez !== data.labez_old || c.clique !== data.clique_old) {
            actions.push ({
                'msg'   : mkmsg ('Set Source to', c.labez, c.clique),
                'bg'    : c.labez,
                'class' : '',
                'data'  : {
                    ... data,
                    'action'     : 'move',
                    'labez_new'  : c.labez,
                    'clique_new' : c.clique,
                },
            });
        }
    });

    // Add another source

    _.forEach (cliques, function (c) {
        if (c.labez !== data.labez_old || c.clique !== data.clique_old) {
            actions.push ({
                'msg'   : mkmsg ('Add Source', c.labez, c.clique),
                'bg'    : c.labez,
                'class' : '',
                'data'  : {
                    ... data,
                    'action'     : 'add',
                    'labez_new'  : c.labez,
                    'clique_new' : c.clique,
                },
            });
        }
    });

    // Delete a source

    const graph_vm = vm.get_graph_vm ();
    const g = graph_vm.graph;
    _.forEach (g.edges, (edge, i) => {
        const t_labez = g.nodes[edge.elems[1].id].attrs.labez;
        if (t_labez === dataset.labez) {
            const s_attr = g.nodes[edge.elems[0].id].attrs;
            actions.push ({
                'msg'   : mkmsg ('Remove Source', s_attr.labez, s_attr.clique),
                'bg'    : s_attr.labez,
                'class' : '',
                'data'  : {
                    ... data,
                    'action'        : 'del',
                    'source_labez'  : s_attr.labez,
                    'source_clique' : s_attr.clique,
                },
            });
        }
    });

    return _.groupBy (actions, a => a.data.action);
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

        if (vm.$store.getters.can_write) {
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
    'components' : {
        'context-menu' : context_menu,
    },
    'props' : ['toolbar', 'cssclass', 'global', 'var_only'],
    'data'  : function () {
        return {
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
            return this.$children[0];
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
            if (this.$store.getters.can_write) {
                this.$refs.menu.open (build_contextmenu (event, this), event.target);
            }
        },
        on_click (event) {
            // close the menu on outside click
            this.$refs.menu.close ();
        },
        on_menu_click (data, event) {
            const vm = this;

            const xhr2 = vm.post ('stemma-edit/' + vm.passage.pass_id, data);
            xhr2.then (() => {
                $ (window).trigger ('hashchange');
            });
            xhr2.catch ((reason) => {
                tools.xhr_alert (reason, vm.$wrapper);
            });
        },
        download (page) {
            window.open (this.build_full_api_url (this.build_url (page), '_blank'));
        },
    },
    'mounted' : function () {
        this.toolbar.dot = () => this.download ('stemma.dot');
        this.toolbar.png = () => this.download ('stemma.png');
        this.$card    = $ (this.$el).closest ('.card');
        this.$wrapper = $ (this.$el).find ('.wrapper');
        this.load_passage ();
    },
};
</script>


<style lang="scss">
/* local_stemma.vue */
@import "bootstrap-custom";

</style>
