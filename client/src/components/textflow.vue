<template>
  <div class="vm-textflow card-slidable">
    <div class="card-header">
      <toolbar :toolbar="toolbar">
        <labezator v-if="'labez' in toolbar"
                   v-model="toolbar.labez"
                   :pass_id="pass_id" v-bind="options.labez">
          Variant:
        </labezator>
        <button-group v-if="'cliques' in toolbar"
                      v-model="toolbar.cliques"
                      type="checkbox" :options="options.cliques" />
        <connectivity v-if="'connectivity' in toolbar"
                      v-model="toolbar.connectivity">
          Conn:
        </connectivity>
        <range v-if="'rg_id' in toolbar"
               v-model="toolbar.rg_id"
               :pass_id="pass_id">
          Chapter:
        </range>
        <button-group v-if="'include' in toolbar"
                      v-model="toolbar.include"
                      type="checkbox" :options="options.include" />
        <button-group v-if="'fragments' in toolbar"
                      v-model="toolbar.fragments"
                      type="checkbox" :options="options.fragments" />
        <button-group v-if="'mode' in toolbar"
                      v-model="toolbar.mode"
                      type="radio" :options="options.mode" />
        <labezator v-if="'hyp_a' in toolbar"
                   v-model="toolbar.hyp_a"
                   :pass_id="pass_id" v-bind="options.hyp_a">
          A =
        </labezator>
        <button-group v-if="'checks' in toolbar"
                      v-model="toolbar.checks"
                      type="checkbox" :options="options.checks" />
        <button-group slot="right" v-if="'png' in toolbar" :options="options.png_dot" />
      </toolbar>
    </div>

    <div class="svg-wrapper" @contextmenu.prevent="on_contextmenu">
      <d3chord v-if="chord" ref="engine" :prefix="prefix" />
      <d3stemma v-else="" ref="engine" :prefix="prefix" />
    </div>

    <context-menu ref="menu" @input="on_menu_input" />
    <alert ref="alert" />
  </div>
</template>

<script>
/**
 * This module displays a textflow diagram.  A textflow diagram is a directed
 * acyclic graph that shows the relationship between all manuscripts that offer
 * one reading at one passage.  It can be used to deduce where a reading
 * originated.
 *
 * @component client/textflow
 * @author Marcello Perathoner
 */

import { groupBy, pick } from 'lodash';

import tools            from 'tools';
import d3_stemma_layout from 'd3_stemma_layout.vue';
import d3_chord_layout  from 'd3_chord_layout.vue';
import alert            from 'widgets/alert.vue';
import button_group     from 'widgets/button_group.vue';
import card_caption     from 'widgets/card_caption.vue';
import context_menu     from 'widgets/context_menu.vue';
import toolbar          from 'widgets/toolbar.vue';
import { mkmsg }        from 'widgets/context_menu.vue';
import { options }      from 'widgets/options';

const SVG_X_BORDER = 40;  // in pixel
const SVG_Y_BORDER = 40;


/**
 * Open a context menu when right clicked on a node.
 *
 * The context menu can be used to reassign the node to a different clique.
 *
 * @param {Object} event - The event
 * @param {Object} vm    - The Vue instance
 */

async function build_contextmenu (event, vm) {
    const msid    = event.target.parentNode.dataset.msId;
    const dataset = event.target.dataset;
    const data = {
        'labez_old'  : dataset.labez,
        'clique_old' : dataset.clique,
        'ms_ids'     : tools.bfs (vm.get_graph_vm ().graph.edges, msid),
    };

    const response = await vm.get ('cliques.json/' + vm.pass_id);

    const cliques = response.data.data.filter (o => o.labez[0] !== 'z');
    const actions = [];

    // Menu Header
    actions.push ({
        'msg'   : mkmsg ('Clique', data.labez_old, data.clique_old),
        'bg'    : data.labez_old,
        'class' : 'disabled',
        'data'  : {
            ... data,
            'action'   : '',
            'disabled' : true,
        },
    });

    // cliques
    for (const c of cliques) {
        if ((c.labez === data.labez_old) && (c.clique !== data.clique_old)) {
            actions.push ({
                'msg'   : mkmsg ('Move subtree to', c.labez, c.clique),
                'bg'    : data.labez_old,
                'class' : '',
                'data'  : {
                    ... data,
                    'action'     : 'move-manuscripts',
                    'labez_new'  : c.labez,
                    'clique_new' : c.clique,
                },
            });
        }
    }

    return groupBy (actions, a => a.data.action);
}


/**
 * @vue-prop {bool}   global   - Display global textual flow
 * @vue-prop {bool}   var_only - Display only nodes and links between different readings.
 *
 * Flags set in various cards:
 *
 * Coherence at variant passages:  global, var_only
 * Coherence in attestations:
 * General textual flow:           global
 */

