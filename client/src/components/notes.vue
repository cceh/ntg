<template>
  <div class="vm-notes card-slidable">
    <div class="card-header">
      <toolbar :toolbar="toolbar">
        <b-button-group size="sm">
          <b-button :disabled="!toolbar.save" variant="primary" size="sm" class="d-print-none"
                    @click="toolbar.save ()">Save</b-button>
        </b-button-group>
      </toolbar>
    </div>

    <textarea v-model="current_text" :readonly="!$store.getters.can_write" />

    <alert ref="alert" />
  </div>
</template>

<script>
/**
 * This module implements the editor notes card.
 *
 * @component notes
 * @author Marcello Perathoner
 */

import { BButton }      from 'bootstrap-vue/src/components/button/button';
import { BButtonGroup } from 'bootstrap-vue/src/components/button-group/button-group';

import alert   from 'widgets/alert.vue';
import toolbar from 'widgets/toolbar.vue';
import tools   from 'tools';


export default {
    'props'      : ['pass_id'],
    'components' : {
        'alert'          : alert,
        'b-button-group' : BButtonGroup,
        'b-button'       : BButton,
        'toolbar'        : toolbar,
    },
    'data' : function () {
        return {
            'original_text' : '',
            'current_text'  : '',
            'toolbar'       : {
                'save' : false,
            },
        };
    },
    'watch' : {
        pass_id () {
            this.load_passage ();
        },
        current_text () {
            this.can_save ();
        },
        original_text () {
            this.can_save ();
        },
    },
    'methods' : {
        /**
         * Load a new passage.
         *
         * @function load_passage
         */
        load_passage () {
            const vm = this;
            if (vm.pass_id === 0) {
                return Promise.resolve ();
            }
            const ta = vm.$el.querySelector ('textarea');

            const requests = [
                vm.get ('notes.txt/' + vm.pass_id),
                tools.fade_out (ta).promise,
            ];

            return Promise.all (requests).then ((responses) => {
                vm.current_text  = responses[0].data;
                vm.original_text = vm.current_text;
                vm.$nextTick (() => {
                    tools.slide_fade_in (ta);
                });
            });
        },
        can_save () {
            const vm = this;
            if (vm.$store.getters.can_write && vm.current_text !== vm.original_text) {
                vm.toolbar.save = () => this.on_save ();
            } else {
                vm.toolbar.save = false;
            }
        },
        /**
         * Save an edited passage.
         *
         * @function save_passage
         */
        on_save () {
            const vm = this;

            vm.put ('notes.txt/' + vm.pass_id, { 'remarks' : vm.current_text })
                .then ((response) => {
                    vm.original_text = vm.current_text;
                    vm.$refs.alert.show (response.data.message, 'success', 2000);
                }).catch ((error) => {
                    vm.$refs.alert.show (error.response.data.message, 'error');
                });
        },
    },
    mounted () {
        const vm = this;
        vm.load_passage ();
    },
};
</script>

<style lang="scss">
/* notes.vue */
@import "bootstrap-custom";

.vm-notes {
    textarea {
        display: block;
        width: 100%;
        border: none;
        padding: $card-spacer-x;
    }
}
</style>
