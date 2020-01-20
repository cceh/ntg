<template>
  <b-button-toolbar class="vm-toolbar justify-content-between" @ntgclick.native="on_click">
    <slot></slot>
    <div class="mr-auto" />
    <slot name="right"></slot>
  </b-button-toolbar>
</template>

<script>
/**
 * This module implements the toolbar that is on most of the cards.
 *
 * Most of the functionality here resides in widgets.  See the widgets
 * subdirectory.
 *
 * @component client/widgets/toolbar
 *
 * @author Marcello Perathoner
 */

import { BButtonToolbar } from 'bootstrap-vue/src/components/button-toolbar/button-toolbar';


export default {
    'props' : {
        'toolbar' : {
            'type'     : Object,
            'required' : true,
        },
    },
    'components' : {
        'b-button-toolbar' : BButtonToolbar,
    },
    'data' : function () {
        return {
        };
    },
    'methods' : {
        on_click (event) {
            this.toolbar[event.detail.data] ();
        },
    },
};
</script>

<style lang="scss">
/* widgets/toolbar.vue */
@import "bootstrap-custom";

div.vm-toolbar {
    margin-bottom: $spacer * -0.5;
    margin-right: $spacer * -0.5;

    div.btn-group {
        margin-right: $spacer * 0.5;
        margin-bottom: $spacer * 0.5;
    }

    label.btn.active {
        @media print {
            color: black !important;
        }
    }
}
</style>
