<template>
  <div class="vm-connectivity btn-group btn-group-sm">
    <label class="btn btn-primary d-flex align-items-center" :title="title"> <!-- moz needs align-center -->
      <slot></slot>
      <span class="connectivity-label">{{ connectivity_formatter (val) }}</span>
      <input v-model="val" type="range" class="custom-range"
             min="1" max="21" list="ticks"
             @mouseup="on_mouseup" />

      <!-- ticks are disabled by appearance: none in class custom-range -->
      <datalist id="ticks">
        <option value="1" label="1" />
        <option value="5" label="5" />
        <option value="10" label="10" />
        <option value="15" label="15" />
        <option value="21" label="All" />
      </datalist>
    </label>
  </div>
</template>

<script>
/**
 * The connectivity slider.
 *
 * @component client/widgets/connectivity
 * @author Marcello Perathoner
 */

export default {
    'props' : {
        'value' : {  // v-model
            'type'     : Number,
            'required' : true,
        },
        'title' : {
            'type'    : String,
            'default' : 'Select a connectivity.',
        },
    },
    'data' : function () {
        return {
            'val' : this.value,
        };
    },
    'methods' : {
        connectivity_formatter (s) {
            return (s === '21') ? 'All' : s;
        },
        on_mouseup () {
            this.$emit ('input', Number (this.val));
        },
    },
};
</script>

<style lang="scss">
/* connectivity.vue */
@import "bootstrap-custom";

.vm-connectivity {
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
