<template>
  <div class="coherence_vm want_hashchange"
       @hashchange="on_hashchange"
       @navigator="on_navigator"
       @goto_attestation="on_goto_attestation"
       @destroy_relatives_popup="on_destroy_relatives_popup ($event, $event.detail.data)">
    <page-header :caption="caption" />

    <div class="container bs-docs-container">

      <!-- the parent for all floating cards must be at the top of the page so
           the cards will not move around on page resizes etc. this element will
           only contain absolute-positioned stuff and thus has a height of 0 -->
      <div id="floating-cards">
        <card v-for="card in floating_cards" :key="card.id"
              :card_id="card.id" :position_target="card.position_target"
              class="card-closable card-draggable card-floating">

          <div class="card-header">
            <toolbar :toolbar="card.toolbar">
              <button-group type="radio" v-model="card.toolbar.type"
                            :options="options.type" />
              <button-group type="radio" v-model="card.toolbar.limit"
                            :options="options.limit" />
              <labezator v-model="card.toolbar.labez" :options="options.labez_all" />
              <range v-model="card.toolbar.range">Chapter:</range>
              <button-group type="checkbox" v-model="card.toolbar.include"
                            :options="options.include" />
              <button-group type="checkbox" v-model="card.toolbar.fragments"
                            :options="options.fragments" />
              <button-group type="radio" v-model="card.toolbar.mode"
                            :options="options.mode" />
              <button-group slot="right" :options="options.csv" />
            </toolbar>
          </div>

          <relatives :ms_id="card.ms_id" :toolbar="card.toolbar" />
        </card>
      </div>

      <navigator ref="nav" class="mb-3" />

      <leitzeile />

      <!-- Apparatus -->

      <card cssclass="card-apparatus" caption="Apparatus">
        <div class="card-header card-slidable">
          <toolbar :toolbar="tb_apparatus">
            <button-group type="checkbox" v-model="tb_apparatus.cliques"
                          :options="options.cliques" />
            <button-group type="checkbox" v-model="tb_apparatus.ortho"
                          :options="options.ortho" />
            <button-group slot="right" :options="options.find_relatives" />
          </toolbar>
        </div>
        <apparatus ref="apparatus" :toolbar="tb_apparatus" />
      </card>

      <!-- Local Stemma -->

      <card cssclass="card-local-stemma" caption="Local Stemma">
        <div class="card-header card-slidable">
          <toolbar :toolbar="tb_local_stemma">
            <button-group slot="right" :options="options.png_dot" />
          </toolbar>
        </div>
        <localstemma cssclass="stemma-wrapper local-stemma-wrapper" :toolbar="tb_local_stemma">
          <d3stemma prefix="ls_" />
        </localstemma>
      </card>

      <!-- Notes -->

      <card v-if="this.$store.state.current_user.is_editor"
            cssclass="card-notes" caption="Notes" default_closed="true">
        <div class="card-header card-slidable">
          <toolbar :toolbar="tb_notes">
            <b-button-group size="sm">
              <b-button :disabled="!tb_notes.save" variant="primary" size="sm" class="d-print-none"
                        @click="tb_notes.save ()">Save</b-button>
            </b-button-group>
          </toolbar>
        </div>
        <notes :passage="passage" :toolbar="tb_notes" />
      </card>

      <!-- Coherence at Variant Passages (GraphViz) -->

      <card cssclass="card-textflow card-variant-textflow"
            caption="Coherence at Variant Passages (GraphViz)">
        <div class="card-header card-slidable">
          <toolbar :toolbar="tb_varonly_textflow">
            <button-group type="checkbox" v-model="tb_varonly_textflow.cliques"
                          :options="options.cliques" />
            <connectivity v-model="tb_varonly_textflow.connectivity">Conn:</connectivity>
            <range v-model="tb_varonly_textflow.range">Chapter:</range>
            <button-group type="checkbox" v-model="tb_varonly_textflow.include"
                          :options="options.include" />
            <button-group type="radio" v-model="tb_varonly_textflow.mode"
                          :options="options.mode" />
            <labezator v-model="tb_varonly_textflow.hyp_a"
                       :options="options.hyp_a" />
            <button-group slot="right" :options="options.png_dot" />
          </toolbar>
        </div>
        <textflow cssclass="textflow-wrapper variant-textflow-wrapper" :toolbar="tb_varonly_textflow"
                  global="true" var_only="true">
          <d3stemma prefix="vtf_" />
        </textflow>
      </card>

      <!-- Coherence at Variant Passages (Chord) -->

      <card class="card-textflow card-variant-textflow-2"
            caption="Coherence at Variant Passages (Chord)" default_closed="true">
        <div class="card-header card-slidable">
          <toolbar :toolbar="tb_varonly_2_textflow">
            <button-group type="checkbox" v-model="tb_varonly_2_textflow.cliques"
                          :options="options.cliques" />
            <connectivity v-model="tb_varonly_2_textflow.connectivity">Conn:</connectivity>
            <range v-model="tb_varonly_2_textflow.range">Chapter:</range>
            <button-group type="checkbox" v-model="tb_varonly_2_textflow.include"
                          :options="options.include" />
            <button-group type="radio" v-model="tb_varonly_2_textflow.mode"
                          :options="options.mode" />
            <labezator v-model="tb_varonly_2_textflow.hyp_a"
                       :options="options.hyp_a" />
            <button-group slot="right" :options="options.png_dot" />
          </toolbar>
        </div>

        <textflow cssclass="textflow-wrapper variant-textflow-wrapper"
                  global="true" var_only="true" :toolbar="tb_varonly_2_textflow">
          <d3chord prefix="vtf2_" />
        </textflow>
      </card>

      <!-- Coherence in Attestations -->

      <card class="card-textflow card-local-textflow"
            caption="Coherence in Attestations">

        <div class="card-header card-slidable" @labez="on_destroy_relatives_popup ($event, 0)">
          <toolbar :toolbar="tb_local_textflow">
            <labezator v-model="tb_local_textflow.labez" :options="options.labez" />
            <connectivity v-model="tb_local_textflow.connectivity">Conn:</connectivity>
            <range v-model="tb_local_textflow.range">Chapter:</range>
            <button-group type="checkbox" v-model="tb_local_textflow.include"
                          :options="options.include" />
            <button-group type="checkbox" v-model="tb_local_textflow.fragments"
                          :options="options.fragments" />
            <button-group type="radio" v-model="tb_local_textflow.mode"
                          :options="options.mode" />
            <labezator v-model="tb_local_textflow.hyp_a"
                       :options="options.hyp_a" />
            <button-group slot="right" :options="options.png_dot" />
          </toolbar>
        </div>

        <textflow ref="lt" cssclass="textflow-wrapper local-textflow-wrapper" :toolbar="tb_local_textflow">
          <d3stemma prefix="tf_" />
        </textflow>
      </card>

      <!-- General Textual Flow -->

      <card class="card-textflow card-global-textflow"
            caption="General Textual Flow">

        <div class="card-header card-slidable">
          <toolbar :toolbar="tb_global_textflow">
            <range v-model="tb_global_textflow.range">Chapter:</range>
            <button-group type="checkbox" v-model="tb_global_textflow.include"
                          :options="options.include_z" />
            <button-group type="radio" v-model="tb_global_textflow.mode"
                          :options="options.mode" />
            <button-group slot="right" :options="options.png_dot" />
          </toolbar>
        </div>

        <textflow global="true" cssclass="textflow-wrapper global-textflow-wrapper" :toolbar="tb_global_textflow">
          <d3stemma prefix="gtf_" />
        </textflow>
      </card>

      <navigator />
    </div>
  </div>
