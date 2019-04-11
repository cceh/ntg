<template>
  <div class="exhaustive_search_vm want_hashchange"
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

      <card :caption="caption" cssclass="card-exhaustive-search">

        <table class="table table-bordered table-sm table-hover table-sortable table-exhaustive-search" cellspacing="0">
          <thead>
            <tr @click="on_sort">
              <th class="details-control" />

              <th class="hs" data-sort-by="mss"
                  title="The combination of ancestors.">Ancestors</th>

              <th class="count" data-sort-by="count"
                  title="Number of ancestors in this combination.">N</th>

              <th class="equal" data-sort-by="equal"
                  title="Number of variants explained by agreement with one of the ancestors.">Equal</th>

              <th class="post" data-sort-by="post"
                  title="Number of variants not explained by agreement but by posteriority.">Post</th>

              <th class="unknown" data-sort-by="unknown"
                  title="Cases of unknown source variant.">Unknown</th>

              <th class="open" data-sort-by="open"
                  title="Cases not explained by this combination of ancestors.">Open</th>

              <th class="hint" data-sort-by="hint"
                  title="Indicates the combination explaining the most variants in the descendant compared with combinations which are equal in number of ancestors.">Hint</th>
            </tr>
          </thead>
          <tbody>
            <template v-for="r in rows">
              <tr>
                <td class="details-control" @click="toggle_details_table (r)" />

                <td class="hs">{{ r.mss }}</td>

                <td class="n">{{ r.count }}</td>

                <td class="equal">{{ r.equal }}</td>
                <td class="post">{{ r.post }}</td>
                <td class="unknown">{{ r.unknown }}</td>
                <td class="open">{{ r.open }}</td>
                <td class="hint">{{ r.hint }}</td>
              </tr>
              <tr v-if="r.child" :data-range="r.range" :key="r.rg_id + '_child'" class="child" >
                <td />
                <td colspan="99">
                  <exhaustive-search-details-table :ms="ms" :range="r.range" />
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
 * Find the optimal substemma of a witness by exhaustive search.
 *
 * See: Presentation 485ff
 *
 * @component exhaustive_search
 * @author Marcello Perathoner
 *
 * 1891 03 5 429 181 2298 04 0120 01
 */

import $ from 'jquery';
import Vue from 'vue';

import { sort_mixin } from 'comparison_details_table.vue';

import tools from 'tools';

/**
 * Row conversion function.  Convert numeric values to numeric types
 * and add calculated fields.
 *
 * @function row_conversion
 *
 * @return The converted row
 */

function row_conversion (d) {
    return {
        'mss'     : d.mss.map (ms => ms.hs).join ('.') + '.',
        'count'   : +d.count,
        'equal'   : +d.equal,
        'post'    : +d.post,
        'unknown' : +d.unknown,
        'open'    : +d.open,
        'hint'    : d.hint ? '<<' : '',
    };
}


export default {
    'mixins' : [sort_mixin],
    data () {
        return {
            'rows'        : [],
            'sorted_by'   : 'equal',
            'sorted_desc' : true,
            'ms'          : { 'hs' : '-' },
            'mss'         : [],
            'input1'      : '',
            'input2'      : '',
        };
    },
    'computed' : {
        'caption' : function () { return `Optimal Substemma for Witness ${this.ms.hs} (${this.ms.open})` ; }
    },
    'methods' : {
        submit (dummy_event) {
            window.location.hash = '#' + $.param ({
                'ms'        : this.input1,
                'selection' : this.input2,
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
                    vm.get ('exhaustive-search.json/' + params.ms + '?' + $.param (params)),
                ];

                Promise.all (requests).then ((responses) => {
                    vm.ms     = responses[0].data.data.ms;
                    vm.mss    = responses[0].data.data.mss;
                    vm.input1 = vm.ms.hs;
                    vm.input2 = vm.mss.map (d => d.hs).join (' ');
                    vm.rows   = responses[0].data.data.cover.map (row_conversion);
                    vm.sort ();
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
/* exhaustive_search.vue */
@import "bootstrap-custom";

div.exhaustive_search_vm {
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

    th[data-sort-by]::after {
        left: auto;
        right: ($spacer * 0.25);
    }
}
</style>
