<template>
  <div class="vm-local-stemma card-slidable">
    <div class="card-header">
      <toolbar :toolbar="toolbar">
        <button-group slot="right" :options="options.png_dot" />
      </toolbar>
    </div>

    <div class="svg-wrapper" @contextmenu.prevent="on_contextmenu">
      <d3stemma ref="engine" prefix="ls_" />
    </div>

    <context-menu ref="menu" @input="on_menu_input" />
    <alert ref="alert" />
  </div>
</template>

<script>
/**
 * This module implements the local stemma with drag-and-drop editing.
 *
 * @component client/local_stemma
 * @author Marcello Perathoner
 */

import { select, selectAll, event } from 'd3-selection';
import { drag }                     from 'd3-drag';
import { groupBy }                  from 'lodash';

import d3_stemma_layout from 'd3_stemma_layout.vue';
import tools            from 'tools';
import alert            from 'widgets/alert.vue';
import button_group     from 'widgets/button_group.vue';
import context_menu     from 'widgets/context_menu.vue';
import toolbar          from 'widgets/toolbar.vue';
import { mkmsg }        from 'widgets/context_menu.vue';
import { options }      from 'widgets/options';

const SVG_X_BORDER = 40;  // in pixel
const SVG_Y_BORDER = 40;


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
 * @param {D3selector} d3_node - The node to slide back.
 */

function return_to_base (d3_node) {
    if (d3_node !== null) {
        const d = d3_node.datum ();
        const n = d3_node.node ();
        n.velocity ({
            'transform' : [`translate(${d.pos.orig_x},${d.pos.orig_y})`, `translate(${d.pos.x},${d.pos.y})`],
        }, {
            'duration' : 250,
            'easing'   : 'ease-in-out',
        }).then (() => {
            d.pos.x = d.pos.orig_x;
            d.pos.y = d.pos.orig_y;
        });
    }
}

/**
 * Highlight or unhighlight a node
 *
 * @param {Object} node - The node to highlight
 * @param {bool}   b    - Whether to highlight or unhighlight
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
 * @param {Object} vm - The Vue instance
 */

