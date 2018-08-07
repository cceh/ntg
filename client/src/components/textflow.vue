<template>
  <div :class="'panel-content svg-wrapper panel-slidable ' + cssclass"
       @contextmenu.prevent="on_contextmenu">
    <slot />
  </div>
</template>

<script>
/**
 * This module displays a textflow diagram.  A textflow diagram is a directed
 * acyclic graph that shows the relationship between all manuscripts that offer
 * one reading at one passage.  It can be used to deduce where a reading
 * originated.
 *
 * @module textflow
 * @author Marcello Perathoner
 */

import { mapGetters } from 'vuex';
import $ from 'jquery';
import _ from 'lodash';
import tools from 'tools';
import 'bootstrap';

/**
 * Open a context menu when right clicked on a node.
 *
 * The context menu can be used to reassign the node to a different split.
 *
 * @function open_contextmenu
 *
 * @param {Object} event - The event
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
            xhr2.fail ((xhrobj) => {
                tools.xhr_alert (xhrobj, event.data.$wrapper);
            });
            menu.fadeOut (() => { menu.remove (); });
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
 */
function load_passage (vm, passage) {
    if (passage.pass_id === 0) {
        return Promise.resolve ();
    }

    const tb = vm.$parent.toolbar;

    const params = _.pick (tb, [
        'labez', 'connectivity', 'range', 'include', 'fragments',
        'mode', 'hyp_a', 'var_only', 'width', 'fontsize', 'cliques',
    ]);

    // dirty hack! Make panel visible so SVG getBBox () will work.
    vm.$wrapper.slideDown ();

    // provide a width and fontsize for GraphViz to format the graph
    params.width = vm.$wrapper.width ();                            // in px
    params.fontsize = parseFloat (vm.$wrapper.css ('font-size'));   // in px

    tb.dot_url = 'textflow.dot/' + passage.pass_id + '?' + $.param (params);
    tb.png_url = 'textflow.png/' + passage.pass_id + '?' + $.param (params);

    const graph_vm = vm.get_graph_vm ();
    const p1 = graph_vm.load_dot (tb.dot_url);
    p1.then (() => {
        vm.$panel.animate ({ 'width' : (graph_vm.bbox.width + 20) + 'px' });
    });
    return p1;
}

/**
 * @param {bool}   cssclass - CSS classes to apply on the wrapper element.
 * @param {bool}   global   - Display global textual flow
 * @param {bool}   var_only - Display only nodes and links between different readings.
 */

export default {
    'props' : ['cssclass', 'global', 'var_only'],
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
    },
    'methods' : {
        load_passage () {
            return load_passage (this, this.passage);
        },
        get_graph_vm () {
            return this.$children[0];
        },
        on_contextmenu (event) {
            if (this.$store.state.current_user.is_editor) {
                open_contextmenu (event, this);
            }
        },
    },
    created () {
        this.$parent.toolbar = {
            'global'       : this.global,
            'labez'        : this.global ? '' : 'a',
            'connectivity' : '5',
            'range'        : 'All',
            'include'      : [],
            'fragments'    : [],
            'mode'         : 'sim',
            'hyp_a'        : 'A',
            'var_only'     : this.var_only ? ['var_only'] : [],
            'cliques'      : [],
            'dot_url'      : null,
            'png_url'      : null,
        };
    },
    mounted () {
        this.$panel   = $ (this.$el).closest ('.panel');
        this.$wrapper = $ (this.$el).closest ('.panel-content');
        this.load_passage ();
    },
};
</script>

<style lang="less">
@import "@{BS}/variables.less";
@import "@{BS}/mixins.less";

div.panel table.contextmenu {
    position: absolute;
    z-index: @zindex-dropdown;
    margin: 0;
    padding: 5px 0;
    font-size: @font-size-base;
    text-align: left;
    background-color: @dropdown-bg;
    border: 1px solid @dropdown-fallback-border;
    border: 1px solid @dropdown-border;
    border-radius: @border-radius-base;
    background-clip: padding-box;
    .box-shadow(0 6px 12px rgba(0,0,0,.175));

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
            color: @dropdown-link-active-color;
            background: @dropdown-link-active-bg;
        }
        &.menu-label { text-align: right; }
        &.menu-description { padding-left: 0; }
    }
}
</style>
