<template>
  <div class="notes-vm card-slidable">
    <div class="card-header">
      <toolbar @save="on_save" />
    </div>

    <div class="wrapper notes-wrapper">
      <textarea v-model="current_text" />
    </div>
  </div>
</template>

<script>
/**
 * This module implements the editor notes card.
 *
 * @component notes
 * @author Marcello Perathoner
 */

import $     from 'jquery';
import tools from 'tools';
import { mapGetters } from 'vuex';

export default {
    'data' : function () {
        return {
            'original_text' : '',
            'current_text'  : '',
            'toolbar'       : {
                'save' : false,
            },
        };
    },
    'computed' : {
        ...mapGetters ([
            'passage',
        ]),
    },
    'watch' : {
        passage () {
            this.load_passage ();
        },
        current_text () {
            const vm = this;
            vm.toolbar.save = vm.current_text !== vm.original_text;
        },
        original_text () {
            const vm = this;
            vm.toolbar.save = vm.current_text !== vm.original_text;
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
            if (vm.passage.pass_id === 0) {
                return Promise.resolve ();
            }
            const $ta = vm.$textarea;
            const old_height = tools.save_height ($ta);

            const xhr = vm.get ('notes.txt/' + vm.passage.pass_id);
            const p1 = $ta.animate ({ 'opacity' : 0.0 }, 300).promise ();

            return Promise.all ([xhr, p1]).then (function (p) {
                vm.current_text  = p[0].data;
                vm.original_text = vm.current_text;
                tools.slide_from ($ta, old_height);
            });
        },

        /**
         * Save an edited passage.
         *
         * @function save_passage
         */
        on_save () {
            const vm = this;

            const xhr = vm.put ('notes.txt/' + vm.passage.pass_id, { 'remarks' : vm.current_text });
            xhr.then ((value) => {
                vm.original_text = vm.current_text;
                tools.xhr_alert (value, vm.$wrapper);
            });
            xhr.catch ((reason) => {
                tools.xhr_alert (reason, vm.$wrapper);
            });
        },
    },
    mounted () {
        const vm = this;
        vm.$card     = $ (vm.$el).closest ('.card');
        vm.$wrapper  = $ (vm.$el).find ('.wrapper');
        vm.$textarea = $ (vm.$el).find ('textarea');
        vm.load_passage ();
    },
};
</script>

<style lang="scss">
/* notes.vue */
@import "bootstrap-custom";

.notes-vm {
    textarea {
        display: block;
        resize: vertical;
        width: 100%;
        max-height: 500px;
        border: none;
        padding: $card-spacer-x;
        border-radius: $card-border-radius;
    }
}
</style>
