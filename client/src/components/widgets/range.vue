<template>
  <div class="vm-range vm-dropdown-mixin dropdown btn-group b-dropdown">
    <button ref="toggle" size="sm" variant="primary" role="group" type="button" :title="title"
            class="btn btn-sm btn-primary dropdown-toggle"
            aria-haspopup="true" :aria-expanded="visible"
            @click="toggle" @keydown="toggle">
      <slot></slot>
      <span class="btn_text">{{ id2range (value) }}</span> <span class="caret" />
    </button>

    <div ref="menu" class="dropdown-menu" tabindex="-1" @keydown="onKeydown">
      <div v-if="visible" class="btn-group btn-group-sm">
        <button v-for="range in ranges" :key="range.rg_id" type="radio" tabindex="0"
                :class="{ 'active' : range.rg_id === current_rg_id }"
                class="btn btn-primary btn-range"
                @click="on_item_click (range.rg_id, range.range, $event)">{{ range.range }}</button>
      </div>
    </div>
  </div>
</template>

<script>
/**
 * A navigator for ranges (like chapters).
 *
 * @component client/widgets/range
 * @author Marcello Perathoner
 */

import dropdown_mixin from 'widgets/dropdown_mixin.vue';

export default {
    'props' : {
        'value' : { // v-model
            'type'     : Number,
            'required' : true,
        },
        'pass_id' : {
            'type'     : Number,
            'required' : true,
        },
        'prefix' : { // special ranges to add before the actual ranges, eg. 'this'
            'type'    : Array,
            'default' : function () { return []; },
        },
        'suffix' : { // special ranges to add before the actual ranges, eg. 'this'
            'type'    : Array,
            'default' : function () { return []; },
        },
        'title' : {
            'type'    : String,
            'default' : 'Select a chapter.',
        },
    },
    'mixins' : [dropdown_mixin],
    'data'   : function () {
        return {
            'ranges'        : [],
            'current_rg_id' : 0,
        };
    },
    'methods' : {
        id2range (rg_id) {
            const f = this.ranges.filter (d => d.rg_id === rg_id);
            return f.length ? f[0].range : '';
        },
        load_ranges (pass_id) {
            const vm = this;
            const requests = [vm.get ('ranges.json/')];
            if (pass_id > 0) {
                requests.push (vm.get ('passage.json/' + pass_id));
            }

            Promise.all (requests).then ((responses) => {
                const ranges = responses[0].data.data;
                vm.ranges = vm.prefix.concat (ranges).concat (vm.suffix);
                if (responses.length > 1) {
                    const passage = responses[1].data.data;
                    vm.current_rg_id = passage.rg_id;
                }
            });
        },
        on_show () {
            this.load_ranges (this.pass_id);
        },
    },
    mounted () {
        this.load_ranges (this.pass_id);
    },
};
</script>

<style lang="scss">
/* widgets/range.vue */
@import "bootstrap-custom";

div.vm-range {
    .dropdown-menu {
        width: 20rem;
        padding: 0;

        .btn-group {
            margin: 0;
            display: flex;
            flex-wrap: wrap;
        }

        button {
            min-width: 2rem;
        }
    }
}
</style>
