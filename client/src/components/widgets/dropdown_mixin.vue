<script>
/**
 * A dropdown mixin for the labezator and range components.
 *
 * @component client/widgets/dropdown_mixin
 * @author Marcello Perathoner
 */

import dropdownMixin from 'bootstrap-vue/src/mixins/dropdown';
import KeyCodes      from 'bootstrap-vue/src/utils/key-codes';

import tools from 'tools';

export const popper_opts = {
    'placement' : 'bottom-start',
    'modifiers' : {
        'offset' : {
            'offset' : '0,0',
        },
        'flip' : {
            'behavior' : ['top', 'right', 'left'],
        },
    },
};


export default {
    'props' : {
        'value' : { /* v-model */
            'required' : true,
        },
        'title' : {
            'type'    : String,
            'default' : 'Select',
        },
        'popperOpts' : {
            'type'    : Object,
            'default' : () => popper_opts,
        },
    },
    'mixins' : [dropdownMixin],
    'data'   : function () {
        return {
        };
    },
    'methods' : {
        emit (type, bvEvt) {
            // post events to ourselves first
            if (type === 'show') {
                this.on_show (bvEvt);
            }
            if (type === 'shown') {
                this.on_shown (bvEvt);
            }
            if (type === 'hide') {
                this.on_hide (bvEvt);
            }
            if (type === 'hidden') {
                this.on_hidden (bvEvt);
            }
            // post event to parent, root
            this.$$emit (type, bvEvt);
        },
        emit_data (data) {
            // override this if you want a different event
            this.$emit ('input', data);  // makes it work with v-model, sets value
        },
        on_show () {
            // override this, if you have to call the base class use:
            // dropdown_mixin.methods.on_show.call (this, event);
        },
        on_shown () {
            tools.fade_in (this.$refs.menu);
        },
        on_hide (event) {
            const vm = this;
            if (vm.$refs.menu.style.opacity > 0.0) {
                tools.fade_out (vm.$refs.menu).then (() => {
                    vm.hide ();
                });
                event.preventDefault (); // do not close right now
            }
        },
        on_hidden () {
        },
        on_item_enter (data) {
            this.emit_data (data);
            this.hide (true);
        },
        on_item_click (data) {
            this.emit_data (data);
            this.hide (true);
        },
        on_item_keydown (data, event) {
            const key = event.keyCode;
            if (key === KeyCodes.ENTER) {
                this.on_item_enter (data, event);
            }
        },
    },
    created () {
        this.$$emit = this.$emit;
        this.$emit = this.emit;
    },
};
</script>

<style lang="scss">
/* widgets/dropdown_mixin.vue */
@import "bootstrap-custom";

div.vm-dropdown-mixin {
    position: relative;

    .dropdown-menu {
        display: block;
        opacity: 0;
        font-size: $font-size-base;
    }

    @media print {
        display: none;
    }
}
</style>
