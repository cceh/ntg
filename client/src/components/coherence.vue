<template>
  <div class="vm-coherence"
       @epoch="on_epoch"
       @goto_attestation="on_goto_attestation"
       @coherence_in_attestations_variant_changed="on_coherence_in_attestations_variant_changed"
  >
    <div class="container bs-docs-container">
      <!-- the parent for all floating cards must be at the top of the page so
           the cards will not move around on page resizes etc. this element will
           only contain absolute-positioned stuff and thus has a height of 0 -->
      <relatives :pass_id="pass_id" ref="relatives" />

      <div class="btn-toolbar">
        <navigator @input="on_nav" :value="pass_id" class="mb-3" />
      </div>

      <leitzeile :pass_id="pass_id" />

      <!-- Apparatus -->

      <card class="card-apparatus card-wide">
        <card-caption>
          Apparatus
        </card-caption>

        <apparatus :pass_id="pass_id" :epoch="epoch" />
      </card>

      <!-- Local Stemma -->

      <card class="card-local-stemma card-wide">
        <card-caption>
          Local Stemma
        </card-caption>

        <localstemma :pass_id="pass_id" :epoch="epoch" />
      </card>

      <!-- Notes -->

      <card v-if="$store.getters.can_read_private" class="card-notes card-wide" :visible="false">
        <card-caption>
          Notes
        </card-caption>

        <notes :pass_id="pass_id" ref="notes" />
      </card>

      <!-- Coherence at Variant Passages (GraphViz) -->

      <card class="card-textflow card-variant-textflow card-wide">
        <card-caption>
          Coherence at Variant Passages (GraphViz)
        </card-caption>

        <textflow :pass_id="pass_id" :epoch="epoch" class="variant-textflow"
                  :global="true" :var_only="true" prefix="vtf_" />
      </card>

      <!-- Coherence at Variant Passages (Chord) -->

      <card class="card-textflow card-variant-textflow-2 card-wide" :visible="false">
        <card-caption>
          Coherence at Variant Passages (Chord)
        </card-caption>

        <textflow :pass_id="pass_id" :epoch="epoch" class="variant-textflow"
                  :global="true" :var_only="true" prefix="vtf2_" :chord="true" />
      </card>

      <!-- Coherence in Attestations -->

      <card class="card-textflow card-local-textflow card-wide">
        <card-caption>
          Coherence in Attestations
        </card-caption>

        <textflow ref="lt" :pass_id="pass_id" :epoch="epoch" class="local-textflow"
                  prefix="tf_" />
      </card>

      <!-- General Textual Flow -->

      <card class="card-textflow card-global-textflow card-wide">
        <card-caption>
          General Textual Flow
        </card-caption>

        <textflow :pass_id="pass_id" :epoch="epoch" class="global-textflow"
                  :global="true" prefix="gtf_" />
      </card>

      <div class="btn-toolbar">
        <navigator @input="on_nav" :value="pass_id" class="mb-3" />
      </div>

    </div>
  </div>
</template>

<script>
/**
 * This module displays the coherence page.  This module is only a container for
 * the Vue.js components that actually display the gadgets.
 *
 * @component client/coherence
 * @author Marcello Perathoner
 */

import Vue from 'vue';

import apparatus        from 'apparatus.vue';
import d3_chord_layout  from 'd3_chord_layout.vue';
import d3_stemma_layout from 'd3_stemma_layout.vue';
import leitzeile        from 'leitzeile.vue';
import local_stemma     from 'local_stemma.vue';
import notes            from 'notes.vue';
import relatives        from 'relatives.vue';
import textflow         from 'textflow.vue';
import tools            from 'tools';

import card             from 'widgets/card.vue';
import card_caption     from 'widgets/card_caption.vue';
import connectivity     from 'widgets/connectivity.vue';
import labezator        from 'widgets/labezator.vue';
import navigator        from 'widgets/navigator.vue';
import range            from 'widgets/range.vue';
import toolbar          from 'widgets/toolbar.vue';

