<template>
  <div :class="'card ' + cssclass">
    <card-caption :caption="current_caption" :default_closed="default_closed" />

    <slot v-if="visible" />
  </div>
</template>

<script>
/**
 * This module is the base for a card.
 *
 * @component card
 * @author Marcello Perathoner
 */

import $ from 'jquery';
import 'jquery-ui/draggable.js';

import 'jquery-ui-css/draggable.css';

export default {
    'props' : ['cssclass', 'caption', 'default_closed', 'card_id', 'position_target'],
    'data'  : function () {
        return {
            'current_caption' : this.caption,
            'draggable'       : false,
            'visible'         : true,
        };
    },
    'methods' : {
        /**
         * Position the card relative to target.
         *
         * Target usually is the element that the user clicked to create the popup.
         *
         * @function position
         *
         * @param {DOM} target - A DOM element relative to which to position the popup.
         */
        position (target) {
            const rect = target.getBoundingClientRect ();
            const bodyRect = document.body.getBoundingClientRect (); // account for scrolling
            let event = new $.Event ('click');
            event.pageY = rect.top  - bodyRect.top  + (rect.height / 2.0);
            event.pageX = rect.left - bodyRect.left + (rect.width / 2.0);
            $ (this.$el).position ({
                'my'        : 'center bottom-15',
                'collision' : 'flipfit flip',
                'of'        : event,
            });
        },
        set_caption (new_caption) {
            this.current_caption = new_caption;
        },
    },
    mounted () {
        this.$card = $ (this.$el);

        // if card is draggable make it so
        this.draggable = this.$card.hasClass ('card-draggable');
        if (this.draggable) {
            $ (this.$el).draggable ();
        }

        // position floating card relative to target
        if (this.position_target) {
            this.position (this.position_target);
        }
    },
};
</script>

<style lang="scss">
/* card.vue */
@import "bootstrap-custom";

div.card {
    min-width: 100%;
    margin-bottom: $spacer;
}
</style>
