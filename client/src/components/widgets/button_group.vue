<template>
  <b-button-group size="sm" class="vm-button-group btn-group-toggle btn-group btn-group-sm"
                  :options="options">
    <template v-for="button in options">
      <label v-if="type !== 'button'" :key="button.value"
             :title="button.title"
             class="btn btn-primary" :class="{ 'active' : is_active (button.value) }">
        <span>{{ button.text }}</span>
        <input :type="type" :checked="is_active (button.value)"
               @change="on_change (button, $event)" />
      </label>
      <button v-if="type === 'button'" :key="button.value" :type="type"
              class="btn btn-primary" :title="button.title"
              @click="on_click (button, $event)">{{ button.text }}</button>
    </template>
  </b-button-group>
</template>

<script>
/**
 * A radio or checkbox group.
 *
 * @component client/widgets/button_group
 * @author Marcello Perathoner
 */

import { BButtonGroup } from 'bootstrap-vue/src/components/button-group/button-group';

export default {
    'props' : {
        'value' : {    // v-model
            'type'     : [String, Array],
        },
        'type' : {
            'type'      : String,
            'default'   : 'button',
            'validator' : function (value) {
                return ['button', 'radio', 'checkbox'].includes (value);
            },
        },
        'options' : {
            'type'     : Array,
            'required' : true,
        },
    },
    'components' : {
        'b-button-group' : BButtonGroup,
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
        on_click (data) {
            if (this.type === 'button') {
                this.$trigger ('ntgclick', data.value);
            }
        },
        on_change (data) {
            if (this.type === 'radio') {
                this.$emit ('input', data.value);  // makes it work with v-model
            }
            if (this.type === 'checkbox') {
                let a = this.value.slice ();
                if (this.value.includes (data.value)) {
                    // remove it
                    a = a.filter (d => d !== data.value);
                } else {
                    // add it
                    a.push (data.value);
                }
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
};
</script>

<style lang="scss">
/* button-group.vue */
@import "bootstrap-custom";

.vm-button-group {
    @media print {
        display: none;
    }

    /* make buttons the same height as inputs */
    align-items: stretch;
}
</style>
