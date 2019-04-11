<template>
  <div class="set_cover_vm want_hashchange"
       @hashchange="on_hashchange" @caption="on_caption">
    <page-header :caption="caption" />

    <div class="container bs-docs-container">

      <div class="navigator">
        <form class="form-inline" @submit.prevent="submit">

          <div class="input-group">
            <div class="input-group-prepend">
              <span class="input-group-text">Witness:</span>
            </div>
            <input id="ms" v-model="input1" type="text" class="form-control"
                   title="Enter the Gregory-Aland-No. of the witness."
                   aria-label="Witness" />
          </div>

          <div class="input-group">
            <div class="input-group-prepend">
              <span class="input-group-text">Pre-Select:</span>
            </div>
            <input id="pre" v-model="input2" type="text" class="form-control"
                   title="Enter a space-separated list of witnesses to pre-select into the set cover."
                   aria-label="Pre-Select" />
          </div>

          <button type="submit" data="Go" class="btn btn-primary"
                  title="Find the set cover.">Go</button>

        </form>
      </div>

      <card :caption="caption" cssclass="card-set-cover">

        <table class="table table-bordered table-sm table-hover table-set-cover" cellspacing="0">
          <thead>
            <tr @click="on_sort">
              <th class="details-control" />

              <th class="n" data-sort-by="n"
                  title="Index No.">No.</th>

              <th class="hs" data-sort-by="hs"
                  title="The ancestor">Ancestor</th>

              <th class="equals" data-sort-by="equals"
                  title="Number of variants explained by agreement with the ancestor.">Equal</th>

              <th class="post" data-sort-by="post"
                  title="Number of variants not explained by agreement but by posteriority.">Post</th>

              <th class="unknown" data-sort-by="unknown"
                  title="Cases of unknown source variant.">Unknown</th>

              <th class="open" data-sort-by="open"
                  title="Number of variants not explained by any ancestor.">Total Open</th>

              <th class="explained" data-sort-by="explained"
                  title="Number of variants explained by one of the ancestors.">Total Explained</th>
            </tr>
          </thead>
          <tbody>
            <template v-for="r in cover">
              <tr :data-ms-id="r.ms_id" :key="r.ms_id">
                <td class="details-control" @click="toggle_details_table (r)" />

                <td class="n">{{ r.n }}</td>

                <td class="hs">{{ r.hs }}</td>

                <td class="equal">{{ r.equal }}</td>
                <td class="post">{{ r.post }}</td>
                <td class="unknown">{{ r.unknown }}</td>
                <td class="open">{{ r.open }}</td>
                <td class="explained">{{ r.explained }}</td>
              </tr>
              <tr v-if="r.child" :data-range="r.range" :key="r.rg_id + '_child'" class="child" >
                <td />
                <td colspan="99">
                  <set-cover-details-table :ms="ms" :range="r.range" />
                </td>
              </tr>
            </template>
          </tbody>
        </table>
      </card>

    </div>
  </div>
</template>

<script>
/**
 * Find the minimum set cover of ancestors for any descendant.
 *
 * See: Presentation 485ff
 *
 * @component set_cover
 * @author Marcello Perathoner
 */

import $ from 'jquery';
import Vue from 'vue';

import { sort_mixin } from 'comparison_details_table.vue';

import tools from 'tools';

export default {
    data () {
        return {
            'ms'      : { 'hs' : '-' },
            'mss'     : [],
            'input1'  : '',
            'input2'  : '',
            'cover'   : [],
        };
    },
    'mixins' : [sort_mixin],
    'computed' : {
        'caption' : function () { return `Minimum Set Cover for Witness ${this.ms.hs} (${this.ms.open})` ; }
    },
    'methods' : {
        submit (dummy_event) {
            window.location.hash = '#' + $.param ({
                'ms'         : this.input1,
                'pre_select' : this.input2,
            });
        },
        on_caption (event) {
            // this.caption = event.detail.data;
        },
        on_hashchange () {
            const hash = window.location.hash ? window.location.hash.substring (1) : '';
            if (hash) {
                const vm = this;
                const params = tools.deparam (hash);
                const requests = [
                    vm.get ('set-cover.json/' + params.ms + '?' + $.param (params)),
                ];

                Promise.all (requests).then ((responses) => {
                    vm.ms     = responses[0].data.data.ms;
                    vm.mss    = responses[0].data.data.mss;
                    vm.input1 = vm.ms.hs;
                    vm.input2 = vm.mss.map (d => d.hs).join (' ');
                    vm.cover  = responses[0].data.data.cover;
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
/* set_cover.vue */
@import "bootstrap-custom";

div.set_cover_vm {
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
        #pre {
            width: 12em;
        }

        @media print {
            display: none;
        }
    }
}
</style>
