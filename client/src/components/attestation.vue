<template>
  <div class="attestation_vm want_hashchange"
       @hashchange="on_hashchange"
       @navigator.prevent="on_navigator"
       @labezator.prevent="on_labezator">
    <page-header :caption="caption" />

    <div class="container bs-docs-container">

      <div class="d-flex">
        <navigator ref="nav" />
        <labezator />
      </div>

      <div class="card">
        <div class="card-header">{{ msg }}
          <ul class="list-inline">
            <li v-for="ms in ms_list" :key="ms.ms_id" @click="scroll_to ('id' + ms.ms_id)">{{ ms.hs }}. </li>
          </ul>
        </div>
        <div class="card-header d-print-none">
          <toolbar :toolbar="relatives_toolbar" />
        </div>
      </div>

      <div class="columns">
        <card v-for="ms in ms_list" :key="ms.ms_id" :id="'id' + ms.ms_id" cssclass="card-attestation">
          <relatives :ms_id="ms.ms_id" :toolbar="relatives_toolbar" />
        </card>
      </div>

    </div>
  </div>
</template>

<script>
/**
 * Show all manuscripts with a certain attestation at a certain passage.
 *
 * Internally uses a list of <relatives> and a <toolbar>.
 *
 * @component attestation
 * @author Marcello Perathoner
 */

import { mapGetters } from 'vuex';
import $ from 'jquery';
import Vue from 'vue';
import csv_parse from 'csv-parse/lib/sync';

import d3common  from 'd3_common';
import tools     from 'tools';

import navigator from 'navigator.vue';
import labezator from 'labezator.vue';
import toolbar   from 'toolbar.vue';
import relatives from 'relatives.vue';

Vue.component ('navigator', navigator);
Vue.component ('labezator', labezator);
Vue.component ('toolbar',   toolbar);
Vue.component ('relatives', relatives);

export default {
    data () {
        return {
            'labez'             : 'a',
            'pass_id'           : 1,
            'ms_list'           : [],
            'relatives_toolbar' : {
                'type'                  : 'rel',
                'range'                 : 'All',
                'limit'                 : '10',
                'include'               : [],
                'fragments'             : [],
                'mode'                  : 'sim',
                'labez'                 : 'all+lac',
                'labez_dropdown_prefix' : [['all', 'All']],
                'labez_dropdown_suffix' : [['all+lac', 'All+Lac']],
            },
        };
    },
    'computed' : {
        'caption' : function () {
            return `Manuscripts attesting '${this.labez}' at ${this.passage ? this.passage.hr : ''}`;
        },
        'msg' : function () {
            return `There are ${this.ms_list.length} manuscripts attesting '${this.labez}'
                    at ${this.passage ? this.passage.hr : ''}: `;
        },
        ...mapGetters ([
            'passage',
        ]),
    },
    'methods' : {
        set_hash () {
            const hash = window.location.hash ? window.location.hash.substring (1) : '';
            const params = tools.deparam (hash);
            params.pass_id = this.pass_id;
            params.labez = this.labez;
            window.location.hash = '#' + $.param (params);
        },
        on_navigator (event) {
            this.pass_id = event.detail.data;
            this.set_hash ();
        },
        on_labezator (event) {
            this.labez = event.detail.data;
            this.set_hash ();
        },
        on_hashchange () {
            const params = tools.deparam (window.location.hash.substring (1));
            const vm = this;
            if ('labez' in params) {
                vm.labez = params.labez;
            }
            if ('pass_id' in params) {
                vm.pass_id = params.pass_id;
                // the <relatives> component reads the passage from the store so
                // we need to set it for it.
                // delete all cards first or set_passage () will reload all cards
                vm.ms_list = [];
                vm.$refs.nav.set_passage (params.pass_id);

                const requests = [
                    vm.get ('attesting/' + params.pass_id + '/' + params.labez),
                ];

                Promise.all (requests).then ((responses) => {
                    vm.ms_list = csv_parse (responses[0].data, { 'columns' : true });
                });
            }
        },
        /**
         * Scroll to the manuscript.
         *
         * @method goto_manuscript
         */
        scroll_to (href) {
            $ ('html, body').animate ({
                'scrollTop' : $ ('#' + href).offset ().top,
            }, 500);
        },

    },
    mounted () {
        // insert css for color palettes
        d3common.insert_css_palette (d3common.generate_css_palette (
            d3common.labez_palette,
            d3common.cliques_palette
        ));

        // On first page load simulate user navigation to hash.
        this.on_hashchange ();
    },
};
</script>

<style lang="scss">
/* attestation.vue */
@import "bootstrap-custom";

div.attestation_vm {
    div.columns {
        column-width: 38em;
    }

    div.card-attestation {
        break-inside: avoid;
    }

    ul.list-inline {
        display: inline;

        li {
            display: inline;
        }
    }
}
</style>
