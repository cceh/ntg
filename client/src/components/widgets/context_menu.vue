<template>
  <div class="vm-context-menu vm-dropdown-mixin dropdown b-dropdown">
    <div ref="menu" class="dropdown-menu" tabindex="-1" @keydown="onKeydown">
      <table v-if="visible" class="table table-sm table-borderless">
        <tbody v-for="(grp, indexg) of items" :key="'grp_' + indexg">
          <tr v-for="(a, index_a) in grp" :key="'a_' + index_a" role="menuitem"
              :class="a.class" class="dropdown-item"
              tabindex="0"
              @keydown="on_item_keydown (a.data, $event)"
              @click="on_item_click (a.data, $event)">
            <td class="bg_labez" :data-labez="a.bg"></td>
            <td>{{ a.msg }}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script>
/**
 * This module implements a context menu.
 *
 * @component context_menu
 * @author Marcello Perathoner
 */

import dropdown_mixin from 'widgets/dropdown_mixin.vue';

export const popper_opts = {
    'placement' : 'right-center',
    'modifiers' : {
        'offset' : {
            'offset' : '0,5',
        },
        'flip' : {
            'behavior' : ['right', 'bottom', 'top'],
        },
    },
};


/**
 * Format message
 *
 * @function mkmsg
 *
 * @param {String} msg    - Message prefix
 * @param {String} labez  - The labez
 * @param {String} clique - The clique
 *
 * @returns {String} The formatted message.
 */

export function mkmsg (msg, labez, clique) {
    return msg + ' ' + labez + (Number (clique) > 1 ? clique : '');
}

export default {
    'props' : {
        'value' : { // no v-model in context_menu
            'required' : false,
        },
        'popperOpts' : {
            'type'    : Object,
            'default' : () => popper_opts,
        },
    },
    'mixins' : [dropdown_mixin],
    'data'   : function () {
        return {
            'items' : {},
        };
    },
    'methods' : {
        open (items, target) {
            this.items = items;
            this.$refs.toggle = target;
            this.show ();
        },
    },
};

</script>


<style lang="scss">
/* widgest/context_menu.vue */
@import "bootstrap-custom";

div.vm-context-menu {
    position: static;

    .dropdown-menu {
        padding: 0;

        table {
            tbody + tbody {
                border-top: $dropdown-border-width solid $dropdown-border-color;
            }

            tr {
                padding: 0;

                &:hover {
                    color: $dropdown-link-hover-color;
                    background: $dropdown-link-hover-bg;
                }

                &.disabled,
                &:disabled {
                    color: $dropdown-link-disabled-color;
                    pointer-events: none;
                    background-color: transparent;
                }
            }

            td {
                border-top: 0;
                white-space: nowrap;

                &.bg_labez {
                    padding: $table-cell-padding-sm 2 * $table-cell-padding-sm;
                }

                &:first-child {
                    width: 1%;
                }
            }
        }
    }
}
</style>
