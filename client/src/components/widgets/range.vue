<template>
  <div class="range-vm btn-group btn-group-sm toolbar-range" role="group">
    <button type="button" :title="title"
            class="btn btn-primary dropdown-toggle dropdown-toggle-range"
            data-toggle="dropdown" aria-haspopup="true" aria-expanded="false">
      <slot></slot>
      <span class="btn_text">{{ value }}</span> <span class="caret" />
    </button>
    <div class="dropdown-menu dropdown-menu-range">
      <div class="btn-group btn-group-sm">
        <button v-for="range in dd_range" :key="range.range" :data-range="range.value"
                type="radio" data-type="dropdown" class="btn btn-primary btn-range"
                @click="on_dropdown_click (range.value, $event)">{{ range.range }}</button>
      </div>
    </div>
  </div>
</template>

<script>
/**
 * A navigator for ranges (like chapters).
 *
 * It triggers a 'range' custom event with the range as parameter.
 *
 * @component range
 * @author Marcello Perathoner
 */

import $ from 'jquery';
import 'bootstrap';

export default {
    'props' : {
        'default' : { // the default reading
            'type'    : String,
            'default' : 'All',
        },
        'prefix'  : { // special ranges to add before the actual ranges, eg. 'this'
            'type'    : Array,
            'default' : function () { return [{ 'range' : 'This', 'value' : 'this' }] },
        },
        'suffix'  : { // special ranges to add before the actual ranges, eg. 'this'
            'type'    : Array,
            'default' : function () { return [] },
        },
        'eventname' : {
            'type'    : String,
            'default' : 'range',
        },
        'title' : {
            'type'    : String,
            'default' : 'Select a chapter.',
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
        ranges () {
            return this.$store.state.ranges || [];
        },
        dd_range () {
            return this.prefix.concat (this.ranges).concat (this.suffix);
        },

    },
    'watch' : {
        value (newVal, oldVal) {
            if (newVal !== oldVal || newVal !== this.value) {
                this.$forceUpdate ();
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
            if (data === 'this') {
                data = this.$store.state.passage.chapter;
            }
            this.change (data);
        },
        on_submit () {
        },
    },
    mounted () {
        $ (this.$el).find ('.dropdown-toggle').dropdown ();
    },
};
</script>

<style lang="scss">
/* range.vue */
@import "bootstrap-custom";

.range-vm {
    @media print {
        display: none;
    }

    /* make buttons the same height as inputs */
    align-items: stretch;

    div.dropdown-menu.dropdown-menu-range {
        button.btn {
            min-width: 3rem;
        }
    }
}
</style>
