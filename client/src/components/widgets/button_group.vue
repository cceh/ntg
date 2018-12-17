<template>
  <b-button-group size="sm" class="button-group-vm btn-group-toggle btn-group btn-group-sm"
                  :options="options">
    <template v-for="button in buttons">
      <label v-if="type !== 'button'" :key="button.value"
             :class="'btn btn-primary btn-sm' + (is_active (button.value) ? ' active' : '')" :title="button.title">
        <span>{{ button.text }}</span>
        <input :type="type" :checked="is_active (button.value)"
               @change="on_change (button, $event)" />
      </label>
      <button v-if="type === 'button'" :type="type" class="btn btn-primary"
              @click="on_click (button, $event)">{{ button.text }}</button>
    </template>
  </b-button-group>
</template>

<script>
/**
 * A radio or checkbox group.
 *
 * @component button-group
 * @author Marcello Perathoner
 */

import $ from 'jquery';
import _ from 'lodash';
import 'bootstrap';

import tools from 'tools';

export default {
    'props' : {
        'eventname' : {
            'type'    : String,
            'default' : 'button-group',
        },
        'type' : {
            'type'    : String,     // "button", "radio", or "checkbox"
            'default' : 'button',
        },
        'options' : {
            'type'     : Array,
            'required' : true,
        },
        'value' : {
            'type'     : [String, Array],
        },
    },
    'data' : function () {
        return {
            buttons : [],
        };
    },
    'computed' : {
    },
    'watch' : {
        value (newVal, oldVal) {
            if (newVal !== oldVal || newVal !== this.value) {
                this.$forceUpdate ();
            }
        }
    },
    'methods' : {
        on_click (data, event) {
            if (this.type === 'button') {
                this.$parent.$parent.on_click (data.value, event);
            }
        },
        on_change (data, event) {
            if (this.type === 'radio') {
                this.$trigger (this.eventname, data.value);
                this.$emit ('input', data.value);  // makes it work with v-model
            }
            if (this.type === 'checkbox') {
                let a = [];
                if (this.value.includes (data.value)) {
                    a = _.without (this.value, data.value);
                } else {
                    a = a.concat (this.value);
                    a.push (data.value);
                }
                this.$trigger (this.eventname, a);
                this.$emit ('input', a);  // makes it work with v-model
            }
        },
        is_active (value) {
            if (this.type === 'checkbox') {
                return this.value.includes (value);
            }
            return value === this.value;
        },
    },
    mounted () {
        this.buttons = this.options;
    },
};
</script>

<style lang="scss">
/* button-group.vue */
@import "bootstrap-custom";

.button-group-vm {
    @media print {
        display: none;
    }

    /* make buttons the same height as inputs */
    align-items: stretch;
}
</style>
