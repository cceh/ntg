<template>
  <div class="labezator-vm btn-group btn-group-sm">
    <button :data-labez="value" type="button"
            class="btn btn-primary dropdown-toggle dropdown-toggle-labez bg_labez"
            data-toggle="dropdown" aria-haspopup="true" aria-expanded="false">
      <slot></slot>
      <span class="btn_text">{{ value }}</span> <span class="caret" />
    </button>

    <div class="dropdown-menu dropdown-menu-labez">
      <div class="btn-group btn-group-sm">
        <button v-for="labez in readings"
                :key="labez.labez" :data-labez="labez.labez"
                type="radio" data-type="dropdown"
                class="btn btn-primary btn-labez bg_labez"
                @click="on_dropdown_click (labez.labez, $event)">{{ labez.labez_i18n }}</button>
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
    'props' : {
        'default' : { // the default reading
            'type'    : String,
            'default' : 'a',
        },
        'prefix'  : { // special readings to add before the actual readings, eg. 'all'
            'type'    : Array,
            'default' : function () { return [] },
        },
        'suffix'  : { // special readings to add before the actual readings, eg. 'all'
            'type'    : Array,
            'default' : function () { return [] },
        },
        'eventname' : {
            'type'    : String,
            'default' : 'labez',
        },
        'reduce' : {
            'type' :    Boolean,
            'default' : false,
        },
        'value' : {
            'type'     : String,
            'required' : true,
        },
    },
    'data' : function () {
        return {
        };
    },
    'computed' : {
        readings () {
            // FIXME: filter zu
            return this.prefix.concat (this.$store.state.passage.readings || []).concat (this.suffix);
        },
    },
    'watch' : {
        value (newVal, oldVal) {
            if (newVal !== oldVal || newVal !== this.value) {
                this.$forceUpdate ();
            }
        },
        readings () {
            // reset value if reading is not in new passage
            if (this.reduce) {
                const mapped_readings = this.readings.map (item => item.labez);
                if (this.labez && !mapped_readings.includes (this.labez)) {
                    this.change (mapped_readings[0]);
                }
            }
        },
    },
    'methods' : {
        change (value) {
            this.$trigger (this.eventname, value);
            this.$emit ('input', value);  // makes it work with v-model
        },
        on_dropdown_click (data, event) {
            const $dropdown = $ (event.target).closest ('.dropdown-menu').parent ().find ('[data-toggle="dropdown"]');
            $dropdown.dropdown ('toggle');
            this.change (data);
        },
        on_submit () {
        },
    },
    mounted () {
        $ (this.$el).find ('.dropdown-toggle').dropdown ();
        this.change (this.default);
    },
};
</script>

<style lang="scss">
/* labezator.vue */
@import "bootstrap-custom";

.labezator-vm {
    @media print {
        display: none;
    }

    /* make buttons the same height as inputs */
    align-items: stretch;
}
</style>
