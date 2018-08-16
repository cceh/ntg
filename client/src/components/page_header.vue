<template>
  <div>

    <!-- the violet header -->
    <div class="bs-docs-header">
      <!-- needs a nested container to expand the violet band to the screen edges -->
      <h1 class="container d-flex flex-row justify-content-between">
        <span class="caption">{{ caption }}</span>
        <span class="appname">{{ $store.state.current_application.name }}</span>
      </h1>
    </div>

    <div class="login-nav container d-flex flex-row justify-content-end bs-docs-container">
      <a v-if="home_url" :href="home_url">Home</a>
      <router-link v-else :to="{ name : 'index' }">Home</router-link>
      &#xa0; | &#xa0;
      <a href="/pdfs/GenQ4_Guide.pdf" target="_blank">Short Guide (PDF)</a>
      <template v-if="this.$store.state.current_user.is_logged_in">
        &#xa0; | &#xa0;
        <a href="/user/profile" class="user_profile_link">
          <span class="fas fa-user" /> {{ this.$store.state.current_user.username }}
        </a>
        &#xa0; | &#xa0;
        <a href="/user/sign-out" class="user_logout_link">
          <span class="fas fa-sign-out-alt" /> Sign out
        </a>
      </template>
    </div>

    <div class="container bs-docs-container flashed_messages">
      <!-- container for eventual messages -->
    </div>

  </div>
</template>

<script>
/**
 * The page header with the violet ribbon.
 *
 * @component page_header
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

<style lang="scss">
/* page_header.vue */
@import "bootstrap-custom";

div.bs-docs-header {
    margin: 0 0 ($spacer * 0.5) 0;
    padding: ($spacer * 0.5) 0 ($spacer * 0.25) 0;
    color: var(--light);
    background-color: var(--brand-color);
}

div.bs-docs-container {
    margin-bottom: ($spacer * 0.5);
}

div.login-nav {
    @media print {
        display: none !important;
    }
}

.alert {
    margin-top: $alert-padding-y;

    &.alert-margins {
        margin: $alert-padding-y $alert-padding-x;
    }
}
</style>
