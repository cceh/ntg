<template>
  <div class="labezator_vm want_hashchange form-inline"
       @hashchange="on_hashchange">
    <button :data-labez="labez" type="button"
            class="btn btn-primary dropdown-toggle dropdown-toggle-labez bg_labez"
            data-toggle="dropdown" aria-haspopup="true" aria-expanded="false">
      Labez:
      <span class="btn_text">{{ labez }}</span> <span class="caret" />
    </button>

    <div class="dropdown-menu dropdown-menu-labez">
      <div class="btn-group btn-group-sm">
        <button v-for="[labez, labez_i18n] in readings"
                :key="labez" :data-labez="labez"
                type="radio" data-type="dropdown"
                class="btn btn-primary btn-labez bg_labez"
                @click="on_dropdown_click (labez, $event)">{{ labez_i18n }}</button>
      </div>
    </div>
  </div>
</template>

<script>
/**
 * A navigator for labez.
 *
 * It triggers a 'labezator' custom event with the labez as parameter.
 *
 * @component labezator
 * @author Marcello Perathoner
 */

import $ from 'jquery';
import 'bootstrap';

import tools from 'tools';

export default {
    'data' : function () {
        return {
            'labez' : 'a',
        };
    },
    'computed' : {
        readings () {
            // FIXME: filter zu
            return this.$store.state.passage.readings || [['none', '-']];
        },
    },
    'watch' : {
        readings () {
            // reset value if reading is not in new passage
            const mapped_readings = this.readings.map (item => item[0]);
            if (this.labez && !mapped_readings.includes (this.labez)) {
                this.change (mapped_readings[0]);
            }
        },
    },
    'methods' : {
        change (labez) {
            this.$trigger ('labezator', labez);
        },
        on_dropdown_click (data, event) {
            const $dropdown = $ (event.target).closest ('.dropdown-menu').parent ().find ('[data-toggle="dropdown"]');
            $dropdown.dropdown ('toggle');
            this.change (data);
        },
        on_submit () {
        },
        on_hashchange () {
            // update control if hash changes
            const hash = window.location.hash.substring (1);
            if (hash) {
                const params = tools.deparam (hash);
                if ('labez' in params) {
                    this.labez = params.labez;
                }
            } else {
                this.labez = 'a';
            }
        },
    },
    mounted () {
        $ (this.$el).find ('.dropdown-toggle').dropdown ();
        // On first page load simulate user navigation to hash.
        this.on_hashchange ();
    },
};
</script>

<style lang="scss">
/* labezator.vue */
@import "bootstrap-custom";

.labezator_vm {
    @media print {
        display: none;
    }

    margin-left: $spacer;
    margin-bottom: $spacer;

    /* make buttons the same height as inputs */
    align-items: stretch;

    div.dropdown-menu {
        border: 0;
        padding: 0;
        background: transparent;
        min-width: 20rem;

        div.btn-group {
            flex-wrap: wrap;
        }

        button.btn {
            min-width: 2rem;
        }
    }
}
</style>
