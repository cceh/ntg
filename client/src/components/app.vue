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
 * @component client/app
 * @author Marcello Perathoner
 */

import Vue            from 'vue';
import Vuex           from 'vuex';
import { mapGetters } from 'vuex';
import VueRouter      from 'vue-router';
import axios          from 'axios';
import url            from 'url';

import d3common       from 'd3_common';

import page_header    from 'page_header.vue';
import flash_messages from 'flash_messages.vue';
import prj_list       from 'project_list.vue';
import index          from 'index.vue';
import find_relatives from 'find_relatives.vue';
import coherence      from 'coherence.vue';
import comparison     from 'comparison.vue';
import notes_list     from 'notes_list.vue';
import checks_list    from 'checks_list.vue';
import opt_stemma     from 'optimal_substemma.vue';
import set_cover      from 'set_cover.vue';


Vue.use (Vuex);
Vue.use (VueRouter);


const default_home = {
    'caption' : 'Up',
    'route'   : 'index',
};

const router = new VueRouter ({
    'mode'   : 'history',
    'routes' : [
        {
            'path'      : '/',
            'component' : prj_list,
            'name'      : 'prj_list',
            'props'     : true,
            'meta'      : {
                'caption' : 'Projects',
                'home'    : { 'caption' : 'INTF', 'route' : 'external.intf' },
            },
        },
        {
            'path'      : '/:app_id/:phase/',
            'component' : index,
            'name'      : 'index',
            'props'     : true,
            'meta'      : {
                'caption' : 'Genealogical Queries',
                'home'    : { 'caption' : 'Up', 'route' : 'prj_list' },
            },
        },
        {
            'path'      : '/:app_id/:phase/find_relatives',
            'component' : find_relatives,
            'name'      : 'find_relatives',
            'props'     : true,
            'meta'      : {
                'caption' : 'Find Relatives',
                'home'    : default_home,
            },
        },
        {
            'path'      : '/:app_id/:phase/coherence/:passage_or_id',
            'component' : coherence,
            'name'      : 'coherence',
            'props'     : true,
            'meta'      : {
                'caption' : 'Coherence and Textual Flow',
                'home'    : default_home,
            },
        },
        {
            'path'      : '/:app_id/:phase/comparison',
            'component' : comparison,
            'name'      : 'comparison',
            'props'     : true,
            'meta'      : {
                'caption' : 'Comparison of Witnesses',
                'home'    : default_home,
            },
        },
        {
            'path'      : '/:app_id/:phase/notes',
            'component' : notes_list,
            'name'      : 'notes_list',
            'props'     : true,
            'meta'      : {
                'caption' : 'List of Notes',
                'home'    : default_home,
            },
        },
        {
            'path'      : '/:app_id/:phase/checks',
            'component' : checks_list,
            'name'      : 'checks_list',
            'props'     : true,
            'meta'      : {
                'caption' : 'List of Congruence Check Failures',
                'home'    : default_home,
            },
        },
        {
            'path'      : '/:app_id/:phase/opt_stemma',
            'component' : opt_stemma,
            'name'      : 'opt_stemma',
            'props'     : true,
            'meta'      : {
                'caption' : 'Optimal Substemma',
                'home'    : default_home,
            },
        },
        {
            'path'      : '/:app_id/:phase/set_cover',
            'component' : set_cover,
            'name'      : 'set_cover',
            'props'     : true,
            'meta'      : {
                'caption' : 'Minimum Set Cover',
                'home'    : default_home,
            },
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
            beforeEnter () {
                /* eslint-disable-next-line no-restricted-globals */
                location.href = 'http://intf.uni-muenster.de/cbgm/acts/';
            },
        },
    ],
});

const default_application = {
    'name'                : '',
    'read_access'         : 'public',
    'read_access_private' : 'nobody',
    'write_access'        : 'nobody',
};