function drag_listener (vm) {
    return drag ()
        .on ('start', function (dummy_d) {
            // do nothing (yet)
        })
        .on ('drag', function (d) {
            if (dragged_node === null) {
                dragged_node = select (this);
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
            d.pos.x += event.dx;
            d.pos.y += event.dy;
            dragged_node.attr ('transform', 'translate(' + d.pos.x + ',' + d.pos.y + ')');
        })
        .on ('end', function (dummy_d) {
            const dragged_node_ref = dragged_node;
            if (target_node) {
                // if dropped on another node, the default action is to
                // move, but if the shift key was held down, the action will
                // be to merge or to split
                let action = 'move';
                if (event.sourceEvent.ctrlKey) {
                    action = 'add';
                }
                if (event.sourceEvent.shiftKey) {
                    action = (dragged_node.datum ().labez === target_node.datum ().labez)
                        ? 'merge' : 'split';
                }
                vm.post ('stemma-edit/' + vm.pass_id, {
                    'action'     : action,
                    'labez_old'  : dragged_node.datum ().labez,
                    'clique_old' : dragged_node.datum ().clique,
                    'labez_new'  : target_node.datum ().labez,
                    'clique_new' : target_node.datum ().clique,
                }).then (() => {
                    vm.$trigger ('epoch');
                }).catch ((error) => {
                    vm.$refs.alert.show (error.response.data.message, 'error');
                    return_to_base (dragged_node_ref);
                });
                highlight (target_node, false);
            } else {
                // if dropped on no mans land
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
 * @param {Object} evt - The event
 * @param {Vue}    vm  - The Vue instance
 */

async function build_contextmenu (evt, vm) {
    const dataset = evt.target.dataset;
    const data = {
        'labez_old'  : dataset.labez,
        'clique_old' : dataset.clique,
    };

    const response = await vm.get ('cliques.json/' + vm.pass_id);

    const cliques = response.data.data.filter (o => o.labez[0] !== 'z')
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
        'data'  : {
            ... data,
            'action'   : '',
            'disabled' : true,
        },
    });

    // Split one clique

    actions.push ({
        'msg'   : mkmsg ('Split', data.labez_old, data.clique_old),
        'bg'    : data.labez_old,
        'class' : '',
        'data'  : {
            ... data,
            'action'     : 'split',
            'labez_new'  : '?',
            'clique_new' : '1',
        },
    });

    // Merge two cliques

    for (const c of cliques) {
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
    }

    // Reassign Source of clique

    for (const c of cliques) {
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
    }

    // Add another source

    for (const c of cliques) {
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
    }

    // Delete a source

    const graph_vm = vm.get_graph_vm ();
    const g = graph_vm.graph;
    for (const edge of g.edges) {
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
    }

    return groupBy (actions, a => a.data.action);
}

/**
 * Load a new passage.
 *
 * @param {Vue}    vm      - The Vue instance
 * @param {Number} pass_id - Which passage to load.
 *
 * @return {Promise} Promise, resolved when the new passage has loaded.
 */
function load_passage (vm, pass_id) {
    if (pass_id === 0) {
        return;
    }

    const graph_vm = vm.get_graph_vm ();
    const wrapper = vm.$el.querySelector ('.svg-wrapper');

    const requests = [
        vm.get ('passage.json/' + vm.pass_id),
        vm.get (vm.build_url ('stemma.dot')),
        tools.fade_out (wrapper).promise,
    ];
    Promise.all (requests).then ((responses) => {
        vm.passage = responses[0].data.data;
        const bbox = graph_vm.load_dot (responses[1].data);
        wrapper
            .velocity ({
                'width'  : (bbox.width  + SVG_X_BORDER),
                'height' : (bbox.height + SVG_Y_BORDER),
            }, tools.velocity_opts)
            .velocity ({
                'opacity' : 1.0,
            }, tools.velocity_opts);

        if (vm.$store.getters.can_write) {
            // Drag a node.
            selectAll ('div.vm-local-stemma g.node.draggable')
                .call (drag_listener (vm));
            selectAll ('div.vm-local-stemma g.node.droptarget')
                .on ('mouseover', function (dummy_d) {
                    if (dragged_node && select (this) !== dragged_node) {
                        target_node = select (this);
                        highlight (target_node, true);
                    }
                })
                .on ('mouseout', function (dummy_d) {
                    if (dragged_node && select (this) !== dragged_node) {
                        highlight (target_node, false);
                        target_node = null;
                    }
                });
        }
    });
}

export default {
    'props'      : ['pass_id', 'epoch', 'global', 'var_only'],
    'components' : {
        'alert'        : alert,
        'button-group' : button_group,
        'context-menu' : context_menu,
        'toolbar'      : toolbar,
        'd3stemma'     : d3_stemma_layout,
    },
    'data' : function () {
        return {
            'passage' : {},
            'options' : options,
            'toolbar' : {
                'dot' : () => { this.download ('stemma.dot'); },
                'png' : () => { this.download ('stemma.png'); },
            },
        };
    },
    'watch' : {
        pass_id () {
            this.load_passage ();
        },
        epoch () {
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
            load_passage (this, this.pass_id);
        },
        get_graph_vm () {
            return this.$refs.engine;
        },
        build_url (page) {
            const vm = this;

            // provide a width and fontsize for GraphViz to format the graph
            const cstyle = getComputedStyle (vm.$el);
            const params = {
                'width'    : parseFloat (cstyle.getPropertyValue ('width')), // in px
                'fontsize' : parseFloat (cstyle.getPropertyValue ('font-size')), // in px
            };
            return `${page}/${vm.pass_id}?` + tools.param (params);
        },
        async on_contextmenu (evt) {
            if (this.$store.getters.can_write) {
                if (evt.target.closest ('.node.draggable')) {
                    this.$refs.menu.open (await build_contextmenu (evt, this), evt.target);
                }
            }
        },
        on_menu_input (data) {
            const vm = this;

            vm.post ('stemma-edit/' + vm.pass_id, data)
                .then (() => {
                    vm.$trigger ('epoch');
                }).catch ((error) => {
                    vm.$refs.alert.show (error.response.data.message, 'error');
                });
        },
        download (page) {
            window.open (this.build_full_api_url (this.build_url (page), '_blank'));
        },
    },
    'mounted' : function () {
        this.load_passage ();
    },
};
</script>


<style lang="scss">
/* local_stemma.vue */
@import "bootstrap-custom";

div.vm-local-stemma {
    marker.link {
        visibility: hidden !important;
    }
}

</style>