</template>

<script>
/**
 * This module displays the coherence page.  This module is only a container for
 * the Vue.js components that actually display the gadgets.
 *
 * @component coherence
 * @author Marcello Perathoner
 */

import $ from 'jquery';
import Vue from 'vue';
import { mapGetters } from 'vuex';

import d3common    from 'd3_common';
import tools       from 'tools';
import { options } from 'widgets/options';

import page_header      from 'page_header.vue';
import leitzeile        from 'leitzeile.vue';
import card             from 'card.vue';
import card_caption     from 'card_caption.vue';
import navigator        from 'widgets/navigator.vue';
import labezator        from 'widgets/labezator.vue';
import range            from 'widgets/range.vue';
import connectivity     from 'widgets/connectivity.vue';
import button_group     from 'widgets/button_group.vue';
import toolbar          from 'widgets/toolbar.vue';
import apparatus        from 'apparatus.vue';
import notes            from 'notes.vue';
import d3_stemma_layout from 'd3_stemma_layout.vue';
import d3_chord_layout  from 'd3_chord_layout.vue';
import local_stemma     from 'local_stemma.vue';
import textflow         from 'textflow.vue';
import relatives        from 'relatives.vue';
import relmetrics       from 'relatives_metrics.vue';

Vue.component ('page-header',  page_header);
Vue.component ('navigator',    navigator);
Vue.component ('labezator',    labezator);
Vue.component ('range',        range);
Vue.component ('connectivity', connectivity);
Vue.component ('button-group', button_group);
Vue.component ('toolbar',      toolbar);
Vue.component ('leitzeile',    leitzeile);
Vue.component ('card',         card);
Vue.component ('card-caption', card_caption);
Vue.component ('toolbar',      toolbar);
Vue.component ('apparatus',    apparatus);
Vue.component ('notes',        notes);
Vue.component ('localstemma',  local_stemma);
Vue.component ('d3stemma',     d3_stemma_layout);
Vue.component ('d3chord',      d3_chord_layout);
Vue.component ('textflow',     textflow);
Vue.component ('relatives',    relatives);
Vue.component ('relmetrics',   relmetrics);

