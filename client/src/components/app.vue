<template>
  <div id="app">
    <page-header></page-header>
    <flash-messages></flash-messages>
    <router-view></router-view>
  </div>
</template>

<script>
/**
 * App component.  The whole application.
 *
 * @component app
 * @author Marcello Perathoner
 */

import $              from 'jquery';
import Vue            from 'vue';
import Vuex           from 'vuex';
import { mapGetters } from 'vuex';
import VueRouter      from 'vue-router';
import BootstrapVue   from 'bootstrap-vue';
import axios          from 'axios';
import url            from 'url';

import page_header    from '../components/page_header.vue';
import flash_messages from '../components/flash_messages.vue';
import prj_list       from '../components/project_list.vue';
import index          from '../components/index.vue';
import attestation    from '../components/attestation.vue';
import coherence      from '../components/coherence.vue';
import comparison     from '../components/comparison.vue';
import notes_list     from '../components/notes_list.vue';
import opt_stemma     from '../components/optimal_substemma.vue';
import set_cover      from '../components/set_cover.vue';

Vue.use (Vuex);
Vue.use (VueRouter);
Vue.use (BootstrapVue);


const default_home = {
    'caption' : 'Up',
    'route'   : 'index',
};

const router = new VueRouter ({
    'mode'   : 'history',
    'routes' : [
        { 'path' : '/',                           'component' : prj_list,    'name' : 'prj_list',    'props' : true,
          'meta' : {
              'caption' : 'Projects',
              'home'    :  { 'caption' : 'INTF', 'route' : 'external.intf' },
          }
        },
        { 'path' : '/:app_id/:phase/',            'component' : index,       'name' : 'index',       'props' : true,
          'meta' : {
              'caption' : 'Genealogical Queries',
              'home'    :  { 'caption' : 'Up', 'route' : 'prj_list' },
          }
        },
        { 'path' : '/:app_id/:phase/attestation', 'component' : attestation, 'name' : 'attestation', 'props' : true,
          'meta' : {
              'caption' : 'Find Relatives',
              'home'    : default_home,
          }
        },
        { 'path' : '/:app_id/:phase/coherence',   'component' : coherence,   'name' : 'coherence',   'props' : true,
          'meta' : {
              'caption' : 'Coherence',
              'home'    : default_home,
          }
        },
        { 'path' : '/:app_id/:phase/comparison',  'component' : comparison,  'name' : 'comparison',  'props' : true,
          'meta' : {
              'caption' : 'Comparison',
              'home'    : default_home,
          }
        },
        { 'path' : '/:app_id/:phase/notes',       'component' : notes_list,  'name' : 'notes_list',  'props' : true,
          'meta' : {
              'caption' : 'Notes',
              'home'    : default_home,
          }
        },
        { 'path' : '/:app_id/:phase/opt_stemma',  'component' : opt_stemma,  'name' : 'opt_stemma',  'props' : true,
          'meta' : {
              'caption' : 'Optimal Substemma',
              'home'    : default_home,
          }
        },
        { 'path' : '/:app_id/:phase/set_cover',   'component' : set_cover,   'name' : 'set_cover',   'props' : true,
          'meta' : {
              'caption' : 'Set Cover',
              'home'    : default_home,
          }
        },

        // external routes

        { 'path' : '/user/sign-in',  'name' : 'user.login'    },
        { 'path' : '/user/profile',  'name' : 'user.profile'  },
        { 'path' : '/user/sign-out', 'name' : 'user.logout'   },

        {
            'path' : '/intf',
            'name' : 'external.intf',
            // hack because router cannot handle external links
            // See: https://github.com/vuejs/vue-router/issues/1280
            beforeEnter () { location.href = 'http://intf.uni-muenster.de/cbgm/acts/' },
        },
    ],
});

const default_application = {
    'name'         : '',
    'read_access'  : 'public',
    'write_access' : 'nobody',
};

const store = new Vuex.Store ({
    'state' : {
        'route_meta' : {
            'caption' : 'Index',
            'home'    : default_home,
        },
        'api_url'   : '',
        'instances' : [],
        'ranges'    : [],
        'leitzeile' : [],
        'passage'   : {
            'pass_id' : 0,
            'hr'      : '',
        },
        'current_application' : {
            ... default_application,
        },
        'current_user' : {
            'username' : 'anonymous',
            'roles'    : ['public'],
        },
    },
    'mutations' : {
        instances (state, data) {
            state.instances = data;
        },
        api_url (state, data) {
            state.api_url = data;
        },
        route_meta (state, data) {
            state.route_meta = data;
        },
        caption (state, data) {
            state.route_meta.caption = data;
        },
        current_user (state, data) {
            state.current_user = data;
        },
        current_application (state, data) {
            state.current_application = data;
        },
        passage (state, data) {
            Object.assign (state, data);
        },
    },
    'getters' : {
        'api_url'    : state => state.api_url,
        'route_meta' : state => state.route_meta,
        'passage'    : state => state.passage,
        'current_application' : state => state.current_application,
        'current_user' : state => state.current_user,
        'is_logged_in' : state => {
            return state.current_user.username != 'anonymous';
        },
        'can_read' : state => {
            return state.current_user.roles.includes (state.current_application.read_access);
        },
        'can_write' : state => {
            return state.current_user.roles.includes (state.current_application.write_access);
        },
    },
});


