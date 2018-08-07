<template>
  <div :class="'panel panel-default ' + cssclass">
    <div class="panel-heading panel-caption">
      <template v-if="closable">
        <a class="close panel-close" @click="close"><span class="glyphicon glyphicon-remove" /></a>
      </template>
      <template v-if="slidable">
        <a class="close panel-minimize" @click="minimize"><span class="glyphicon glyphicon-collapse-up" /></a>
        <a class="close panel-maximize" @click="maximize"><span class="glyphicon glyphicon-collapse-down" /></a>
      </template>
      <div v-html="caption" />
    </div>
    <slot v-if="visible" />
  </div>
</template>

<script>
/**
 * This module is the base for a panel.  It implements the minimize, maximize,
 * and close functionality.
 *
 * @module panel
 *
 * @author Marcello Perathoner
 */

import $ from 'jquery';
import 'jquery-ui/draggable.js';
import 'bootstrap';

export default {
    'props' : ['cssclass', 'static_caption', 'name', 'mode', 'default_closed', 'panel_id', 'position_target'],
    'data'  : function () {
        return {
            'slidable'  : false,
            'closable'  : false,
            'draggable' : false,
            'visible'   : true,
            'caption'   : this.static_caption,
            'toolbar'   : {},    // toolbar data
        };
    },
    'methods' : {
        get_toolbar_vm () {
            return this.$children.find (child => { return child.$options.name === 'toolbar'; });
        },
        get_view_vm () {
            // get the view that *defines* the toolbar options, not the toolbar component!
            return this.$children[this.$children.length - 1];
        },
        set_caption (caption) {
            this.caption = caption;
        },
        minimize (dummy_event) {
            this.$panel.find ('.panel-slidable').slideUp (() => {
                this.visible = false;
            });
        },
        maximize (dummy_event) {
            this.visible = true;
            // this.$panel.find ('.panel-slidable').slideDown ();
        },
        close (dummy_event) {
            this.$panel.fadeOut (() => {
                // FIXME this works because currently the relatives popup is the
                // only panel with a close button
                this.$parent.destroy_relatives_popup (this.panel_id);
            });
        },
        /**
         * Position the panel relative to target.
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
    },
    mounted () {
        this.$panel = $ (this.$el);

        // if panel is closable add the button
        this.closable = this.$panel.hasClass ('panel-closable');

        // if any of our children are slidable add the buttons
        this.slidable = this.$panel.find ('.panel-slidable').length > 0;

        // if panel is draggable make it so
        this.draggable = this.$panel.hasClass ('panel-draggable');
        if (this.draggable) {
            $ (this.$el).draggable ();
        }

        // if panel should start closed
        if (this.default_closed) {
            this.visible = false;
        }

        // position floating panel relative to target
        if (this.position_target) {
            this.position (this.position_target);
        }
    },
};
</script>

<style lang="less">
div.panel {
    min-width: 100%;

    a.close {
        padding-left: 4px;
        font-size: 1.1em;
    }
}
</style>
