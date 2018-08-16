<template>
  <div class="apparatus-vm card-slidable">
    <div class="card-header">
      <toolbar />
    </div>

    <ul class="list-group list-group-flush wrapper apparatus-wrapper">
      <li v-for="group in groups" :key="group.group" class="list-group-item">
        <h3 class="list-group-item-heading">
          <a :data-labez="group.labez" class="apparatus-labez fg_labez"
             @click="goto_attestation">{{ group.group }} {{ group.reading }}</a>
        </h3>
        <ul class="list-group-item-text attesting-mss list-inline">
          <li v-for="item in group.items" :key="item.ms_id">
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

    return Promise.all ([xhr, p1]).then ((p) => {
        // select a grouping function
        const labez_grouper  = (g) => g.labez;
        const clique_grouper = (g) => g.labez_clique;
        const grouper = vm.toolbar.cliques.includes ('cliques') ? clique_grouper : labez_grouper;

        // load readings into a dictionary for faster lookup
        const readings = [];
        _.forEach (p[0].data.data.readings, (reading) => {
            readings[reading.labez] = reading.lesart;
        });

        // group manuscripts and loop over groups
        const new_groups = [];
        _.forEach (_.groupBy (_.sortBy (p[0].data.data.manuscripts, grouper), grouper), (items) => {
            new_groups.push ({
                'pass_id'      : passage.pass_id,
                'labez'        : items[0].labez,
                'labez_clique' : items[0].labez_clique,
                'group'        : grouper (items[0]),
                'items'        : items,
                'reading'      : _.get (readings, items[0].labez, 'Error: no reading found'),
            });
        });

        // save current height of card
        const old_height = tools.save_height (vm.$wrapper);

        // update
        vm.groups = new_groups;

        vm.$nextTick (function () {
            tools.slide_from (vm.$wrapper, old_height);
        });
    });
}

export default {
    'data' : function () {
        return {
            'toolbar' : {
                'cliques' : [],  // Show readings or cliques.
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
         * @param {Object} event - The event
         */
        goto_attestation (event) {
            event.stopPropagation ();
            const lt = this.$parent.$parent.$refs.lt;
            const labez = $ (event.currentTarget).attr ('data-labez');
            lt.toolbar.labez = labez;
            lt.load_passage ();

            $ ('html, body').animate ({
                'scrollTop' : $ ('div.card-local-textflow').offset ().top,
            }, 500);
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
