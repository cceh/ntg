<template>
  <textarea class="panel-slidable" @input="changed" />
</template>

<script>
/**
 * This module implements the editor notes panel.
 *
 * @module notes
 * @author Marcello Perathoner
 */

import { mapGetters } from 'vuex';
import $     from 'jquery';
import tools from 'tools';

export default {
    'data' : function () {
        return {
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
    },
    'methods' : {
        /**
         * Load a new passage.
         *
         * @function load_passage
         */
        load_passage () {
            const vm = this;
            const $ta = vm.$textarea;
            const old_height = tools.save_height ($ta);

            const xhr = vm.get ('notes.txt/' + vm.passage.pass_id);
            const p2 = $ta.animate ({ 'opacity' : 0.0 }, 300).promise ();

            return Promise.all ([xhr, p2]).then (function (p) {
                $ta.val (p[0].data);
                vm.original_text = $ta.val ();
                tools.slide_from ($ta, old_height);
                vm.changed ();
            });
        },

        /**
         * Save an edited passage.
         *
         * @function save_passage
         */
        save_passage () {
            const vm = this;

            const xhr = vm.put ('notes.txt/' + vm.passage.pass_id, { 'remarks' : vm.$textarea.val () });
            xhr.then ((dummy_response) => {
                vm.original_text = vm.$textarea.val ();
                vm.changed ();
                tools.xhr_alert (xhr, vm.$wrapper);
            });
        },
        changed () {
            const vm = this;
            vm.$save_button.prop ('disabled', vm.original_text === vm.$textarea.val ());
        },
    },
    mounted () {
        const vm = this;
        vm.$panel    = $ (vm.$el).closest ('.panel');
        vm.$wrapper  = $ (vm.$el).closest ('.panel-content');
        vm.$textarea = $ (vm.$el);

        vm.$save_button = vm.$panel.find ('button[name="save"]');
        vm.$save_button.on ('click', () => { vm.save_passage (); });

        vm.load_passage ();
    },
};
</script>

<style lang="less">
@import "@{BS}/variables.less";
@import "@{BS}/mixins.less";

.panel-notes {
    textarea {
        display: block;
        resize: vertical;
        width: 100%;
        max-height: 500px;
        border: none;
        padding: @panel-body-padding;
        border-radius: @border-radius-base;
    }
}
</style>
