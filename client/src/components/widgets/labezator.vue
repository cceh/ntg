<template>
  <div class="vm-labezator vm-dropdown-mixin dropdown btn-group b-dropdown">
    <button ref="toggle" size="sm" variant="primary" role="group" type="button" :title="title"
            class="btn btn-sm btn-primary dropdown-toggle bg_labez" :data-labez="value"
            aria-haspopup="true" :aria-expanded="visible"
            @click="toggle" @keydown="toggle">
      <slot></slot>
      <span class="btn_text">{{ value }}</span> <span class="caret" />
    </button>

    <div ref="menu" class="dropdown-menu" tabindex="-1" @keydown="onKeydown">
      <div v-if="visible" class="btn-group btn-group-sm">
        <button v-for="labez in readings" :key="labez.labez" :data-labez="labez.labez"
                type="radio" tabindex="0"
                class="btn btn-primary btn-labez bg_labez"
                @click="on_item_click (labez.labez, $event)">{{ labez.labez_i18n }}</button>
      </div>
    </div>
  </div>
</template>

<script>
/**
 * A navigator for labez.
 *
 * @component client/widgets/labezator
 * @author Marcello Perathoner
 */

import dropdown_mixin from 'widgets/dropdown_mixin.vue';

export default {
    'props' : {
        'value' : {  // v-model
            'type'     : String,
            'required' : true,
        },
        'pass_id' : {
            'type'     : Number,
            'required' : true,
        },
        // special readings to add before and after the actual readings, eg. 'All'
        'prefix'  : {
            'type'    : Array,
            'default' : [],
        },
        'suffix' : {
            'type'    : Array,
            'default' : [],
        },
        'reduce' : {
            'type'    : String,
            'default' : null,
        },
        'title' : {
            'type'    : String,
            'default' : 'Select a variant.',
        },
    },
    'mixins' : [dropdown_mixin],
    'data'   : function () {
        return {
            'readings' : [],
        };
    },
    'watch' : {
        pass_id (new_pass_id) {
            this.load_labez (new_pass_id);
        },
    },
    'methods' : {
        load_labez (pass_id) {
            const vm = this;
            if (pass_id > 0) {
                const requests = [
                    vm.get ('readings.json/' + pass_id),
                ];

                Promise.all (requests).then ((responses) => {
                    const readings = responses[0].data.data;
                    vm.readings = vm.prefix
                        .concat (readings.filter (d => d.labez !== 'zu'))
                        .concat (vm.suffix);

                    // reset value if reading is not in new passage
                    if (vm.reduce !== null) {
                        const mapped_readings = vm.readings.map (item => item.labez);
                        if (vm.value && !mapped_readings.includes (vm.value)) {
                            vm.$emit ('input', vm.reduce);
                        }
                    }
                });
            } else {
                vm.readings = [];
            }
        },
    },
    mounted () {
        this.load_labez (this.pass_id);
    },
};
</script>

<style lang="scss">
/* widgets/labezator.vue */

div.vm-labezator {
    .dropdown-menu {
        min-width: 4rem;
        width: max-content;
        max-width: 20rem;
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
