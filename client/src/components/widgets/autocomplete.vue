<template>
  <div class="vm-autocomplete vm-dropdown-mixin dropdown b-dropdown input-group input-group-sm">
    <input ref="toggle"
           v-model="val" :title="title" :name="name"
           class="form-control dropdown-toggle" type="text"
           aria-haspopup="true" aria-expanded="false"
           @click="toggle"
           @focusout="on_focusout"
           @input="on_input"
           @keydown="on_keydown" />
    <div ref="menu" class="dropdown-menu" @keydown="onKeydown">
      <table v-if="visible" class="table table-sm">
        <tbody>
          <tr v-for="(s, index) in suggestions" :key="s.value" role="menuitem"
              class="dropdown-item" :class="{ 'active' : index === active_item_index }"
              @click="on_item_click (s.value.toString (), $event)">
            <td>{{ s.label }}</td>
            <td>{{ s.description }}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script>
/**
 * An autocomplete dropdown.
 *
 * The difference between a normal dropdown and this is that we have an input
 * control instead of a button, and we always keep the focus on the input and
 * never give it to the menu.
 *
 * @component client/widgets/autocomplete
 * @author Marcello Perathoner
 */

import dropdown_mixin from 'widgets/dropdown_mixin.vue';
import KeyCodes       from 'bootstrap-vue/src/utils/key-codes';


export default {
    'props' : {
        'value' : {
            'type'     : String,  // v-model
            'required' : true,
        },
        'name' : {
            'type'     : String,  // the field name eg. chapter, verse, word
            'required' : true,
        },
        'more_params' : {
            'type'     : Object,  // params to add to the suggestion.json call
            'required' : true,
        },
        'title' : String,
    },
    'mixins' : [dropdown_mixin],
    'data'   : function () {
        return {
            'val'               : this.value,  // what the input showns
            'suggestions'       : [],
            'active_item_index' : 0,
        };
    },
    'watch' : {
        value (new_value) {
            this.val = new_value;  // v-model update from parent
        },
    },
    'methods' : {
        clip_active_item_index () {
            const vm = this;
            vm.active_item_index = Math.max (Math.min (vm.active_item_index, vm.suggestions.length - 1), 0);
        },
        load_suggestions (term) {
            const vm = this;
            const params = { ... vm.more_params };
            params.currentfield = vm.name;
            params.term = term;
            const requests = [
                vm.get ('suggest.json', { 'params' : params }),
            ];
            return Promise.all (requests).then ((responses) => {
                vm.suggestions = responses[0].data;
                vm.clip_active_item_index ();
            });
        },
        on_show () {
            const vm = this;
            vm.load_suggestions (vm.val).then (() => {
                vm.active_item_index = 0;
                if (vm.suggestions[0]) {
                    vm.val = vm.suggestions[0].value.toString ();
                }
            });
        },
        on_input () {
            // called every time the input value changes
            const vm = this;
            if (vm.visible) {
                // keep the suggestions current when the user is typing in the
                // input while the dropdown is open
                vm.load_suggestions (vm.val);
            }
        },
        on_keydown (event) {
            const vm = this;
            if (!vm.visible) {
                vm.toggle (event);
            } else {
                const key = event.keyCode;
                if (key === KeyCodes.UP || key === KeyCodes.DOWN) {
                    if (key === KeyCodes.UP) {
                        --vm.active_item_index;
                    } else {
                        ++vm.active_item_index;
                    }
                    vm.clip_active_item_index ();
                    if (vm.suggestions[vm.active_item_index]) {
                        vm.val = vm.suggestions[vm.active_item_index].value.toString ();
                    }
                    return;
                }
                if (key === KeyCodes.ESC) {
                    vm.hide ();
                }
                if (key === KeyCodes.ENTER) {
                    vm.on_item_enter (vm.val, event);
                }
            }
        },
        on_focusout () {
            this.emit_data (this.val);
        },
        focusMenu () {
            // this overrides the base class: we always keep the focus on the input
        },
    },
};
</script>

<style lang="scss">
/* widgets/autocomplete.vue */
@import "bootstrap-custom";

div.vm-autocomplete {
    .form-control {
        margin-left: -$input-border-width;
    }

    .dropdown-menu {
        padding: 0;
        min-width: 2rem;

        tr {
            padding: 0 $btn-padding-x;

            &.active {
                color: $dropdown-link-active-color;
                background: $dropdown-link-active-bg;
            }

            td {
                border-top: 0;
                white-space: nowrap;

                &:first-child {
                    width: 1%;
                }
            }
        }
    }
}
</style>
