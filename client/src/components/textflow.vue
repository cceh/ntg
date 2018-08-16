<template>
  <div class="textflow-vm card-slidable">
    <div class="card-header">
      <toolbar @dot="download ('textflow.dot')" @png="download ('textflow.png')" />
    </div>

    <div :class="'wrapper svg-wrapper ' + cssclass"
         @contextmenu.prevent="on_contextmenu">
      <slot />
    </div>
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

import $ from 'jquery';
import _ from 'lodash';
import { mapGetters } from 'vuex';
import 'jquery-ui/menu.js';

import 'jquery-ui-css/theme.css';
import 'jquery-ui-css/menu.css';

import tools from 'tools';

/**
 * Open a context menu when right clicked on a node.
 *
 * The context menu can be used to reassign the node to a different split.
 *
 * @function open_contextmenu
 *
 * @param {Object} event - The event
 * @param {Object} vm    - The Vue instance
 */

function open_contextmenu (event, vm) {
    const passage = vm.passage;

    const msid    = event.target.parentNode.dataset.msId;
    const dataset = event.target.dataset;
    const data = {
        'labez_old'  : dataset.labez,
        'clique_old' : dataset.clique,
    };

    // build the context menu
    const menu  = $ ('<table class="contextmenu"></table>');
    menu.append ($ (tools.format (
        '<tr class="ui-state-disabled">'
            + '<td class="bg_labez" data-labez="{labez_old}"></td>'
            + '<td>{labez_old}{clique_old}</td>'
            + '</tr>',
        data
    )));
    menu.append ($ ('<tr><td>-</td><td>-</td></tr>'));

    const cliques = _.filter (vm.$store.state.passage.cliques, (o) => (o[0][0] !== 'z'));
    _.forEach (cliques, (value) => {
        data.labez_new  = value[0];
        data.clique_new = value[1];

        if (data.labez_new === data.labez_old && data.clique_new !== data.clique_old) {
            menu.append ($ (tools.format (
                '<tr data-action="move-manuscripts" '
                    + 'data-labez_old="{labez_old}" data-clique_old="{clique_old}" '
                    + 'data-labez_new="{labez_new}" data-clique_new="{clique_new}">'
                    + '<td class="bg_labez" data-labez="{labez_old}"></td>'
                    + '<td>Move subtree to {labez_new}{clique_new}</td>'
                    + '</tr>',
                data
            )));
        }
    });

    menu.menu ({
        'select' : (ev, ui) => {
            const tr = ui.item[0];

            // console.log ('Selected: ' + $ (tr).text ());

            const xhr2 = vm.post ('stemma-edit/' + passage.pass_id, $.extend ({}, tr.dataset, {
                // do not extend the dataset itself, because arrays cannot
                // be part of datasets
                'ms_ids' : tools.bfs (vm.get_graph_vm ().graph.edges, msid),
            }));
            xhr2.then (() => {
                $ (window).trigger ('hashchange');
            });
            xhr2.catch ((reason) => {
                tools.xhr_alert (reason, event.data.$wrapper);
            });
            menu.fadeOut (() => { menu.remove (); });
        },
    });
    tools.svg_contextmenu (menu, event.target);
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
    'props' : ['cssclass', 'global', 'var_only'],
    data () {
        const tb = {
            'range'   : 'All',
            'include' : [],
            'mode'    : 'sim',
            'dot'     : true, // show a download dot button
            'png'     : true, // show a download png button
        };
        if (!this.global && !this.var_only) {
            tb.labez = 'a';
            tb.reduce_labez = true;
            tb.connectivity = 5;
            tb.fragments = [];
            tb.hyp_a = 'A';
        }
        if (this.global && this.var_only) {
            tb.cliques = [];
            tb.connectivity = 5;
            tb.var_only = ['var_only'];
            tb.hyp_a = 'A';
        }
        return {
            'toolbar' : tb,
            'dot_url' : null,
            'png_url' : null,
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
            return this.$children[1];
        },
        on_contextmenu (event) {
            if (this.$store.state.current_user.is_editor) {
                open_contextmenu (event, this);
            }
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
        this.$card    = $ (this.$el).closest ('.card');
        this.$wrapper = $ (this.$el).find ('.wrapper');
        this.load_passage ();
    },
};
</script>

<style lang="scss">
/* textflow.vue */
@import "bootstrap-custom";

div.card table.contextmenu {
    position: absolute;
    z-index: $zindex-dropdown;
    margin: 0;
    padding: 5px 0;
    font-size: $font-size-base;
    text-align: left;
    background-color: $dropdown-bg;
    border: $dropdown-border-width solid $dropdown-border-color;
    background-clip: padding-box;

    /* stylelint-disable at-rule-no-unknown */
    @include border-radius($dropdown-border-radius);
    @include box-shadow($dropdown-box-shadow);

    tr.ui-menu-item {
        &.ui-state-active {
            margin: 0;
            border-width: 0;
            background: #ccc;
        }
    }

    td.ui-menu-item-wrapper {
        /* padding: 3px 20px; */
        &.ui-state-active {
            margin: 0;
            border-width: 0;
            color: $dropdown-link-active-color;
            background: $dropdown-link-active-bg;
        }
        &.menu-label { text-align: right; }
        &.menu-description { padding-left: 0; }
    }
}
</style>
