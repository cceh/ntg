<template>
  <div class="coherence_vm want_hashchange"
       @hashchange="on_hashchange"
       @navigator="on_navigator"
       @goto_attestation="on_goto_attestation"
       @destroy_relatives_popup="on_destroy_relatives_popup">
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
            <toolbar :toolbar="card.toolbar" />
          </div>

          <relatives :ms_id="card.ms_id" :toolbar="card.toolbar" />
        </card>
      </div>

      <navigator ref="nav" />

      <leitzeile />

      <card cssclass="card-apparatus" caption="Apparatus">
        <apparatus />
      </card>

      <card cssclass="card-local-stemma" caption="Local Stemma">
        <localstemma cssclass="stemma-wrapper local-stemma-wrapper">
          <d3stemma prefix="ls_" />
        </localstemma>
      </card>

      <card v-if="this.$store.state.current_user.is_editor"
            cssclass="card-notes" caption="Notes" default_closed="true">
        <notes />
      </card>

      <card cssclass="card-textflow card-variant-textflow"
            caption="Coherence at Variant Passages (GraphViz)">
        <textflow cssclass="textflow-wrapper variant-textflow-wrapper"
                  global="true" var_only="true">
          <d3stemma prefix="vtf_" />
        </textflow>
      </card>

      <card class="card-textflow card-variant-textflow-2"
            caption="Coherence at Variant Passages (Chord)" default_closed="true">
        <textflow cssclass="textflow-wrapper variant-textflow-wrapper"
                  global="true" var_only="true">
          <d3chord prefix="vtf2_" />
        </textflow>
      </card>

      <card class="card-textflow card-local-textflow"
            caption="Coherence in Attestations">
        <textflow ref="lt" cssclass="textflow-wrapper local-textflow-wrapper">
          <d3stemma prefix="tf_" />
        </textflow>
      </card>

      <card class="card-textflow card-global-textflow"
            caption="General Textual Flow">
        <textflow global="true" cssclass="textflow-wrapper global-textflow-wrapper">
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

import d3common  from 'd3_common';
import tools     from 'tools';

import page_header      from 'page_header.vue';
import navigator        from 'navigator.vue';
import leitzeile        from 'leitzeile.vue';
import card             from 'card.vue';
import card_caption     from 'card_caption.vue';
import toolbar          from 'toolbar.vue';
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
        };
    },
    'computed' : {
        'caption' : function () {
            return `Attestation for ${this.$store.state.passage.hr}`;
        },
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
                'toolbar'         : this.relatives_toolbar (),
            });
        },
        on_destroy_relatives_popup (event) {
            const card_id = event.detail.data;
            this.floating_cards = this.floating_cards.filter (item => item.id !== card_id);
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
        relatives_toolbar () {
            return {
                'type'                  : 'rel',
                'range'                 : 'All',
                'limit'                 : '10',
                'include'               : [],
                'fragments'             : [],
                'mode'                  : 'sim',
                'labez'                 : 'all+lac',
                'labez_dropdown_prefix' : [['all', 'All']],
                'labez_dropdown_suffix' : [['all+lac', 'All+Lac']],
                'csv'                   : true, // this will be replaced by a closure later
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
        min-width: 0;
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
    visibility: hidden;
}

div.variant-textflow-wrapper {
    path.link {
        stroke-dasharray: none;
    }

    marker.link {
        visibility: visible;
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
