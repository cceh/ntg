<template>
  <div class="vm-apparatus card-slidable">
    <div class="card-header">
      <toolbar :toolbar="toolbar">
        <button-group v-model="toolbar.cliques" type="checkbox" :options="options.cliques" />
        <button-group v-model="toolbar.ortho" type="checkbox" :options="options.ortho" />
        <button-group slot="right" :options="options.find_relatives" />
      </toolbar>
    </div>

    <div class="wrapper">
      <ul class="list-group list-group-flush">
        <li v-for="(items, group) in groups" :key="group" class="list-group-item">
          <h3 class="list-group-item-heading">
            <a v-if="items[0].labez[0] !== 'z'" :data-labez="items[0].labez" class="apparatus-labez fg_labez"
               @click="goto_attestation (items[0].labez)">{{ items[0].caption }}</a>
            <span v-else="" :data-labez="items[0].labez"
                  class="apparatus-labez fg_labez">{{ items[0].caption }}</span>
          </h3>
          <ul class="list-group-item-text attesting-mss list-inline">
            <li v-for="item in items" :key="item.ms_id">
              <a :data-ms-id="item.ms_id" class="ms">{{ item.hs }}.</a>
              <span> </span>
            </li>
          </ul>
        </li>
      </ul>
    </div>
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

import { groupBy, sortBy, zip } from 'lodash';

import button_group     from 'widgets/button_group.vue';
import toolbar          from 'widgets/toolbar.vue';
import { options }      from 'widgets/options';
import tools            from 'tools';

/**
 * Load a new passage.
 *
 * @function
 * @param {Number} pass_id - The passage to load.
 * @returns {Promise} Promise, resolved when the passage has loaded.
 */
function load_passage (vm, pass_id) {
    if (pass_id === 0) {
        return Promise.resolve ();
    }

    const wrapper = vm.$el.querySelector ('.wrapper');

    const requests = [
        vm.get ('apparatus.json/' + pass_id),
        tools.fade_out (wrapper).promise,
    ];

    return Promise.all (requests).then ((responses) => {
        const show_cliques = vm.toolbar.cliques.includes ('cliques');
        const show_ortho   = vm.toolbar.ortho.includes ('ortho');

        /* zip ('a/b/c', '1/2/3') => 'a1/b2/c3' */
        function qzip (... args) {
            return zip (... args.map (e => e.split ('/'))).map (e => e.join ('')).join ('/');
        }

        let grouper = item => item.labez;
        let caption = item => item.labez + ' ' + item.reading;

        if (!show_cliques && show_ortho) {
            grouper = item => item.labez + item.labezsuf + item.lesart;
            caption = item => qzip (item.labez, item.labezsuf) + ' ' + item.lesart;
        } else if (show_cliques && !show_ortho) {
            grouper = item => item.labez + item.clique;
            caption = item => qzip (item.labez, item.clique) + ' ' + item.reading;
        } else if (show_cliques && show_ortho) {
            grouper = item => item.labez + item.clique + item.labezsuf + item.lesart;
            caption = item => qzip (item.labez, item.labezsuf, item.clique) + ' ' + item.lesart;
        }

        const manuscripts = responses[0].data.data.manuscripts;

        const readings = new Map (responses[0].data.data.readings.map (
            r => [r.labez, r.lesart]
        ));

        const mss = manuscripts.map (ms => {
            ms.zw      = (ms.certainty < 1.0) ? 'zw ' : '';
            ms.reading = ms.lesart || readings.get (ms.labez);
            ms.lesart  = ms.lesart || '';
            ms.group   = ms.zw + grouper (ms);
            ms.caption = ms.zw + caption (ms);
            ms.labez   = ms.zw + ms.labez;
            return ms;
        });

        // group manuscripts and loop over groups
        vm.groups = groupBy (sortBy (mss, 'group'), 'group');

        vm.$nextTick (() => {
            tools.slide_fade_in (wrapper, true);
        });
    });
}

export default {
    'props'      : ['pass_id', 'epoch'],
    'components' : {
        'toolbar'      : toolbar,
        'button-group' : button_group,
    },
    'data' : function () {
        return {
            'groups'  : [],
            'options' : options,
            'toolbar' : {
                'cliques' : [],  // Show readings or cliques.
                'ortho'   : [],  // Show orthographic variations.
                'rel'     : this.find_relatives,
            },
        };
    },
    'watch' : {
        pass_id () {
            this.load_passage ();
        },
        epoch () {
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
            return load_passage (this, this.pass_id);
        },

        /**
         * Show the attestation in the "Coherence in Attestations" card and scroll to it.
         *
         * @method goto_attestation
         */
        goto_attestation (labez) {
            this.$trigger ('goto_attestation', labez);
        },
        /**
         * Open a page listing all manuscripts.
         */
        find_relatives () {
            this.$router.push ({
                'name' : 'find_relatives',
                'hash' : '#' + tools.param ({
                    'pass_id' : this.pass_id,
                }),
            });
        },
    },
    mounted () {
        this.load_passage ();
    },
};
</script>

<style lang="scss">
/* apparatus.vue */
@import "bootstrap-custom";

div.vm-apparatus {
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
