<template>
  <div class="labezator_vm">
    <form class="form-inline" @submit.prevent="on_nav">

      <div class="input-group">
        <div class="input-group-prepend">
          <span class="input-group-text">Labez:</span>
        </div>

        <input v-model="labez" type="text" class="form-control" id="labez"
               title="Enter the Lesartbezeichnung."
               aria-label="Labez" />

        <div class="input-group-btn input-group-append">
          <button type="submit" data="Go" class="btn btn-primary"
                  aria-label="Go" title="Go">
            <span class="fas fa-check" />
          </button>
        </div>
      </div>

    </form>
  </div>
</template>

<script>
/**
 * A navigator for labez.
 *
 * To actually navigate this module changes the hash.
 *
 * @component labezator
 * @author Marcello Perathoner
 */

import $ from 'jquery';

import tools from 'tools';

export default {
    'data' : function () {
        return {
            'labez' : 'a',
        };
    },
    'props' : {
        'param' : { 'default' : 'labez' },      // param name to use in the window hash
    },
    'methods' : {
        /**
         * Answer the user input on the Go button.
         *
         * @function on_nav
         *
         * @param {Object} event - The event
         */
        on_nav (dummy_event) {
            if (this.labez) {
                const hash = window.location.hash.substring (1);
                const params = tools.deparam (hash);
                params[this.param] = this.labez;
                window.location.hash = '#' + $.param (params);
            }
        },
        on_hashchange () {
            this.labez = null;
            const hash = window.location.hash.substring (1);
            if (hash) {
                const params = tools.deparam (hash);
                if ('labez' in params) {
                    this.labez = params.labez;
                }
            }
        },
    },
    /**
     * Initialize the module.
     *
     * @function created
     */
    mounted () {
        const vm = this;

        $ (window).off ('hashchange.labezator');
        $ (window).on ('hashchange.labezator', function () {
            vm.on_hashchange ();
        });

        // On first page load simulate user navigation to hash.
        vm.on_hashchange ();
    },
};
</script>

<style lang="scss">
/* labezator.vue */
@import "bootstrap-custom";

div.labezator_vm {
    @media print {
        display: none;
    }

    form.form-inline {
        margin-bottom: $spacer;
        /* make buttons the same height as inputs */
        align-items: stretch;

        input.form-control {
            text-align: right;
            width: 3.5em;

            &[name=labez] {
                text-align: left;
            }
        }
    }
}
</style>
