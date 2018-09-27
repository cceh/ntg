<template>
  <div class="card-header d-flex justify-content-between">
    <h2 v-html="caption" />
    <div>
      <template v-if="closable">
        <button type="button" class="close" aria-label="Close" @click="close">
          <span class="fas fa-window-close"></span>
        </button>
      </template>
      <template v-if="slidable">
        <button type="button" class="close" aria-label="Maximize" @click="maximize">
          <span class="fas fa-window-maximize"></span>
        </button>
        <button type="button" class="close" aria-label="Minimize" @click="minimize">
          <span class="fas fa-window-minimize"></span>
        </button>
      </template>
    </div>
  </div>
</template>

<script>
/**
 * The card caption with min/max/close buttons.
 *
 * @component card_caption
 * @author Marcello Perathoner
 */

import $ from 'jquery';

export default {
    'data' : function () {
        return {
            'slidable' : false,
            'closable' : false,
        };
    },
    'props'   : ['caption', 'default_closed'],
    'methods' : {
        minimize (dummy_event) {
            this.$card.find ('.card-slidable').slideUp (() => {
                this.card_vm.visible = false;
            });
        },
        maximize (dummy_event) {
            this.card_vm.visible = true;
            this.$card.find ('.card-slidable').slideDown ();
        },
        close (dummy_event) {
            const vm = this;
            vm.$card.fadeOut (() => {
                vm.$trigger ('destroy_relatives_popup', vm.card_vm.card_id);
            });
        },
    },
    mounted () {
        const vm = this;
        vm.card_vm = vm.$parent;

        vm.$card = $ (vm.$el).closest ('.card');

        // if card is closable add the button
        vm.closable = vm.$card.hasClass ('card-closable');

        // if any of our children are slidable add the buttons
        vm.slidable = vm.$card.find ('.card-slidable').length > 0;

        // if card should start closed
        if (vm.default_closed) {
            vm.card_vm.visible = false;
            vm.$nextTick (() => vm.minimize ());
        }
    },
};

</script>

<style lang="scss">
/* card_caption.vue */
@import "bootstrap-custom";

div.card {
    h2 {
        font-size: 1rem;
        margin-bottom: 0;
    }

    .close {
        margin-left: ($spacer * 0.25);
        font-size: 1rem;

        @media print {
            display: none;
        }
    }
}
</style>
