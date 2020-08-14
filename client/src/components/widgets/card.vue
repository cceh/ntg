<template>
  <div class="vm-card card" @minimize="on_minimize" @maximize="on_maximize" @close="on_close"
       @dragstart="on_dragstart">
    <slot />
  </div>
</template>

<script>
/**
 * This module is the base for a card.
 *
 * The card may position itself relatively to a target element.
 * The card may be draggable.
 *
 * @component client/widgets/card
 * @author Marcello Perathoner
 */

import tools from 'tools';

import Popper from 'popper.js';

export default {
    'props' : {
        'card_id'         : Number,
        'position_target' : Element,
        'visible'         : {
            'type'    : Boolean,
            'default' : true,
        },
    },
    'data' : function () {
        return {
        };
    },
    'methods' : {
        /**
         * Position the card relative to target.
         *
         * Target usually is the element that the user clicked to create the popup.
         *
         * @param {DOM} target - A DOM element relative to which to position the popup.
         */
        position (target) {
            /* eslint-disable-next-line no-new */
            new Popper (target, this.$el, {
                'placement'     : 'bottom',
                'positionFixed' : true,
                'eventsEnabled' : false,
                'modifiers'     : {
                    'offset' : {
                        'offset' : '0,3',
                    },
                    'flip' : {
                        'behavior' : ['left', 'right', 'top'],
                    },
                    'preventOverflow' : {
                        'boundariesElement' : 'viewport',
                    },
                },
            });
        },
        move (event, data) {
            const style = this.$el.style;
            style.transform = `translate3d(${event.clientX - data.x}px, ${event.clientY - data.y}px, 0px)`;
        },
        on_minimize () {
            const vm = this;
            for (const el of vm.$el.querySelectorAll ('.card-slidable')) {
                tools.slide_fade_out (el);
            }
        },
        on_maximize () {
            const vm = this;
            for (const el of vm.$el.querySelectorAll ('.card-slidable')) {
                tools.slide_fade_in (el, true);
            }
        },
        on_close () {
            const vm = this;
            tools.fade_out (vm.$el).then (() => {
                // FIXME: hardcoded function
                vm.$trigger ('destroy_relatives_popup', vm.card_id);
            });
        },

        /*
         * Use the HTML5 drag and drop protocol to drag the card around.
         *
         * See also: relatives.vue, widgets/card_caption.vue
         */
        on_dragstart (event) {
            // bubbled up from card_caption.vue

            // popperjs uses 'transform: translate3d' to position the element
            const m = [... this.$el.style.transform.matchAll (/(\d+)px/g)];
            const data = {
                'vm'      : this,
                'clientX' : event.clientX,
                'clientY' : event.clientY,
                'left'    : parseInt (m[0][1], 10),
                'top'     : parseInt (m[1][1], 10),
            };

            data.x = data.clientX - data.left;
            data.y = data.clientY - data.top;

            // console.log ('dragstart');
            // console.log (data);

            this.$parent.dragging = data;
            event.dataTransfer.setData ('text', 'dummy');
            event.dataTransfer.effectAllowed = 'none';

            // set empty drag image
            const canvas = document.createElement ('canvas');
            canvas.width = 0;
            canvas.height = 0;
            event.dataTransfer.setDragImage (canvas, 0, 0);
        },

        on_dragenter (event, data) {
            // reflected by relatives.vue
            // console.log ('dragenter');
            this.move (event, data);
        },

        on_dragover (event, data) {
            // reflected by relatives.vue
            // console.log ('dragover');
            this.move (event, data);
        },

        on_drop (event, data) {
            // reflected by relatives.vue
            // console.log ('drop');
            this.move (event, data);
        },
    },
    mounted () {
        const vm = this;

        // position floating card relative to target
        if (vm.position_target) {
            vm.position (vm.position_target);
        }
        if (!vm.visible) {
            for (const el of vm.$el.querySelectorAll ('.card-slidable')) {
                el.style.height = 0;
            }
        }
    },
};
</script>

<style lang="scss">
/* widgets/card.vue */

.vm-card {
    .card-slidable {
        overflow: hidden;
    }
}

</style>