/**
 * Ascend the VM tree until you find an api_url and use it as prefix to build
 * the full API url.
 *
 * @function build_full_api_url
 *
 * @param {Object} vm  - The Vue instance
 * @param {String} url - Url suffix
 *
 * @returns {String} Full API url
 */

Vue.prototype.build_full_api_url = function (url) {
    let vm = this;
    /* eslint-disable-next-line no-constant-condition */
    while (true) {
        if (vm.api_url) {
            return vm.api_url + url;
        }
        if (!vm.$parent) {
            break;
        }
        vm = vm.$parent;
    }
    return url;
};

/**
 * Make a GET request to the API server.
 *
 * @function get
 *
 * @param {String} url  - Url suffix
 * @param {Object} data - Params for axios call
 *
 * @returns {Promise}
 */

Vue.prototype.get = function (url, data = {}) {
    return axios.get (this.build_full_api_url (url), data);
};

Vue.prototype.post = function (url, data = {}) {
    return axios.post (this.build_full_api_url (url), data);
};

Vue.prototype.put = function (url, data = {}) {
    return axios.put (this.build_full_api_url (url), data);
};


/**
 * Trigger a native event.
 *
 * vue.js custom `events´ do not bubble, so they are useless.  Trigger a real
 * event that bubbles and can be caught by vue.js.
 *
 * @function $trigger
 *
 * @param {string} name - event name
 * @param {array}  data - data
 */

Vue.prototype.$trigger = function (name, data) {
    const event = new CustomEvent (name, {
        'bubbles' : true,
        'detail'  : { 'data' : data },
    });
    this.$el.dispatchEvent (event);
};

/* eslint-disable no-new */
export default {
    'data'  : function () {
        return {
            /* eslint-disable no-undef */
            'api_base_url' : api_base_url,
        }
    },
    'router'     : router,
    'store'      : store,
    'components' : {
        'page-header'    : page_header,
        'flash-messages' : flash_messages,
    },
    'computed' : {
        ...mapGetters ([
            'api_url',
            'route_meta',
        ]),
    },
    'watch' : {
        route_meta () {
            document.title = this.route_meta.caption;
        },
        api_url () {
            const vm = this;
            if (vm.api_url) {
                const requests = [
                    vm.get ('application.json'),
                ];
                Promise.all (requests).then ((responses) => {
                    vm.$store.commit ('current_application', responses[0].data.data);
                });
            } else {
                vm.$store.commit ('current_application', default_application);
            }
        },
        $route (to, from) {
            this.on_route_change (to);
        },
    },
    'methods' : {
        on_route_change (to) {
            const vm = this;
            if (to.params.app_id) {
                vm.$store.commit (
                    'api_url',
                    url.resolve (vm.api_base_url, to.params.app_id + '/' + to.params.phase + '/')
                );
            } else {
                vm.$store.commit ('api_url', null);
            }
            vm.$store.commit ('route_meta', to.matched[0].meta);
        },
        update_globals () {
            const vm = this;
            const requests = [
                axios.get (url.resolve (vm.api_base_url, 'info.json')),
                axios.get (url.resolve (vm.api_base_url, 'user.json')),
            ];
            Promise.all (requests).then ((responses) => {
                vm.$store.commit ('instances',    responses[0].data.data.instances);
                vm.$store.commit ('current_user', responses[1].data.data);
            });
        },
    },
    created () {
        const vm = this;
        vm.update_globals ();
        this.$router.onReady (() => { vm.on_route_change (this.$router.currentRoute); });
    },
};

$ (document).off ('.data-api'); // turn off bootstrap's data api

// The browser triggers hashchange only on window.  We want it on every app.
$ (window).on ('hashchange', function () {
    // Concoct an event that you can actually catch with vue.js. (jquery events
    // are not real native events.)  This event does not bubble.
    const event = new CustomEvent ('hashchange');
    $ ('.want_hashchange').each (function (i, e) {
        e.dispatchEvent (event);
    });
});

</script>

<style lang="scss">
/* app.vue */

@import "../css/bootstrap-custom.scss";

/* bootstrap */
@import "../../node_modules/bootstrap/scss/bootstrap";
@import "../../node_modules/bootstrap-vue/dist/bootstrap-vue.css";

/* List of icons at: http://astronautweb.co/snippet/font-awesome/ */
@import "../../node_modules/@fortawesome/fontawesome-free/css/fontawesome.css";
@import "../../node_modules/@fortawesome/fontawesome-free/css/solid.css";

</style>
