<template>
  <div class="optimal_substemma_vm want_hashchange"
       @hashchange="on_hashchange" @caption="on_caption">
    <page-header :caption="caption" />

    <div class="container bs-docs-container">

      <div class="navigator">
        <form class="form-inline" @submit.prevent="submit">

          <div class="input-group">
            <div class="input-group-prepend">
              <span class="input-group-text">Descendant:</span>
            </div>
            <input id="ms" v-model="input1" type="text" class="form-control"
                   title="Enter the Gregory-Aland-No. of the descendant witness."
                   aria-label="Descendant" />
          </div>

          <div class="input-group">
            <div class="input-group-prepend">
              <span class="input-group-text">Ancestors:</span>
            </div>
            <input id="selection" v-model="input2" type="text" class="form-control"
                   title="Enter a space-separated list of ancestor witnesses."
                   aria-label="List of Ancestors" />
          </div>

          <button type="submit" data="Go" class="btn btn-primary"
                  title="Do an exhaustive search of all combinations of the ancestors.">Go</button>

        </form>
      </div>

      <card :caption="caption" cssclass="card-optimal-substemma">
        <optimal-substemma-table :ms="ms" :mss="mss" />
      </card>

    </div>
  </div>
</template>

<script>
/**
 * Find the optimal substemma of a witness by exhaustive search.
 *
 * See: Presentation 485ff
 *
 * @component optimal_substemma
 * @author Marcello Perathoner
 *
 * 1891 03 5 429 181 2298 04 0120 01
 */

import $ from 'jquery';
import Vue from 'vue';

import optimal_substemma_table from 'optimal_substemma_table.vue';

import tools from 'tools';

export default {
    'components' : {
        'optimal-substemma-table' : optimal_substemma_table,
    },
    data () {
        return {
            'ms'      : { 'hs' : '-' },
            'mss'     : [],
            'input1'  : '',
            'input2'  : '',
            'caption' : 'Optimal Substemma',
        };
    },
    'methods' : {
        submit (dummy_event) {
            window.location.hash = '#' + $.param ({
                'ms'        : this.input1,
                'selection' : this.input2,
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
                    vm.get ('optimal-substemma.json?' + $.param (params)),
                ];

                Promise.all (requests).then ((responses) => {
                    vm.ms     = responses[0].data.data.ms;
                    vm.mss    = responses[0].data.data.mss;
                    vm.input1 = vm.ms.hs;
                    vm.input2 = vm.mss.map (d => d.hs).join (' ');
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
/* optimal_substemma.vue */
@import "bootstrap-custom";

div.optimal_substemma_vm {
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
        #selection {
            width: 30em;
        }

        @media print {
            display: none;
        }
    }
}
</style>
