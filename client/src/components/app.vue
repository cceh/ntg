<template>
  <router-view />
</template>

<script>
/**
 * The vue.js application
 *
 * @module app
 * @author Marcello Perathoner
 */

import Vue from 'vue';
import Vuex from 'vuex';
import url from 'url';

Vue.use (Vuex);

const store = new Vuex.Store ({
    'state' : {
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
        update_globals () {
            const requests = [
                this.get ('application.json'),
                this.get ('user.json'),
            ];
            Promise.all (requests).then ((responses) => {
                store.commit ('current_app_and_user', [
                    responses[0].data.data,
                    responses[1].data.data,
                ]);
            });
        },
    },
    mounted () {
        this.update_globals ();
    },
};

</script>