export default {
    'props' : {
        'pass_id'  : { 'type' : Number,  'required' : true },
        'epoch'    : { 'type' : Number,  'required' : true },
        'global'   : { 'type' : Boolean, 'default' : false },
        'var_only' : { 'type' : Boolean, 'default' : false },
        'chord'    : { 'type' : Boolean, 'default' : false },
        'prefix'   : { 'type' : String,  'default' : '' },
    },
    'components' : {
        'alert'        : alert,
        'button-group' : button_group,
        'card-caption' : card_caption,
        'context-menu' : context_menu,
        'toolbar'      : toolbar,
        'd3stemma'     : d3_stemma_layout,
        'd3chord'      : d3_chord_layout,
    },
    data () {
        return {
            'passage' : {},
            'options' : this.get_options (),
            'toolbar' : this.get_toolbar (),
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
        'toolbar.labez' : function () {
            // Fixes #84
            this.$trigger ('coherence_in_attestations_variant_changed', null);
        },
    },
    /** @lends module:client/textflow */
    'methods' : {
        /**
         * Load a new passage.
         */
        load_passage () {
            const vm = this;

            if (vm.pass_id === 0) {
                return;
            }

            const graph_vm = vm.get_graph_vm ();
            const wrapper = vm.$el.querySelector ('.svg-wrapper');

            const requests = [
                vm.get ('passage.json/' + vm.pass_id),
                vm.get (vm.build_url ('textflow.dot')),
                tools.fade_out (wrapper).promise,
            ];
            Promise.all (requests).then ((responses) => {
                wrapper.style.visibility = 'hidden';
                vm.passage = responses[0].data.data;
                const bbox = graph_vm.load_dot (responses[1].data);
                wrapper
                    .velocity ({
                        'width'  : (bbox.width  + SVG_X_BORDER),
                        'height' : (bbox.height + SVG_Y_BORDER),
                    }, { 'complete' : () => wrapper.style.visibility = 'visible',
                         ... tools.velocity_opts })
                    .velocity ({
                        'visibility' : 'visible',
                        'opacity' : 1.0,
                    }, tools.velocity_opts);
            });
        },
        get_options () {
            const vm = this;
            if (vm.global && !vm.var_only) {
                return Object.assign ({}, options, { 'include' : options.include_z });
            }
            return options;
        },
        get_toolbar () {
            const vm = this;
            const rg_id_all = vm.$store.state.current_application.rg_id_all || 0;
            const download_buttons = {
                'dot' : () => this.download ('textflow.dot'),
                'png' : () => this.download ('textflow.png'),
            };
            const tb_global_varonly = {
                'rg_id'        : rg_id_all,
                'include'      : [],
                'mode'         : 'sim',
                'cliques'      : [],
                'connectivity' : 5,
                'var_only'     : ['var_only'],
                'hyp_a'        : 'A',
                'checks'       : [],
            };
            const tb_local = {
                'rg_id'        : rg_id_all,
                'include'      : [],
                'mode'         : 'sim',
                'labez'        : 'a',
                'connectivity' : 5,
                'fragments'    : [],
                'hyp_a'        : 'A',
                'checks'       : [],
                ... download_buttons,
            };
            const tb_global = {
                'rg_id'   : rg_id_all,
                'include' : [],
                'mode'    : 'sim',
                'checks'  : [],
                ... download_buttons,
            };
            if (vm.global && vm.var_only) {
                if (vm.chord) {
                    return tb_global_varonly;
                }
                return {
                    ... tb_global_varonly,
                    ... download_buttons,
                }
            }
            if (vm.global) {
                return tb_global;
            }
            return tb_local;
        },
        get_graph_vm () {
            return this.$refs.engine;
        },
        async on_contextmenu (event) {
            if (this.$store.getters.can_write) {
                this.$refs.menu.open (await build_contextmenu (event, this), event.target);
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
        build_url (page) {
            const vm = this;
            const params = pick (vm.toolbar, [
                'labez', 'connectivity', 'rg_id', 'include', 'fragments',
                'mode', 'hyp_a', 'var_only', 'cliques', 'checks',
            ]);

            // provide a width and fontsize for GraphViz to format the graph
            const cstyle = getComputedStyle (vm.$el);
            params.width    = parseFloat (cstyle.getPropertyValue ('width')); // in px
            params.fontsize = parseFloat (cstyle.getPropertyValue ('font-size')); // in px

            return `${page}/${vm.pass_id}?` + tools.param (params);
        },
        download (page) {
            window.open (this.build_full_api_url (this.build_url (page), '_blank'));
        },
    },
    mounted () {
        this.load_passage ();
    },
};
</script>

<style lang="scss">
/* textflow.vue */

div.variant-textflow {
    path.link {
        stroke-dasharray: none;
    }
}
</style>
