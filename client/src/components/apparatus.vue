<template>
  <div class="apparatus-vm card-slidable">
    <div class="card-header">
      <toolbar :toolbar="toolbar" />
    </div>

    <ul class="list-group list-group-flush wrapper apparatus-wrapper">
      <li v-for="(items, group) in groups" :key="group" class="list-group-item">
        <h3 class="list-group-item-heading">
          <a :data-labez="items[0].labez" class="apparatus-labez fg_labez"
             @click="goto_attestation (items[0].labez)">{{ items[0].caption }}</a>
        </h3>
        <ul class="list-group-item-text attesting-mss list-inline">
          <li v-for="item in items" :key="item.ms_id">
            <a :data-ms-id="item.ms_id" class="ms">{{ item.hs }}{{ (item.certainty === 1.0) ? '' : '?' }}.</a>
            <span> </span>
          </li>
        </ul>
      </li>
    </ul>
  </div>
</template>

<script>
/**
 * This module displays the apparatus table.  It retrieves the apparatus data in
 * JSON format and builds a list of readings and of the manuscripts that attest
 * that reading.
 *
 * @component apparatus
 * @author Marcello Perathoner
 */

import $ from 'jquery';
import _ from 'lodash';
import { mapGetters } from 'vuex';

import tools from 'tools';

/**
 * Load a new passage.
 *
 * @function
 * @param {Object} passage - The passage to load.
 * @returns {Promise} Promise, resolved when the passage has loaded.
 */
function load_passage (vm, passage) {
    if (passage.pass_id === 0) {
        return Promise.resolve ();
    }

    const xhr = vm.get ('apparatus.json/' + passage.pass_id);
    const p1 = vm.$wrapper.animate ({ 'opacity' : 0.0 }, 300).promise ();

    return Promise.all ([xhr, p1]).then ((responses) => {
        const show_cliques = vm.toolbar.cliques.includes ('cliques');
        const show_ortho   = vm.toolbar.ortho.includes ('ortho');

        let grouper = item => item.labez;
        let caption = item => `${item.labez} ${item.reading}`;

        if (!show_cliques && show_ortho) {
            grouper = item => item.labez + item.suf + item.lesart;
            caption = item => `${item.labez}${item.labezsuf} ${item.lesart}`;
        } else if (show_cliques && !show_ortho) {
            grouper = item => item.labez + item.clique;
            caption = item => `${item.labez}${item.clique} ${item.reading}`;
        } else if (show_cliques && show_ortho) {
            grouper = item => item.labez + item.clique + item.suf + item.lesart;
            caption = item => `${item.labez}${item.labezsuf}${item.clique} ${item.lesart}`;
        }

        const readings = [];
        responses[0].data.data.readings.map (reading => {
            readings[reading.labez] = reading.lesart;
            return false;
        });

        const mss = responses[0].data.data.manuscripts.map ((ms) => {
            ms.reading  = readings[ms.labez];
            ms.lesart   = ms.lesart || '';
            ms.suf      = (ms.labezsuf === '') ? ' ' : ms.labezsuf;
            ms.group    = grouper (ms);
            ms.caption  = caption (ms);
            return ms;
        });

        // save current height of card
        const old_height = tools.save_height (vm.$wrapper);

        // group manuscripts and loop over groups
        vm.groups = _.groupBy (_.sortBy (mss, 'group'), 'group');

        vm.$nextTick (function () {
            tools.slide_from (vm.$wrapper, old_height);
        });
    });
}

export default {
    'data' : function () {
        return {
            'toolbar' : {
                'cliques'        : [],  // Show readings or cliques.
                'ortho'          : [],  // Show orthographic variations.
                'find_relatives' : this.find_relatives,
            },
            'groups' : [],
        };
    },
    'computed' : {
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
    },
    'methods' : {
        load_passage () {
            return load_passage (this, this.passage);
        },

        /**
         * Show the attestation in the "Coherence in Attestations" card and scroll to it.
         *
         * @method goto_attestation
         */
        goto_attestation (labez) {
            this.$trigger ('goto_attestation', labez);
        },
        find_relatives () {
            this.$router.push (`attestation#pass_id=${this.passage.pass_id}&labez=a`);
        },
    },
    mounted () {
        this.$card    = $ (this.$el).closest ('.card');
        this.$wrapper = $ (this.$el).find ('.wrapper');
        this.load_passage ();
    },
};
</script>

<style lang="scss">
/* apparatus.vue */
@import "bootstrap-custom";

div.apparatus-vm {
    a:not([href]):not([tabindex]) {
        color: var(--primary);
        cursor: pointer;

        &:hover {
            text-decoration: underline;
        }
    }

    h3.list-group-item-heading {
        display: inline;
        padding-right: 1em;
        font-size: 1.2rem;
    }

    ul.list-inline {
        display: inline;

        li {
            display: inline;
        }
    }
}
</style>
