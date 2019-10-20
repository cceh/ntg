<template>
  <div class="vm-relatives"
       @dragover.prevent="on_dragover"
       @drop.prevent="on_drop"
       @destroy_relatives_popup="on_destroy_relatives_popup ($event, $event.detail.data)">

    <card v-for="card in floating_cards" :key="card.id"
          :card_id="card.id" :position_target="card.position_target"
          class="card-floating">
      <relatives-table :pass_id="pass_id" :ms_id="card.ms_id" />
    </card>
  </div>
</template>

<script>

import card            from 'widgets/card.vue';
import relatives_table from 'relatives_table.vue';


export default {
    'props' : {
        'pass_id' : Number,
    },
    'components' : {
        'card'            : card,
        'relatives-table' : relatives_table,
    },
    'data' : function () {
        return {
            'floating_cards' : [],
            'next_card_id'   : 0,
            'dragging'       : null,
        };
    },
    'methods' : {
        on_dragover (event) {
            if (this.dragging) {
                this.dragging.vm.on_dragover (event, this.dragging);
            }
        },
        on_drop (event) {
            if (this.dragging) {
                this.dragging.vm.on_drop (event, this.dragging);
            }
            this.dragging = null;
        },
        /**
         * Create a new popup managed by the relatives module.
         *
         * We have to create these dynamically because there may be many open at once.
         *
         * @function create_relatives_popup
         *
         * @param {integer} ms_id - The manuscript id
         * @param {HTMLElement} target - An element. The popup will be positioned relative to this element.
         */
        create_relatives_popup (ms_id, target) {
            this.next_card_id += 1;
            this.floating_cards.push ({
                'id'              : this.next_card_id,
                'ms_id'           : parseInt (ms_id, 10),
                'position_target' : target,
            });
        },
        on_destroy_relatives_popup (event, card_id) {
            if (card_id === 0) {
                this.floating_cards = [];
            } else {
                this.floating_cards = this.floating_cards.filter (item => item.id !== card_id);
            }
        },
    },
    created () {
        const vm = this;

        // install event handlers

        document.addEventListener ('click', (event) => {
            const ms_id = event.target.getAttribute ('data-ms-id')
                  // the data is on SVG g.node not on circle
                  || event.target.parentNode.getAttribute ('data-ms-id');
            if (ms_id) {
                vm.create_relatives_popup (ms_id, event.target);
            }
        });
    },
};

</script>

<style lang="scss">
/* relatives.vue */
@import "bootstrap-custom";

div.vm-relatives {
    position: relative;
    height: 0;

    .card-floating {
        position: fixed;
        z-index: 10;
        width: min-content;
    }

    div.relatives-scroller {
        resize: both;
        min-width: 32em;
        min-height: 2em;
        max-height: 50em;
        overflow-y: scroll;
    }
}

</style>
