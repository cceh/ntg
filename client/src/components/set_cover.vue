<template>
  <div class="set_cover_vm want_hashchange" @hashchange="on_hashchange">

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
        <div class="card-header">
          <toolbar :toolbar="toolbar">
            <button-group type="checkbox" v-model="toolbar.include"
                          :options="options.include" />
          </toolbar>
        </div>

        <table class="table table-bordered table-sm table-hover table-set-cover" cellspacing="0">
          <thead>
            <tr>
              <th class="n"
                  title="Index No.">No.</th>

              <th class="hs"
                  title="The ancestor">Ancestor</th>

              <th class="equals"
                  title="Number of variants explained by agreement with the ancestor.">Equal</th>

              <th class="post"
                  title="Number of variants not explained by agreement but by posteriority.">Post</th>

              <th class="unknown"
                  title="Cases of unknown source variant.">Unknown</th>

              <th class="open"
                  title="Number of variants not explained by any ancestor.">Total Open</th>

              <th class="explained"
                  title="Number of variants explained by one of the ancestors.">Total Explained</th>
            </tr>
          </thead>
          <tbody>
            <template v-for="r in cover">
              <tr :data-ms-id="r.ms_id" :key="r.ms_id" @click="on_click (r.cumsum_hs)">
                <td class="n">{{ r.n }}</td>
                <td class="hs">{{ r.hs }}</td>
                <td class="equal">{{ r.equal }}</td>
                <td class="post">{{ r.post }}</td>
                <td class="unknown">{{ r.unknown }}</td>
                <td class="open">{{ r.open }}</td>
                <td class="explained">{{ r.explained }}</td>
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

import tools from 'tools';
import { options } from 'widgets/options';

export default {
    data () {
        return {
            'ms'      : { 'hs' : '-' },
            'mss'     : [],
            'input1'  : '',
            'input2'  : '',
            'cover'   : [],
            'options'      : options,
            'toolbar' : {
                'include' : [],
            }
        };
    },
    'computed' : {
        'caption' : function () { return `Minimum Set Cover for Witness ${this.ms.hs} (${this.ms.open})` ; }
    },
    'watch' : {
        'toolbar' : {
            handler () {
                this.load_set_cover ();
            },
            'deep' : true,
        },
    },
    'methods' : {
        submit (dummy_event) {
            window.location.hash = '#' + $.param ({
                'ms'         : this.input1,
                'pre_select' : this.input2,
            });
        },
        on_click (cumsum) {
            const vm = this;
            vm.$router.push ({
                name : 'opt_stemma',
                hash : '#' + $.param ({
                    'ms'        : vm.ms.hs,
                    'selection' : cumsum,
                })
            });
        },
        load_set_cover () {
            const vm = this;
            const params = {
                'ms'         : vm.input1,
                'pre_select' : vm.input2,
                'include'    : vm.toolbar.include,
            };
            const requests = [
                vm.get ('set-cover.json/' + params.ms + '?' + $.param (params)),
            ];

            Promise.all (requests).then ((responses) => {
                vm.ms     = responses[0].data.data.ms;
                vm.mss    = responses[0].data.data.mss;
                vm.input1 = vm.ms.hs;
                vm.input2 = vm.mss.map (d => d.hs).join (' ');

                let cumsum = [];
                vm.cover = responses[0].data.data.cover.map (function (item) {
                    cumsum.push (item.hs);
                    item.cumsum_hs = cumsum.join (' ');
                    return item;
                });
            });
        },
        on_hashchange () {
            const hash = window.location.hash ? window.location.hash.substring (1) : '';
            if (hash) {
                const data = tools.deparam (hash);
                this.input1 = data.ms;
                this.input2 = data.pre_select;
                this.load_set_cover ();
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