const store = new Vuex.Store ({
    'state' : {
        'route_meta' : {
            'caption' : 'Index',
            'home'    : default_home,
        },
        'api_url'             : '',
        'instances'           : [],
        'ranges'              : [],
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
            document.title = data.caption;
        },
        caption (state, data) {
            state.route_meta.caption = data;
            document.title = data;
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
        ranges (state, data) {
            state.ranges = data;
        },
    },
    'getters' : {
        'api_url'             : state => state.api_url,
        'route_meta'          : state => state.route_meta,
        'ranges'              : state => state.ranges,
        'current_application' : state => state.current_application,
        'current_user'        : state => state.current_user,
        'is_logged_in'        : state => {
            return state.current_user.username !== 'anonymous';
        },
        'can_read' : state => {
            return state.current_user.roles.includes (state.current_application.read_access);
        },
        'can_read_private' : state => {
            return state.current_user.roles.includes (state.current_application.read_access_private);
        },
        'can_write' : state => {
            return state.current_user.roles.includes (state.current_application.write_access);
        },
    },
});

/*
 * Get application information *before* displaying the view.
 */

router.beforeEach ((to, from, next) => {
    if (to.params.app_id) {
        const api_url = url.resolve (api_base_url, to.params.app_id + '/' + to.params.phase + '/');
        if (api_url !== store.state.api_url) {
            const requests = [
                axios.get (url.resolve (api_url, 'application.json')),
                axios.get (url.resolve (api_url, 'ranges.json/')),
            ];
            Promise.all (requests).then ((responses) => {
                store.commit ('current_application', responses[0].data.data);
                store.commit ('ranges',              responses[1].data.data);
                store.commit ('api_url',             api_url);
                store.commit ('route_meta',          to.matched[0].meta);
                next ();
            }).catch ((dummy_error) => {
                next (false);
            });
            return;
        }
        store.commit ('route_meta', to.matched[0].meta);
        next ();
        return;
    }
    store.commit ('api_url',    '');
    store.commit ('route_meta', to.matched[0].meta);
    next ();
});

/**
 * Ascend the VM tree until you find an api_url and use it as prefix to build
 * the full API url.
 *
 * @param    {String} suffix - Url suffix
 * @returns  {String} Full API url
 * @memberof module:client/app
 */

Vue.prototype.build_full_api_url = function (suffix) {
    let vm = this;
    /* eslint-disable-next-line no-constant-condition */
    while (true) {
        if (vm.api_url) {
            return url.resolve (vm.api_url, suffix);
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
 * @param {String} suffix - Url suffix
 * @param {Object} config - Params for axios call
 * @returns {Promise}
 * @memberof module:client/app
 */

Vue.prototype.get = function (suffix, config = {}) {
    return axios.get (this.build_full_api_url (suffix), config);
};

Vue.prototype.post = function (suffix, config = {}) {
    return axios.post (this.build_full_api_url (suffix), config);
};

Vue.prototype.put = function (suffix, config = {}) {
    return axios.put (this.build_full_api_url (suffix), config);
};


/**
 * Trigger a native event.
 *
 * vue.js custom 'events' do not bubble, so they are useless.  Trigger a real
 * event that bubbles and can be caught by vue.js.
 *
 * @param {string} name - event name
 * @param {array}  data - data
 * @memberof module:client/app
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
    'router' : router,
    'store'  : store,
    'data'   : function () {
        return {
            'api_base_url' : api_base_url,
            'bust'         : 1,
        };
    },
    'components' : {
        'page-header'    : page_header,
        'flash-messages' : flash_messages,
    },
    'computed' : {
        ...mapGetters ([
            'api_url',
        ]),
    },
    created () {
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
    mounted () {
        // insert css for color palettes
        d3common.insert_css_palette (d3common.generate_css_palette (
            d3common.labez_palette,
            d3common.cliques_palette
        ));
    },
};

// The browser triggers hashchange only on window.  We want it on every app.
window.addEventListener ('hashchange', function () {
    const event = new CustomEvent ('hashchange');
    document.querySelectorAll ('.want_hashchange').forEach (function (el) {
        el.dispatchEvent (event);
    });
});


</script>

<style lang="scss">
/* app.vue */

@import "bootstrap-custom.scss";

/* bootstrap */
/* FIXME: this file is huge, maybe pick only the things we use */
@import "~bootstrap";

/* font-awesome */
/* List of icons at: http://astronautweb.co/snippet/font-awesome/ */

$fa-font-path: '~@fortawesome/fontawesome-free/webfonts';
/* FIXME: this file is huge, maybe pick only the icons we use */
@import "~@fortawesome/fontawesome-free/scss/fontawesome.scss";
@import "~@fortawesome/fontawesome-free/scss/solid.scss";

</style>
