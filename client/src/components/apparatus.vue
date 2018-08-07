<template>
  <ul class="panel-content panel-slidable list-group wrapper apparatus-wrapper">
    <li v-for="group in groups" :key="group.group" class="list-group-item">
      <h4 class="list-group-item-heading">
        <a :data-labez="group.labez" class="apparatus-labez fg_labez"
           @click="goto_attestation">{{ group.group }} {{ group.reading }}</a>
      </h4>
      <ul class="list-group-item-text attesting-mss list-inline">
        <li v-for="item in group.items" :key="item.ms_id">
          <a :data-ms-id="item.ms_id" class="ms">{{ item.hs }}{{ (item.certainty === 1.0) ? '' : '?' }}.</a>
        </li>
      </ul>
    </li>
  </ul>
</template>

<script>
/**
 * This module displays the apparatus table.  It retrieves the apparatus data in
 * JSON format and builds a list of readings and of the manuscripts that attest
 * that reading.
 *
 * @module apparatus
 * @author Marcello Perathoner
 */

import { mapGetters } from 'vuex';
import $ from 'jquery';
import _ from 'lodash';
import tools from 'tools';

/**
 * Load a new passage.
 *
 * @function load_passage
 *
 * @param {Object} passage - Which passage to load.
 *
 * @return {Promise} Promise, resolved when the new passage has loaded.
 */
function load_passage (vm, passage) {
    if (passage.pass_id === 0) {
        return Promise.resolve ();
    }

    const xhr = vm.get ('apparatus.json/' + passage.pass_id);
    const p2 = vm.$wrapper.animate ({ 'opacity' : 0.0 }, 300).promise ();

    return Promise.all ([xhr, p2]).then ((p) => {
        // select a grouping function
        const labez_grouper  = (g) => g.labez;
        const clique_grouper = (g) => g.labez_clique;
        const grouper = vm.$parent.toolbar.cliques.includes ('cliques') ? clique_grouper : labez_grouper;

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

        // save current height of panel
        const $wrapper = vm.$wrapper;
        const old_height = tools.save_height ($wrapper);

        // update
        vm.groups = new_groups;

        vm.$nextTick (function () {
            tools.slide_from ($wrapper, old_height);
        });
    });
}

export default {
    'data' : function () {
        return {
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
    },
    'methods' : {
        load_passage () {
            return load_passage (this, this.passage);
        },

        /**
         * Show the attestation in the Coherence panel and scroll to it.
         *
         * @function goto_attestation
         *
         * @param {Object} event - The event
         */
        goto_attestation (event) {
            event.stopPropagation ();
            const panel = this.$parent.$parent.$refs.ltpanel;
            const labez = $ (event.currentTarget).attr ('data-labez');
            panel.toolbar.labez = labez;
            panel.get_view_vm ().load_passage ();

            $ ('html, body').animate ({
                'scrollTop' : $ ('div.panel-local-textflow').offset ().top,
            }, 500);
        },
    },
    created () {
        this.$parent.toolbar = {
            'cliques' : [],  // Show readings or cliques.
        };
    },
    mounted () {
        this.$wrapper = $ (this.$el.closest ('.panel-content'));
        this.load_passage ();
    },
};
</script>

<style lang="less">
ul.apparatus-wrapper {
    font-size: smaller;

    h4.list-group-item-heading {
        display: inline;
    }

    ul.list-group-item-text {
        display: inline;
        padding-left: 2em;
    }
}

a.apparatus-labez {
    cursor: pointer;
}
</style>
