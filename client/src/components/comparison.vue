<template>
  <div class="comparison_vm want_hashchange"
       @hashchange="on_hashchange" @caption="on_caption">
    <page-header :caption="caption" />

    <div class="container bs-docs-container">

      <div class="navigator">
        <form class="form-inline" @submit.prevent="submit">

          <div class="input-group">
            <div class="input-group-prepend">
              <span class="input-group-text">Witness 1:</span>
            </div>
            <input id="ms1" v-model="input1" type="text" class="form-control"
                   title="Enter the Gregory-Aland no. of the first witness ('A' for the initial text)."
                   aria-label="Witness 1" />
          </div>

          <div class="input-group">
            <div class="input-group-prepend">
              <span class="input-group-text">Witness 2:</span>
            </div>
            <input id="ms2" v-model="input2" type="text" class="form-control"
                   title="Enter the Gregory-Aland no. of the second witness ('A' for the initial text)."
                   aria-label="Witness 2" />
          </div>

          <button type="submit" data="Go" class="btn btn-primary"
                  title="Start the comparison.">Go</button>

        </form>
      </div>

      <card :caption="caption" cssclass="card-comparison">
        <comparison-table :ms1="ms1" :ms2="ms2" />
      </card>

    </div>
  </div>
</template>

<script>
/**
 * Comparison of 2 witnesses.  This module shows a table with a global
 * comparison of two witnesses: in how many passages do they differ, how many
 * are older / younger? There is also a drill-down table for each range with
 * more detail about the differing passages.
 *
 * @component comparison
 * @author Marcello Perathoner
 */

import $ from 'jquery';
import Vue from 'vue';

import tools from 'tools';

import comparison_table from 'comparison_table.vue';

Vue.component ('comparison-table', comparison_table);

export default {
    data () {
        return {
            'ms1'     : { 'hs' : '-' },
            'ms2'     : { 'hs' : '-' },
            'input1'  : '',
            'input2'  : '',
            'caption' : 'Comparison of Witnesses',
        };
    },
    'methods' : {
        submit (dummy_event) {
            window.location.hash = '#' + $.param ({
                'ms1' : this.input1,
                'ms2' : this.input2,
            });
        },
        on_caption (event) {
            this.caption = event.detail.data;
        },
        on_hashchange () {
            const hash = window.location.hash ? window.location.hash.substring (1) : '';
            if (hash) {
                const vm = this;
                const params = tools.deparam (hash);
                const requests = [
                    vm.get ('manuscript.json/' + params.ms1),
                    vm.get ('manuscript.json/' + params.ms2),
                ];

                Promise.all (requests).then ((responses) => {
                    vm.ms1 = responses[0].data.data;
                    vm.ms2 = responses[1].data.data;
                    vm.input1 = vm.ms1.hs;
                    vm.input2 = vm.ms2.hs;
                });
            } else {
                // reset data
                Object.assign (this.$data, this.$options.data.call (this));
            }
        },
    },
    mounted () {
        this.on_hashchange ();
    },
};
</script>

<style lang="scss">
/* comparison.vue */
@import "bootstrap-custom";

div.comparison_vm {
    div.navigator {
        margin-bottom: $spacer;

        form.form-inline {
            /* make button same height as inputs */
            align-items: stretch;
        }

        .input-group {
            margin-right: ($spacer * 0.5);
        }

        input[type=text] {
            width: 6em;
        }

        @media print {
            display: none;
        }
    }
}
</style>
