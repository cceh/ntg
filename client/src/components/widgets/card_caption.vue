<template>
  <div class="vm-card-caption card-header" :draggable="draggable ? 'draggable' : undefined">
    <div class="d-flex justify-content-between">
      <h2>
        <slot />
      </h2>
      <div>
        <template v-if="closable">
          <button type="button" class="close" aria-label="Close" @click="$trigger ('close')">
            <span class="fas fa-window-close"></span>
          </button>
        </template>
        <template v-if="slidable">
          <button type="button" class="close" aria-label="Maximize" @click="$trigger ('maximize')">
            <span class="fas fa-window-maximize"></span>
          </button>
          <button type="button" class="close" aria-label="Minimize" @click="$trigger ('minimize')">
            <span class="fas fa-window-minimize"></span>
          </button>
        </template>
      </div>
    </div>
  </div>
</template>

<script>
/**
 * The card caption with min/max/close buttons.
 *
 * @component client/widgets/card_caption
 * @author Marcello Perathoner
 */

export default {
    'data' : function () {
        return {
        };
    },
    'props' : {
        'draggable' : {
            'type'    : Boolean,
            'default' : false,
        },
        'slidable' : {
            'type'    : Boolean,
            'default' : true,
        },
        'closable' : {
            'type'    : Boolean,
            'default' : false,
        },
    },
};

</script>

<style lang="scss">
/* widgets/card_caption.vue */
@import "bootstrap-custom.scss";

div.vm-card-caption {
    min-width: max-content;

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
