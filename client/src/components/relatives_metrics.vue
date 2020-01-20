<template>
  <div class="vm-relatives-metrics">
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
 * @component client/relatives_metrics
 *
 * @author Marcello Perathoner
 */

export default {
    'props' : {
        'pass_id' : Number,
        'ms_id'   : Number,
    },
    data () {
        return {
            'ms'    : null,
            'mt'    : null,
            'mt_id' : 2,      // const
        };
    },
    'watch' : {
        pass_id () {
            this.load_passage ();
        },
        ms_id () {
            this.load_passage ();
        },
    },
    /** @lends module:client/relatives_metrics */
    'methods' : {
        /**
         * Load new data.
         *
         * Display new data after the user navigated to a different passage.
         *
         * @param {Object} passage - The new passage
         */
        load_passage () {
            const vm = this;
            const requests = [
                vm.get (`manuscript-full.json/${vm.pass_id}/id${vm.ms_id}`),
            ];
            if (vm.ms_id !== 2) {
                requests.push (vm.get (`manuscript-full.json/${vm.pass_id}/id${vm.mt_id}`));
            }

            Promise.all (requests).then ((responses) => {
                vm.ms = responses[0].data.data;
                if (responses.length > 1) {
                    vm.mt = responses[1].data.data;
                } else {
                    vm.mt = null;
                }
            });
        },
    },
    mounted () {
        this.load_passage ();
    },
};
</script>
