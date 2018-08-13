<template>
  <div class="relatives-metrics-vm">
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
 * @component relatives_metrics
 *
 * @author Marcello Perathoner
 */

import { mapGetters } from 'vuex';

export default {
    'props' : ['ms'],
    data () {
        return {
            'mt'    : null,
            'mt_id' : 2,
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
        ms () {
            this.load_passage ();
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
            if (vm.ms && vm.ms.ms_id !== 2) {
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
