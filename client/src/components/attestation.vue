<template>
  <div class="attestation_vm">
    <page-header :caption="caption" />

    <div class="container bs-docs-container">

      <navigator ref="nav" param="pass_id" />

      <labezator param="labez" />

      <div class="mb-3">{{ msg }}
        <ul class="list-inline">
          <li v-for="ms in ms_list" :key="ms.ms_id" @click="scroll_to ('id' + ms.ms_id)">{{ ms.hs }}. </li>
        </ul>
      </div>

      <div class="columns">
        <card v-for="ms in ms_list" :caption="caption" :key="ms.ms_id" cssclass="card-attestation" :id="'id' + ms.ms_id">
          <relatives :ms_id="ms.ms_id" />
        </card>
      </div>

    </div>
  </div>
</template>

<script>
/**
 * Show all manuscripts witha certain attestation at a certain passage.
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
import relatives from 'relatives.vue';

Vue.component ('navigator', navigator);
Vue.component ('labezator', labezator);
Vue.component ('relatives', relatives);

export default {
    data () {
        return {
            'labez' : '',
            'ms_list' : [],
        };
    },
    'computed' : {
        'caption' : function () {
            return `Manuscripts attesting '${this.labez}' at ${this.passage ? this.passage.hr : ''}`;
        },
        'msg' : function () {
            return `There are ${this.ms_list.length} manuscripts attesting '${this.labez}' at ${this.passage ? this.passage.hr : ''}: `;
        },
        ...mapGetters ([
            'passage',
        ]),
    },
    'methods' : {
        on_hashchange () {
            const hash = window.location.hash.substring (1);
            if (hash) {
                const vm = this;
                const params = tools.deparam (hash);
                this.labez = params.labez;
                // the relatives component reads the passage from the store
                vm.$refs.nav.set_passage (params.pass_id);
                const requests = [
                    vm.get ('attesting/' + params.pass_id + '/' + params.labez),
                ];

                Promise.all (requests).then ((responses) => {
                    vm.ms_list = csv_parse (responses[0].data, { 'columns' : true });
                });
            } else {
                // reset data
                Object.assign (this.$data, this.$options.data.call (this));
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
        const vm = this;

        // insert css for color palettes
        d3common.insert_css_palette (d3common.generate_css_palette (
            d3common.labez_palette,
            d3common.cliques_palette
        ));


        $ (window).off ('hashchange.attestation');
        $ (window).on ('hashchange.attestation', function () {
            vm.on_hashchange ();
        });

        // On first page load simulate user navigation to hash.
        vm.on_hashchange ();
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
