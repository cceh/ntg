<template>
  <div class="panel-slidable panel-heading panel-relatives-metrics">
    <template v-if="mt">
      <span :data-labez="mt.labez" class="mt fg_labez"><span class="ms hilite-target" data-ms-id="mt_id">MT</span>
      ({{ mt.labez }})</span> •
    </template>
    <template v-if="ms">
      <span
        title="The percentage of majority readings at passages where the manuscript is extant and MT is defined."
      >MT {{ ms.mt.toFixed (2) }}</span> •
      <span
        title="The percentage of majority readings at passages where the manuscript is extant."
      >MT/P {{ ms.mtp.toFixed (2) }}</span> •
      <span
        title="The average agreement with all witnesses included."
      >AA {{ ms.aa.toFixed (2) }}</span> •
      <span
        title="The median agreement with all witnesses included."
      >MA {{ ms.ma.toFixed (2) }}</span>
    </template>
  </div>
</template>

<script>
/**
 * This module implements the information bar about the average agreements
 * in the relatives popup.
 *
 * @module relatives_metrics
 *
 * @author Marcello Perathoner
 */

import { mapGetters } from 'vuex';

export default {
    'props' : ['ms_id'],
    data () {
        return {
            'ms'    : null,
            'mt'    : null,
            'mt_id' : 2,
        };
    },
    'computed' : {
        caption () {
            return this.ms ? `Relatives for <span class="ms">W1:</span>
                <span class="fg_labez" data-labez="${this.ms.labez}"><span
                      class="ms hilite-source" data-ms-id="${this.ms_id}">${this.ms.hs}</span>
                (<span class="labez">${this.ms.labez}</span>) ${this.ms.length}</span>` : 'Loading ...';
        },
        ...mapGetters ([
            'passage',
        ]),
    },
    'watch' : {
        passage () {
            // NOT this.$parent.load_passage () because the caption must change
            // even if the panel is closed
            this.load_passage ();
        },
        caption (new_caption) {
            this.$parent.set_caption (new_caption);
        },
    },
    'methods' : {
        /**
         * Load new data.
         *
         * Display new data after the user navigated to a different passage.
         *
         * @function load_passage
         *
         * @param {Object} passage - The new passage
         */
        load_passage () {
            const vm = this;
            vm.get (`manuscript-full.json/${this.passage.pass_id}/id${this.ms_id}`).then ((response) => {
                vm.ms = response.data.data;
            });
            if (vm.ms_id !== 2) {
                vm.get (`manuscript-full.json/${this.passage.pass_id}/id${this.mt_id}`).then ((response) => {
                    vm.mt = response.data.data;
                });
            } else {
                vm.mt = null;
            }
        },
    },
    mounted () {
        this.load_passage ();
    },
};
</script>
