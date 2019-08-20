<template>
  <div class="textflow-vm card-slidable">
    <div :class="'wrapper svg-wrapper ' + cssclass"
         @contextmenu.prevent="on_contextmenu" @click="on_click">
      <slot />
    </div>
    <context-menu ref="menu" @menu-click="on_menu_click" />
  </div>
</template>

<script>
/**
 * This module displays a textflow diagram.  A textflow diagram is a directed
 * acyclic graph that shows the relationship between all manuscripts that offer
 * one reading at one passage.  It can be used to deduce where a reading
 * originated.
 *
 * @component textflow
 * @author Marcello Perathoner
 */

import { mapGetters } from 'vuex';
import $     from 'jquery';
import _     from 'lodash';
import tools from 'tools';
import context_menu from 'widgets/context_menu.vue';
import { mkmsg }    from 'widgets/context_menu.vue';

/**
 * Open a context menu when right clicked on a node.
 *
 * The context menu can be used to reassign the node to a different clique.
 *
 * @function build_contextmenu
 *
 * @param {Object} event - The event
 * @param {Object} vm    - The Vue instance
 */

function build_contextmenu (event, vm) {
    const passage = vm.passage;

    const msid    = event.target.parentNode.dataset.msId;
    const dataset = event.target.dataset;
    const data = {
        'labez_old'  : dataset.labez,
        'clique_old' : dataset.clique,
        'ms_ids'     : tools.bfs (vm.get_graph_vm ().graph.edges, msid),
    };

    const cliques = _.filter (vm.$store.state.passage.cliques, (o) => (o.labez[0] !== 'z'));
    const actions = [];

    // Menu Header
    actions.push ({
        'msg'   : mkmsg ('Clique', data.labez_old, data.clique_old),
        'bg'    : data.labez_old,
        'class' : 'disabled',
        'data' : {
            ... data,
            'action'   : '',
            'disabled' : true,
        }
    });

    // cliques
    _.forEach (cliques, function (c) {
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
    });

    return _.groupBy (actions, a => a.data.action);
}

/*
 * @vue-prop {String} cssclass - CSS classes to apply on the wrapper element.
 * @vue-prop {bool}   global   - Display global textual flow
 * @vue-prop {bool}   var_only - Display only nodes and links between different readings.
 *
 * Coherence at variant passages:  global var_only
 * Coherence in attestations:
 * General textual flow:           global
 */

export default {
    'components' : {
        'context-menu' : context_menu,
    },
    'props' : ['cssclass', 'global', 'var_only', 'toolbar'],
    data () {
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
        /**
         * Load a new passage.
         *
         * @function load_passage
         */
        load_passage () {
            const vm = this;

            if (vm.passage.pass_id === 0) {
                return Promise.resolve ();
            }

            // dirty hack! Make content visible so SVG getBBox () will work.
            vm.$wrapper.slideDown ();

            const graph_vm = vm.get_graph_vm ();
            const p1 = graph_vm.load_dot (vm.build_url ('textflow.dot'));
            p1.then (() => {
                vm.$card.animate ({ 'width' : (graph_vm.bbox.width + 20) + 'px' });
            });
            return p1;
        },
        get_graph_vm () {
            return this.$children[0];
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
        build_url (page) {
            const vm = this;
            const params = _.pick (vm.toolbar, [
                'labez', 'connectivity', 'range', 'include', 'fragments',
                'mode', 'hyp_a', 'var_only', 'cliques',
            ]);

            // provide a width and fontsize for GraphViz to format the graph
            params.width = vm.$wrapper.width ();                          // in px
            params.fontsize = parseFloat ($ ('body').css ('font-size'));  // in px

            return page + '/' + vm.passage.pass_id + '?' + $.param (params);
        },
        download (page) {
            window.open (this.build_full_api_url (this.build_url (page), '_blank'));
        },
    },
    mounted () {
        this.toolbar.dot = () => this.download ('textflow.dot');
        this.toolbar.png = () => this.download ('textflow.png');
        this.$card    = $ (this.$el).closest ('.card');
        this.$wrapper = $ (this.$el).find ('.wrapper');
        this.load_passage ();
    },
};
</script>

<style lang="scss">
/* textflow.vue */
@import "bootstrap-custom";

</style>
