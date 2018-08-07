<template>
  <div>

    <!-- the violet header -->
    <div class="bs-docs-header">
      <div class="container">
        <h1>
          <span class="caption">{{ caption }}</span>
          <span class="appname">{{ $store.state.current_application.name }}</span>
        </h1>
      </div>
    </div>

    <div class="container bs-docs-container">
      <div class="clearfix">
        <div class="pull-right">
          <a v-if="home_url" :href="home_url">Home</a>
          <router-link v-else :to="{ name : 'index' }">Home</router-link>
          &#xa0; | &#xa0;
          <a href="/pdf/GenQ4_Guide.pdf" target="_blank">Short Guide (PDF)</a>
          <template v-if="this.$store.state.current_user.is_logged_in">
            &#xa0; | &#xa0;
            <router-link :to="{ name : 'user.profile' }" class="user_profile_link">
              {{ this.$store.state.current_user.username }}
            </router-link>
            &#xa0; | &#xa0;
            <router-link :to="{ name : 'user.logout' }" class="user_logout_link">Sign out</router-link>
          </template>
        </div>
      </div>
    </div>

    <div class="container bs-docs-container">
      <div class="flashed_messages">
        <!-- container for eventual messages -->
      </div>
    </div>

  </div>
</template>

<script>
/**
 * The page header.
 *
 * @module page_header
 * @author Marcello Perathoner
 */

import $ from 'jquery';

export default {
    data () {
        return {
        };
    },
    'props' : ['caption', 'home_url'],
    'watch' : {
        caption () {
            document.title = this.caption;
        },
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

.alert {
    margin-top: @line-height-computed;

    &.alert-margins {
        margin: @line-height-computed @alert-padding;
    }
}
</style>
