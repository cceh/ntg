<template>
  <div class="vm-alert">
    <div v-if="visible" class="alert alert-dismissible" :class="'alert-' + category" role="alert">
      <button type="button" class="close" data-dismiss="alert" aria-label="Close"
              @click="on_close"><span aria-hidden="true">&times;</span></button>
      <div v-html="message" />
    </div>
  </div>
</template>

<script>
/**
 * Display an auto-closing alert window.
 */

import tools from 'tools';

export default {
    'data' : function () {
        return {
            'message'  : '',
            'category' : '',
            'visible'  : false,
        };
    },
    'methods' : {
        show (message, category, timeout = 5000) {
            const vm = this;
            vm.category = (category === 'error') ? 'danger' : category;
            vm.message  = message;
            vm.timeout  = timeout;
            vm.visible  = true;

            vm.$nextTick (() => {
                tools.slide_fade_in (vm.$el).then (() => {
                    vm.$emit ('open', vm.id);
                    vm.timeout_id = setTimeout (vm.on_close, vm.timeout);
                });
            });
        },
        on_close () {
            // called by user click or timeout
            const vm = this;
            clearTimeout (vm.timeout_id);
            vm.$emit ('closing', vm.id);
            vm.$el.velocity ({ 'height' : 0 }).then (() => {
                vm.visible = false;
                vm.$emit ('closed', vm.id);
            });
        },
    },
};
</script>

<style lang="scss">
/* widgets/alert.vue */
@import "bootstrap-custom";

div.vm-alert {
    height: 0;
    overflow: hidden;

    .alert {
        margin-bottom: 0;
    }
}

</style>
