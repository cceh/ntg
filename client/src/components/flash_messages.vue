<template>
  <div class="vm-flash-messages container bs-docs-container">
    <transition-group name="alerts"
                      tag="div"
                      :css="false"
                      @enter="enter"
                      @leave="leave">
      <div v-for="msg in flashed_messages" :key="msg.id" class="alert-wrap">
        <div class="alert-wrap-inner">
          <div :class="'alert alert-dismissible alert-' + (msg.category === 'error' ? 'danger' : msg.category)"
               role="alert">
            <button type="button" class="close" data-dismiss="alert" aria-label="Close"
                    @click="close_message (msg.id)"><span aria-hidden="true">×</span></button>
            {{ msg.message }}
          </div>
        </div>
      </div>
    </transition-group>
  </div>
</template>

<script>
/**
 * Output the flashed messages.
 *
 * @component flash_messages
 * @author Marcello Perathoner
 */

import axios    from 'axios';
import url      from 'url';


export default {
    data () {
        return {
            'flashed_messages' : [],
            'next_msg_id'      : 1,
        };
    },
    'methods' : {
        close_message (msg_id) {
            const vm = this;
            vm.flashed_messages = vm.flashed_messages.filter ((msg) => msg.id !== msg_id);
        },
        delayed_close_message (msg_id) {
            const vm = this;
            setTimeout (() => vm.close_message (msg_id), 2000);
        },
        get_flashed_messages () {
            const vm = this;
            const requests = [
                /* eslint-disable no-undef */
                axios.get (url.resolve (api_base_url, 'messages.json')),
            ];
            Promise.all (requests).then ((responses) => {
                vm.flashed_messages = responses[0].data.data.messages.map ((msg) => {
                    msg.id = vm.next_msg_id++;
                    vm.delayed_close_message (msg.id);
                    return msg;
                });
            });
        },
        enter (el, done) {
            el.velocity ({ 'opacity' : [1.0, 0.0] }).then (done);
        },
        leave (el, done) {
            el.velocity ({ 'opacity' : [0.0, 1.0] }).velocity ({ 'height' : '0px' }).then (done);
        },
    },
    created () {
        const vm = this;
        vm.get_flashed_messages ();
    },
};

</script>

<style lang="scss">
/* flash_messages.vue */
@import "bootstrap-custom";

div.vm-flash-messages {
    margin-top: 0;
    margin-bottom: 0;

    .alert-wrap {
        margin: 0;

        .alert-wrap.inner {
            padding-top: $alert-padding-y;

            .alert {
                margin: 0;
            }
        }
    }
}
</style>
