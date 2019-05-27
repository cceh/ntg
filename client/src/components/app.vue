<template>
  <router-view />
</template>

<script>
/**
 * The Vue.js application
 *
 * @component app
 * @author Marcello Perathoner
 */

import Vue  from 'vue';
import Vuex from 'vuex';
import url  from 'url';

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
            'name'         : 'ntg',
            'read_access'  : 'none',
            'write_access' : 'none',
        },
        'current_user' : {
            'username' : 'anonymous',
            'roles'    : ['public'],
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

<style lang="scss">
@import "../css/bootstrap-custom.scss";

/* bootstrap */
@import "../../node_modules/bootstrap/scss/bootstrap";
@import "../../node_modules/bootstrap-vue/dist/bootstrap-vue.css";

/* List of icons at: http://astronautweb.co/snippet/font-awesome/ */
@import "../../node_modules/@fortawesome/fontawesome-free/css/fontawesome.css";
@import "../../node_modules/@fortawesome/fontawesome-free/css/solid.css";

</style>