export default {
    'props' : ['current_user'],
    'data'  : function () {
        return {
            'floating_cards' : [],
            'card_id'        : 0,
            'options'        : options,
            'tb_apparatus'   : {
                'cliques' : [],  // Show readings or cliques.
                'ortho'   : [],  // Show orthographic variations.
                'rel'     : () => {},
            },
            'tb_local_stemma' : {
                'dot' : () => {},
                'png' : () => {},
            },
            'tb_varonly_textflow' : {
                'range'        : 'All',
                'include'      : [],
                'mode'         : 'sim',
                'cliques'      : [],
                'connectivity' : 5,
                'var_only'     : ['var_only'],
                'hyp_a'        : 'A',
                'dot'          : () => {},
                'png'          : () => {},
            },
            'tb_varonly_2_textflow' : {
                'range'        : 'All',
                'include'      : [],
                'mode'         : 'sim',
                'cliques'      : [],
                'connectivity' : 5,
                'var_only'     : ['var_only'],
                'hyp_a'        : 'A',
                'dot'          : () => {},
                'png'          : () => {},
            },
            'tb_local_textflow' : {
                'range'        : 'All',
                'include'      : [],
                'mode'         : 'sim',
                'labez'        : 'a',
                'connectivity' :  5,
                'fragments'    : [],
                'hyp_a'        : 'A',
                'dot'          : () => {},
                'png'          : () => {},
            },
            'tb_global_textflow' : {
                'range'        : 'All',
                'include'      : [],
                'mode'         : 'sim',
                'dot'          : () => {},
                'png'          : () => {},
            },
            'tb_notes' : {
                'save' : false,
            },
        };
    },
    'computed' : {
        'caption' : function () {
            return this.$store.state.passage.hr;
        },
        ...mapGetters ([
            'passage',
        ]),
    },
    'methods' : {
        set_hash (param, data) {
            const hash = window.location.hash ? window.location.hash.substring (1) : '';
            const params = tools.deparam (hash);
            params[param] = data;
            window.location.hash = '#' + $.param (params);
        },
        on_navigator (event) {
            // All navigation is done by manipulating the hash.
            this.set_hash ('pass_id', event.detail.data);
        },
        on_hashchange () {
            const nav = this.$refs.nav;
            const params = tools.deparam (window.location.hash.substring (1));
            if ('pass_id' in params) {
                nav.set_passage (params.pass_id);
            } else {
                nav.set_passage (1);
            }
        },
        /**
         * Create a new popup managed by the relatives module.
         *
         * We have to create these dynamically because there may be many open at once.
         *
         * @function create_relatives_popup
         *
         * @param {integer} ms_id - The manuscript id
         * @param {jQuery} target - An element. The popup will be positioned relative to this element.
         */
        create_relatives_popup (ms_id, target) {
            this.card_id += 1;
            this.floating_cards.push ({
                'id'              : this.card_id,
                'ms_id'           : ms_id,
                'position_target' : target,
                'toolbar'         : this.tb_relatives (),
            });
        },
        on_destroy_relatives_popup (event, card_id) {
            if (card_id === 0) {
                this.floating_cards = [];
            } else {
                this.floating_cards = this.floating_cards.filter (item => item.id !== card_id);
            }
        },
        on_goto_attestation (event) {
            const labez = event.detail.data;
            const lt = this.$refs.lt;
            lt.toolbar.labez = labez;
            lt.load_passage ();

            $ ('html, body').animate ({
                'scrollTop' : $ (lt.$el).offset ().top,
            }, 500);
        },
        tb_relatives () {
            return {
                'type'      : 'rel',
                'range'     : 'All',
                'labez'     : 'all+lac',
                'limit'     : '0',
                'include'   : [],
                'fragments' : [],
                'mode'      : 'sim',
                'csv'       : () => {}, // this will be replaced in relatives.vue
            };
        },
    },
    created () {
        /**
         * Initialize the component.
         *
         * @function created
         */
        const vm = this;

        // insert css for color palettes
        d3common.insert_css_palette (d3common.generate_css_palette (
            d3common.labez_palette,
            d3common.cliques_palette
        ));

        // install event handlers

        // Click on a ms. in the apparatus or in a relatives popup.
        $ (document).on ('click', '.ms[data-ms-id]', function (event) {
            event.stopPropagation ();
            let ms_id = $ (event.target).attr ('data-ms-id');
            vm.create_relatives_popup (ms_id, event.target);
        });

        // Click on a comparison row in the apparatus or in a relatives popup.
        $ (document).on ('click', 'tr.comparison[data-ms2-id]', function (event) {
            event.stopPropagation ();
            let ms1_id = $ (event.currentTarget).attr ('data-ms1-id');
            let ms2_id = $ (event.currentTarget).attr ('data-ms2-id');
            let win = window.open ('comparison#ms1=id' + ms1_id + '&ms2=id' + ms2_id, '_blank');
            win.focus ();
        });

        // Click on a node in the textflow diagram.
        $ (document).on ('click', 'div.card-textflow g.node', function (event) {
            let ms_id = $ (event.currentTarget).attr ('data-ms-id'); // the g.node, not the circle
            vm.create_relatives_popup (ms_id, event.currentTarget);
        });

        // Click on canvas to close context menus
        $ (document).on ('click', function (dummy_event) {
            let $menu = $ ('table.contextmenu');
            $menu.fadeOut (() => $menu.remove ());
        });
    },
    mounted () {
        // On first page load simulate user navigation to hash.
        this.on_hashchange ();
    },
};
</script>

