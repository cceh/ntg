<template>
  <div class="vm-page-header">

    <!-- the violet header -->
    <div class="bs-docs-header">
      <!-- needs a nested container to expand the violet band to the screen edges -->
      <h1 class="container d-flex flex-row justify-content-between">
        <span class="caption">{{ route_meta.caption }}</span>
        <span class="appname">{{ current_application.name }}</span>
      </h1>
    </div>

    <div class="login-nav container d-flex flex-row justify-content-end bs-docs-container">
      <router-link :to="{ 'name' : route_meta.home.route }">{{ route_meta.home.caption }}</router-link>
      &#xa0; | &#xa0;
      <a href="/pdfs/GenQ4_Guide.pdf" target="_blank">Short Guide (PDF)</a>
      <template v-if="current_user.can_login">
        <template v-if="is_logged_in">
          &#xa0; | &#xa0;
          <a href="/user/profile" class="user-profile-link">
            <span class="fas fa-user" /> {{ current_user.username }}
          </a>
          &#xa0; | &#xa0;
          <a href="/user/sign-out" class="user-logout-link">
            <span class="fas fa-sign-out-alt" /> Sign out
          </a>
        </template>
        <template v-else>
          &#xa0; | &#xa0;
          <a href="/user/sign-in" class="user-login-link">
            <span class="fas fa-sign-in-alt" /> Sign in
          </a>
        </template>
      </template>
    </div>

    <div v-if="!can_read" class="container bs-docs-container login-required-message">
      Sorry.  You don't have read access to this section.
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

import { mapGetters } from 'vuex';

export default {
    data () {
        return {
        };
    },
    'computed' : {
        ...mapGetters ([
            'can_read',
            'is_logged_in',
            'current_application',
            'current_user',
            'route_meta',
        ]),
    },
};

</script>

<style lang="scss">
/* page_header.vue */
@import "bootstrap-custom";

div.vm-page-header {
    div.bs-docs-header {
        margin: 0;
        padding: ($spacer * 0.5) 0 ($spacer * 0.25) 0;
        color: var(--light);
        background-color: var(--brand-color);

        @media print {
            /* compensate for missing div.login-nav */
            margin-bottom: $spacer;
            color: black;
            background-color: transparent;
        }
    }

    div.bs-docs-container {
        padding-top: ($spacer * 0.5);
        padding-bottom: ($spacer * 0.5);
    }

    div.login-nav {
        @media print {
            display: none !important;
        }
    }

    div.login-required-message {
        color: red;
    }
}
</style>