Vue.component ('apparatus',    apparatus);
Vue.component ('card',         card);
Vue.component ('card-caption', card_caption);
Vue.component ('connectivity', connectivity);
Vue.component ('d3chord',      d3_chord_layout);
Vue.component ('d3stemma',     d3_stemma_layout);
Vue.component ('labezator',    labezator);
Vue.component ('leitzeile',    leitzeile);
Vue.component ('localstemma',  local_stemma);
Vue.component ('navigator',    navigator);
Vue.component ('notes',        notes);
Vue.component ('range',        range);
Vue.component ('relatives',    relatives);
Vue.component ('textflow',     textflow);
Vue.component ('toolbar',      toolbar);
Vue.component ('toolbar',      toolbar);

export default {
    'props' : {
        'passage_or_id' : { 'type' : [Number, String], 'required' : true },
    },
    data () {
        return {
            'pass_id' : 0,  // Number !!!
            'epoch'   : 1,  // bump this to reload components
        };
    },
    /** @lends module:client/coherence */
    'methods' : {
        /**
         * Set a new passage.
         *
         * @param {string} pass_id - The new passage id
         * @return {Promise} - Resolved when the new passage is loaded
         */
        set_passage (passage_or_id) {
            const vm = this;

            const p = Promise.all ([
                vm.get ('passage.json/' + passage_or_id),
            ]);
            p.then ((responses) => {
                const passage = responses[0].data.data;
                vm.pass_id = passage.pass_id; // Number! updates our children
                this.$store.commit ('caption', passage.hr);
            });
            return p;
        },
        /**
         * React on user navigation through the navigator widget.
         *
         * The navigator widget $emits an input event on navigation.
         * Translate the event into a new route.
         *
         * @param {Number} new_pass_id - Id of the passage to navigate to.
         */
        on_nav (new_pass_id) {
            this.$router.push ({
                'name'   : 'coherence',
                'params' : { 'passage_or_id' : new_pass_id }
            });
        },
        /**
         * React to epoch changes, eg. when a child edits the database. Tell
         * all children to refresh.
         */
        on_epoch () {
            this.epoch++;
            // console.log ('epoch: ' + this.epoch);
        },
        /**
         * Scroll to the "Coherence in Attestations" card and load the given
         * attestation.
         *
         * @param {Event} event - The event, sent from a child.
         */
        on_goto_attestation (event) {
            const labez = event.detail.data;
            const lt = this.$refs.lt;
            lt.toolbar.labez = labez;
            lt.load_passage ();

            const top = document.querySelector ('.card-local-textflow').offsetTop;
            document.querySelector ('html').velocity ({
                'scrollTop' : top + 'px',
            });
        },
        /**
         * Close all relatives popups if the attestation changes.
         *
         * @param {Event} event - The event, sent from a child.
         */
        on_coherence_in_attestations_variant_changed (event) {
            this.$refs.relatives.on_destroy_relatives_popup (event, 0); // Fixes #84
        },
    },
    beforeRouteEnter (to, from, next) {
        next (vm => vm.set_passage (to.params.passage_or_id));
    },
    async beforeRouteUpdate (to, from, next) {
        const vm = this;
        const notes = this.$refs.notes;
        if (notes && notes.can_save ()) {
            if (confirm ('You have unsaved notes! Save notes?')) {
                await notes.on_save ();
            }
        }
        await vm.set_passage (to.params.passage_or_id);
        next ();
    },
};
</script>

<style lang="scss">
/* coherence.vue */
@import "bootstrap-custom";

div.vm-coherence {
    div.card-wide {
        min-width: 100%;
        width: fit-content;
        margin-bottom: $spacer;
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

    .svg-wrapper {
        display: flex;
        align-items: center;
        justify-content: center;
        min-width: 100%;
    }

    /* SVG stuff */

    $svg-link-color: #ccc;
    $svg-link-opacity: 0.6;

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

            &.dotted {
                stroke-dasharray: 1 1;
            }

            &.bold {
                stroke-width: 4px;
            }

            &.congruence-error {
                stroke: red !important;
                stroke-width: 6px;
            }

            &.hover {
                stroke-opacity: 1;
            }

            &.hi-source {
                stroke: red !important;
            }

            &.hi-target {
                stroke: green !important;
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

    /* nodes */

    circle,
    ellipse {
        &.node {
            stroke-width: 3px;
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
        transition: fill 0.2s linear;
        fill: #ff0 !important;
    }

    g.selected ellipse.node {
        transition: fill 0.2s linear;
        fill: #f00 !important;
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
}
</style>