<style lang="scss">
/* coherence.vue */
@import "bootstrap-custom";

#floating-cards {
    position: relative;
    height: 0;

    .card-floating {
        position: fixed;
        z-index: 10;
        width: 38em;
        min-width: 38em;
    }
}

.ms[data-ms-id]:hover {
    cursor: pointer;
    text-decoration: underline;
}

a.highlight,
span.highlight {
    background-color: #ff0;
}

a.selected,
span.selected {
    outline: 2px solid #f00;
}

$svg-link-color: #ccc;
$svg-link-opacity: 0.6;

/* links */

path,
line,
text {
    &.link {
        stroke: $svg-link-color;
        stroke-opacity: $svg-link-opacity;
        stroke-width: 2px;
        fill: none;

        &.dashed {
            stroke-dasharray: 4 4;
        }

        &.hover {
            stroke-opacity: 1;
        }

        &.hi-source {
            stroke: red;
        }

        &.hi-target {
            stroke: green;
        }
    }
}

path,
line {
    &.link {
        &.hover {
            stroke-width: 3px;
        }
    }
}

text {
    dominant-baseline: middle;
    text-anchor: middle;
    fill: #000;
    cursor: pointer;
    pointer-events: none;

    &.link {
        stroke: #fff;
        stroke-width: 2px;
        stroke-linejoin: round;
        paint-order: stroke;

        &.hover {
            stroke-width: 2px;
            fill: black;
        }
    }
}

marker.link {
    stroke: $svg-link-color;
    stroke-opacity: $svg-link-opacity;
    fill: #000;
    fill-opacity: 1;
    stroke-dasharray: none;
    visibility: visible;
}

div.variant-textflow-wrapper {
    path.link {
        stroke-dasharray: none;
    }
}

div.local-stemma-wrapper {
    marker.link {
        visibility: hidden;
    }
}

/* nodes */

circle,
ellipse {
    &.node {
        stroke-width: 3px;
        fill: #fff;
        transition: fill 2s linear;
    }
}

g.clickable ellipse.node {
    cursor: pointer;
}

g.draggable ellipse.node {
    cursor: move;
}

line.link.highlight,
g.highlight ellipse.node {
    transition: fill 0.5s linear;
    fill: #ff0;
}

g.selected ellipse.node {
    transition: fill 0.5s linear;
    fill: #f00;
}

/* subgraphs */

rect.subgraph {
    stroke: $card-border-color;
    stroke-width: $card-border-width;
    fill: $card-cap-bg;

    &.rounded {
        rx: $card-border-radius;
        ry: $card-border-radius;
    }
}

/* wrapper */

div.svg-wrapper {
    width: 100%;

    svg {
        display: block;
        margin: 1em auto;
    }
}

</style>
