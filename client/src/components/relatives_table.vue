<template>
  <div class="vm-relatives-table">
    <card-caption :draggable="!external_toolbar" :closable="!external_toolbar">
      <span v-html="caption" />
    </card-caption>

    <div class="card-slidable">
      <div v-if="!external_toolbar" class="card-header">
        <toolbar :toolbar="toolbar">
          <button-group v-model="toolbar.type" type="radio" :options="options.type" />
          <button-group v-model="toolbar.limit" type="radio" :options="options.limit" />
          <labezator v-model="toolbar.labez" :pass_id="pass_id" v-bind="options.labez_all">
            Variant:
          </labezator>
          <range v-model="toolbar.rg_id" :pass_id="pass_id">
            Chapter:
          </range>
          <button-group v-model="toolbar.include" type="checkbox" :options="options.include" />
          <button-group v-model="toolbar.fragments" type="checkbox" :options="options.fragments" />
          <button-group v-model="toolbar.mode" type="radio" :options="options.mode" />
          <button-group slot="right" :options="options.csv" />
        </toolbar>
      </div>

      <div class="card-header">
        <relmetrics :pass_id="pass_id" :ms_id="ms_id"></relmetrics>
      </div>

      <div class="relatives-scroller">
        <table class="table table-sm table-bordered table-sortable table-relatives">
          <thead>
            <tr @click="on_sort">
              <th class="ms" data-sort-by="hsnr"
                  title="Witness 2: Witnesses compared to W1">W2</th>
              <th class="rank" data-sort-by="rank_sort"
                  title="Ancestral rank according to the degree of agreement (Perc)">NR</th>
              <th class="direction" data-sort-by="direction"
                  title="Genealogical direction, potential ancestors indicated by “>”">D</th>
              <th class="labez" data-sort-by="labez"
                  title="The reading offered by W2">Rdg</th>
              <th class="perc" data-sort-by="perc"
                  title="Percentaged agreement of W1 and W2 at the variant passages attested by both (Pass)">Perc</th>
              <th class="equal" data-sort-by="equal"
                  title="Number of agreements of W1 and W2 at the variant passages attested by both (Pass)">Eq</th>
              <th class="common" data-sort-by="common"
                  title="Total number of passages where W1 and W2 are both extant">Pass</th>
              <th class="newer" data-sort-by="newer"
                  title="Number of variants in W2 that are prior to those in W1">W1&lt;W2</th>
              <th class="older" data-sort-by="older"
                  title="Number of variants in W1 that are prior to those in W2">W1&gt;W2</th>
              <th class="unclear" data-sort-by="unclear"
                  title="Number of variants where no decision has been made about priority">Uncl</th>
              <th class="norel" data-sort-by="norel"
                  title="Number of passages where the respective variants are unrelated">NoRel</th>
              <th class="d-print-none"
                  title="Open Manuscripts Comparison view"></th>
              <th class="d-print-none"
                  title="Open Optimal Substemma view"></th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(r, index) in rows" :key="r.ms_id" :data-labez="r.labez"
                :data-ms1-id="ms_id" :data-ms2-id="r.ms_id" class="fg_labez comparison">
              <th class="ms"><span :data-ms-id="r.ms_id" class="ms hilite-target">{{ r.hs }}</span></th>
              <td class="rank">{{ r.rank }}</td>
              <td class="direction">{{ r.direction }}</td>
              <td class="labez">{{ r.labez }}</td>
              <td class="perc">{{ r.perc }}%</td>
              <td class="equal">{{ r.equal }}</td>
              <td class="common">{{ r.common }}</td>
              <td class="newer">{{ r.newer }}</td>
              <td class="older">{{ r.older }}</td>
              <td class="unclear">{{ r.unclear }}</td>
              <td class="norel">{{ r.norel }}</td>
              <td class="compare d-print-none" :title="`Compare ${ms.hs} and ${r.hs}`"
                  @click.stop="on_compare (r.ms_id)">
                <span class="fas fa-balance-scale"></span>
              </td>
              <td v-if="index < 15" class="opt_stemma d-print-none"
                  :title="`Find Optimal Substemma for ${ms.hs} using ${get_first_n_mss (index)}`"
                  @click.stop="on_opt_stemma (index)">
                <span class="fas fa-sitemap"></span>
              </td>
              <td v-else="" class="d-print-none"></td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script>
/**
 * This module implements the table in the relatives popup.
 *
 * @component client/relatives_table
 *
 * @author Marcello Perathoner
 */

import csv_parse  from 'csv-parse/lib/sync';

import button_group from 'widgets/button_group.vue';
import card_caption from 'widgets/card_caption.vue';
import labezator    from 'widgets/labezator.vue';
import range        from 'widgets/range.vue';
import relmetrics   from 'relatives_metrics.vue';
import sort_mixin   from 'table_sort_mixin.vue';
import toolbar      from 'widgets/toolbar.vue';
import tools        from 'tools';
import { options }  from 'widgets/options';


const CAPTIONS = {
    'rel' : 'Relatives for',
    'anc' : 'Ancestors for',
    'des' : 'Descendants for',
};

