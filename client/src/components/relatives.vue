<template>
  <div class="relatives-vm card-slidable">
    <div class="card-header">
      <relmetrics :ms="ms" />
    </div>

    <div class="scroller">
      <table class="relatives table table-sm">
        <thead>
          <tr>
            <th class="ms"
                title="Witness 2: Witnesses compared to W1">W2</th>
            <th class="rank"
                title="Ancestral rank according to the degree of agreement (Perc)">NR</th>
            <th class="direction"
                title="Genealogical direction, potential ancestors indicated by “>”">D</th>
            <th class="labez"
                title="The reading offered by W2">Rdg</th>
            <th class="perc"
                title="Percentaged agreement of W1 and W2 at the variant passages attested by both (Pass)">Perc</th>
            <th class="equal"
                title="Number of agreements of W1 and W2 at the variant passages attested by both (Pass)">Eq</th>
            <th class="common"
                title="Total number of passages where W1 and W2 are both extant">Pass</th>
            <th class="older"
                title="Number of variants in W2 that are prior to those in W1">W1&lt;W2</th>
            <th class="newer"
                title="Number of variants in W1 that are prior to those in W2">W1&gt;W2</th>
            <th class="unclear"
                title="Number of variants where no decision has been made about priority">Uncl</th>
            <th class="norel"
                title="Number of passages where the respective variants are unrelated">NoRel</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="r in rows" :key="r.ms_id" :data-labez="r.labez"
              :data-ms1-id="ms_id" :data-ms2-id="r.ms_id" class="fg_labez comparison">
            <th class="ms"><span :data-ms-id="r.ms_id" class="ms hilite-target">{{ r.hs }}</span></th>
            <td class="rank">{{ r.rank }}</td>
            <td class="direction">{{ r.direction }}</td>
            <td class="labez">({{ r.labez }})</td>
            <td class="perc">{{ r.perc }}%</td>
            <td class="equal">{{ r.equal }}</td>
            <td class="common">{{ r.common }}</td>
            <td class="older">{{ r.newer }}</td>
            <td class="newer">{{ r.older }}</td>
            <td class="unclear">{{ r.unclear }}</td>
            <td class="norel">{{ r.norel }}</td>
          </tr>
        </tbody>
      </table>
    </div>

  </div>
</template>

<script>
/**
 * This module implements the table in the relatives popup.
 *
 * @component relatives
 *
 * @author Marcello Perathoner
 */

import { mapGetters } from 'vuex';
import $ from 'jquery';
import _ from 'lodash';
import csv_parse from 'csv-parse/lib/sync';

const CAPTIONS = {
    'rel' : 'Relatives for',
    'anc' : 'Ancestors for',
    'des' : 'Descendants for',
};

export default {
    'props' : ['ms_id', 'toolbar'],
    data () {
        return {
            'rows' : [],
            'ms'   : null,
        };
    },
    'computed' : {
        caption () {
            if (!this.ms) {
                return '';
            }
            return `${CAPTIONS[this.toolbar.type]} <span class="ms">W1:</span>
                <span class="fg_labez" data-labez="${this.ms.labez}"><span
                      class="ms hilite-source" data-ms-id="${this.ms.ms_id}">${this.ms.hs}</span>
                (<span class="labez">${this.ms.labez}</span>) ${this.ms.length}</span>`;
        },
        ...mapGetters ([
            'passage',
        ]),
    },
    'watch' : {
        passage () {
            this.load_passage ();
        },
        'toolbar' : {
            handler () {
                this.load_passage ();
            },
            'deep' : true,
        },
        caption () {
            // vue.js `events´ do not bubble, so they are pretty useless
            this.$trigger ('caption', this.caption);
        },
    },
    'methods' : {
        /**
         * Load new data.
         *
         * Display new data in the table after the user navigated to a different
         * passage.
         *
         * @function load_passage
         */
        load_passage () {
            const vm = this;
            vm.rows.length = 0;

            vm.get (`manuscript-full.json/${this.passage.pass_id}/id${this.ms_id}`).then ((response) => {
                vm.ms = response.data.data;
            });

            vm.get (this.build_url ('relatives.csv')).then ((response) => {
                const records = csv_parse (response.data, { 'columns' : true });
                vm.rows = records.map ((d) => {
                    return {
                        'rank'      : +d.rank || '',
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
                        'labez'     : d.labez,
                        'perc'      : (100.0 * d.equal / d.common).toFixed (2),
                    };
                });
            });
        },
        build_url (page) {
            const vm = this;
            const params = _.pick (vm.toolbar, [
                'type', 'range', 'limit', 'labez', 'mode', 'include', 'fragments',
            ]);
            return `${page}/${vm.passage.pass_id}/id${vm.ms_id}?` + $.param (params);
        },
        download (page) {
            window.open (this.build_full_api_url (this.build_url (page), '_blank'));
        },
    },
    mounted () {
        if ('csv' in this.toolbar) {
            this.toolbar.csv = () => this.download ('relatives.csv');
        }
        this.load_passage ();
    },
};
</script>

<style lang="scss">
/* relatives.vue */

div.relatives-vm {
    span.ms {
        font-weight: bold;
    }

    div.scroller {
        max-height: 50em;
        overflow-y: scroll;
    }

    table.relatives {
        margin-bottom: 0;

        th,
        td {
            padding-left: 0;
            padding-right: 0;
            text-align: right;

            &:first-child {
                padding-left: 1em;
            }

            &:last-child {
                padding-right: 1em;
            }

            &.ms {
                text-align: left;
            }
        }
    }
}
</style>
