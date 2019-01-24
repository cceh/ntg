<template>
  <div class="connectivity-vm btn-group btn-group-sm" role="group" data-toggle="buttons">

    <label class="btn btn-primary d-flex align-items-center" :title="title"> <!-- moz needs align-center -->
      <slot></slot>
      <span class="connectivity-label">{{ connectivity_formatter (value) }}</span>
      <input v-model="value" type="range" class="custom-range" min="1" max="21"
             @change="on_change" />
      <datalist id="ticks" style="display: none;">
        <option value="1" label="1" />
        <option value="5" label="5" />
        <option value="10" label="10" />
        <option value="20" label="20" />
        <option value="21" label="All" />
      </datalist>
    </label>
  </div>
</template>

<script>
/**
 * The connectivity slider.
 *
 * It triggers a 'connectivity' custom event with the selected connectivity as a
 * parameter.
 *
 * @component connectivity
 * @author Marcello Perathoner
 */

import $ from 'jquery';
import 'bootstrap';

export default {
    'props' : {
        'default' : { // the default reading
            'type'    : Number,
            'default' : 5,
        },
        'eventname' : {
            'type'    : String,
            'default' : 'connectivity',
        },
        'title' : {
            'type'    : String,
            'default' : 'Select a connectivity.',
        },
        'value' : {
            'type'     : Number,
            'required' : true,
        },
    },
    'data' : function () {
        return {
        };
    },
    'watch' : {
        value (newVal, oldVal) {
            if (newVal !== oldVal || newVal !== this.value) {
                this.$forceUpdate ();
            }
        },
    },
    'methods' : {
        connectivity_formatter (s) {
            return (s === '21') ? 'All' : s;
        },
        change (value) {
            this.$trigger (this.eventname, value);
            this.$emit ('input', value);  // makes it work with v-model
        },
        on_change (event) {
            this.change (event.target.value);
        },
        on_submit () {
        },
    },
    mounted () {
    },
};
</script>

<style lang="scss">
/* connectivity.vue */
@import "bootstrap-custom";

.connectivity-vm {
    @media print {
        display: none;
    }

    /* make buttons the same height as inputs */
    align-items: stretch;

    label {
        margin-bottom: 0;

        span.connectivity-label {
            display: inline-block;
            width: 1.5em;
            text-align: right;
        }
    }

    input[type="range"] {
        width: 12em;
        padding-left: ($spacer * 0.5);
        padding-right: ($spacer * 0.5);
    }
}
</style>
