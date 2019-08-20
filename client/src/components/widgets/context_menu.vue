<template>
  <table class="dropdown-menu" role="menu" ref="menu">
    <tbody v-for="grp of actions">
      <tr v-for="a in grp" :class="a.class" @click="on_menu_click (a.data, $event)">
        <td class="bg_labez" :data-labez="a.bg"></td>
        <td>{{ a.msg }}</td>
      </tr>
    </tbody>
  </table>
</template>

<script>
/**
 * This module implements a context menu.
 *
 * @component context_menu
 * @author Marcello Perathoner
 */

import $      from 'jquery';
import _      from 'lodash';
import Popper from 'popper.js';

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

/**
 * Position a context menu aside an svg element.
 *
 * We use Popper since jQuery doesn't grok the SVG DOM.
 *
 * @function svg_contextmenu
 *
 * @param {Object} menu   - The menu
 * @param {Object} target - The DOM object to attach the menu to
 */

export function svg_contextmenu (menu, target) {
    const $card = $ (target).closest ('div.card');
    $card.append (menu);

    var popper = new Popper (target, menu, {
        'placement' : 'right-start',
        'modifiers' : {
            'offset' : {
                'offset' : '0,3',
            },
            'flip' : {
                'behavior' : ['right', 'bottom', 'top']
            },
            'preventOverflow' : {
                'boundariesElement' : $card,
            },
        },
    });
}

export default {
    'data'  : function () {
        return {
            'actions' : {},
        };
    },
    'methods' : {
        open (actions, target) {
            const vm = this;
            const $el = $ (vm.$el);
            $el.fadeIn ();
            vm.actions = actions;
            svg_contextmenu ($el, target);
        },
        close () {
            const vm = this;
            $ (vm.$el).fadeOut (function () {
                vm.actions = {};
                vm.$emit ('menu-close');
            });
        },
        on_menu_click (data, event) {
            this.$emit ('menu-click', data);
            this.close ();
        },
    },
};
</script>


<style lang="scss">
/* local_stemma.vue */
@import "bootstrap-custom";

div.card table.dropdown-menu {
    font-size: $font-size-base;
    text-align: left;

    tbody + tbody {
        border-top: $dropdown-border-width solid $dropdown-border-color;
    }

    tr {
        &:hover {
            color: $dropdown-link-active-color;
            background: $dropdown-link-active-bg;
        }
        &.disabled,
        &:disabled {
            color: $dropdown-link-disabled-color;
            pointer-events: none;
            background-color: transparent;
        }
    }

    td {
        padding: 3px 5px;
        &.bg_labez {
            padding: 3px 10px;
        }
    }
}
</style>