export default {
    'props' : {
        'pass_id'          : Number,
        'ms_id'            : Number,
        'external_toolbar' : {
            'type'    : Object,
            'default' : null,
        },
    },
    'mixins' : [sort_mixin],
    data () {
        return {
            'rows'      : [],
            'ms'        : {},
            'sorted_by' : 'perc',
            'options'   : options,
            'toolbar'   : this.external_toolbar || this.get_toolbar (),
        };
    },
    'components' : {
        'button-group' : button_group,
        'card-caption' : card_caption,
        'labezator'    : labezator,
        'range'        : range,
        'relmetrics'   : relmetrics,
        'toolbar'      : toolbar,
    },
    'computed' : {
        caption () {
            if (!this.ms.ms_id) {
                return '';
            }
            return `${CAPTIONS[this.toolbar.type]} <span class="ms">W1:</span>
                <span class="fg_labez" data-labez="${this.ms.labez}"><span
                      class="ms hilite-source" data-ms-id="${this.ms.ms_id}">${this.ms.hs}</span>
                (<span class="labez">${this.ms.labez}</span>) ${this.ms.length}</span>`;
        },
    },
    'watch' : {
        pass_id () {
            this.load_passage ();
        },
        'toolbar' : {
            handler () {
                this.load_passage ();
            },
            'deep' : true,
        },
    },
    /** @lends module:client/relatives_table */
    'methods' : {
        /**
         * Load new data.
         *
         * Display new data in the table after the user navigated to a different
         * passage.
         */
        load_passage () {
            const vm = this;
            // vm.rows = [];

            const requests = [
                vm.get (`manuscript-full.json/${vm.pass_id}/id${vm.ms_id}`),
                vm.get (this.build_url ('relatives.csv')),
            ];
            Promise.all (requests).then ((responses) => {
                vm.ms = responses[0].data.data;
                if (vm.ms.certainty < 1.0) {
                    vm.ms.labez = 'zw ' + vm.ms.labez;
                }
                const records = csv_parse (responses[1].data, { 'columns' : true });
                vm.rows = records.map ((d) => {
                    return {
                        'rank'      : +d.rank || '',
                        'rank_sort' : +d.rank || 9999,
                        'ms_id'     : +d.ms_id,
                        'hs'        : d.hs,
                        'hsnr'      : +d.hsnr,
                        'length'    : +d.length,
                        'common'    : +d.common,
                        'equal'     : +d.equal,
                        'older'     : +d.older,
                        'newer'     : +d.newer,
                        'unclear'   : +d.unclear,
                        'norel'     : +d.norel,
                        'direction' : d.direction,
                        'affinity'  : +d.affinity,
                        'labez'     : parseFloat (d.certainty) === 1.0 ? d.labez : 'zw ' + d.labez,
                        'perc'      : (100.0 * d.equal / d.common).toFixed (2),
                    };
                });
            });
        },
        on_opt_stemma (index) {
            const vm = this;
            window.open (
                vm.$router.resolve ({
                    'name' : 'opt_stemma',
                    'hash' : '#' + tools.param ({
                        'ms'        : vm.ms.hs,
                        'selection' : vm.get_first_n_mss (index),
                    }),
                }).href, '_blank'
            ).focus ();
        },
        on_compare (ms_id) {
            const vm = this;
            window.open (
                vm.$router.resolve ({
                    'name' : 'comparison',
                    'hash' : '#' + tools.param ({
                        'ms1' : 'id' + vm.ms.ms_id,
                        'ms2' : 'id' + ms_id,
                    }),
                }).href, '_blank'
            ).focus ();
        },
        get_toolbar () {
            return {
                'type'      : 'rel',
                'rg_id'     : this.$store.state.current_application.rg_id_all || 0,
                'labez'     : 'all+lac',
                'limit'     : '0',
                'include'   : [],
                'fragments' : [],
                'mode'      : 'sim',
                'csv'       : () => this.download ('relatives.csv'),
            };
        },
        get_first_n_mss (n) {
            return this.rows.slice (0, n + 1).map (r => r.hs).join (' ');
        },
        build_url (page) {
            const vm = this;
            return `${page}/${vm.pass_id}/id${vm.ms_id}?` + tools.param (vm.toolbar, [
                'type', 'rg_id', 'limit', 'labez', 'mode', 'include', 'fragments',
            ]);
        },
        download (page) {
            window.open (this.build_full_api_url (this.build_url (page), '_blank'));
        },
    },
    mounted () {
        this.load_passage ();
    },
};
</script>

<style lang="scss">
/* relatives_table.vue */

div.vm-relatives-table {
    span.ms {
        font-weight: bold;
    }

    table.table-relatives {
        width: 100%;
        margin-bottom: 0;
        border-width: 0;

        th {
            padding-left: 1em;
        }

        th,
        td {
            text-align: right;

            &:last-child {
                padding-right: 1em;
            }

            &.ms {
                text-align: left;
            }

            span.fas {
                color: var(--green);
            }
        }
    }
}
</style>
