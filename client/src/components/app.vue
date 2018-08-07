<template>
  <div>
    <div class="bs-docs-header">
      <div class="container">
        <!-- the violet header -->
        <h1>
          <span class="caption">{{ this.$store.state.caption }}</span>
          <span class="appname">{{ this.$store.state.current_application.name }}</span>
        </h1>
      </div>
    </div>

    <div class="container bs-docs-container">
      <div class="clearfix">
        <div v-if="this.$store.state.current_user.is_logged_in" class="pull-right">
          <router-link :to="{ name : 'user.profile' }" class="user_profile_link">
            {{ this.$store.state.current_user.username }}
          </router-link>
          &#xa0; | &#xa0;
          <router-link :to="{ name : 'user.logout' }" class="user_logout_link">Sign out</router-link>
        </div>
      </div>
      <div class="helpmenu">
        <a href="/pdf/GenQ4_Guide.pdf" target="_blank">Short Guide (PDF)</a>
      </div>
      <div class="flashed_messages">
        <!-- container for eventual messages -->
      </div>

      <!-- the component matched by the route will render here -->
      <router-view />
    </div>
  </div>
</template>

<script>
/**
 * The vue.js application
 *
 * @module app
 * @author Marcello Perathoner
 */

import $ from 'jquery';
import Vue from 'vue';
import Vuex from 'vuex';
import url from 'url';

Vue.use (Vuex);

const store = new Vuex.Store ({
    'state' : {
        'caption'   : 'ntg',
        'ranges'    : [],
        'leitzeile' : [],
        'passage'   : {
            'pass_id' : 0,
            'hr'      : '',
        },
        'current_application' : {
            'name' : 'ntg',
        },
        'current_user' : {
            'is_logged_in' : false,
            'is_editor'    : false,
            'username'     : 'anonymous',
        },
    },
    'mutations' : {
        passage (state, data) {
            Object.assign (state, data);
        },
        caption (state, caption) {
            document.title = caption;
            state.caption = caption;
        },
        current_app_and_user (state, data) {
            state.current_application = data[0];
            state.current_user        = data[1];
        },
    },
    'getters' : {
        'passage' : state => state.passage,
    },
});

export default {
    'store' : store,
    data () {
        return {
        };
    },
    'props'    : ['app_id', 'phase', 'api_base_url'],
    'computed' : {
        api_url () { return url.resolve (this.api_base_url, this.app_id + '/' + this.phase + '/'); },
    },
    'watch' : {
        api_url () { return this.update_globals; },
    },
    'methods' : {
        get_flashed_messages () {
            this.get ('messages.json').then ((response) => {
                for (let msg of response.data.data || []) {
                    if (msg.category === 'error') {
                        msg.category = 'danger';
                    }
                    $ ('div.flashed_messages').append (
                        `<div class="alert alert-${msg.category} alert-dismissible" role="alert">
                         <button type="button" class="close" data-dismiss="alert"
                                 aria-label="Close"><span aria-hidden="true">×</span></button>
                            ${msg.message}
                         </div>`
                    );
                }
            });
        },
        update_globals () {
            const p1 = this.get ('application.json');
            const p2 = this.get ('user.json');

            Promise.all ([p1, p2]).then ((p) => {
                store.commit ('current_app_and_user', [p[0].data.data, p[1].data.data]);
            });
        },
    },
    mounted () {
        this.update_globals ();
    },
};

</script>

<style lang="less">
@import "@{BS}/variables.less";
@import "@{BS}/mixins.less";

div.bs-docs-header {
    margin-bottom: 1em;
    color: #cdbfe3;
    background-color: #6f5499;

    h1 {
        color: white;

        span.appname {
            float: right;
        }
    }
}

div.helpmenu {
    float: right;
}

.alert {
    margin-top: @line-height-computed;

    &.alert-margins {
        margin: @line-height-computed @alert-padding;
    }
}
</style>
