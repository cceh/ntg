/*
 * This is just a wrapper around the app.vue component
 * to make a suitable entry point for webpack.
 *
 * See: https://ssr.vuejs.org/guide/structure.html#code-structure-with-webpack
 *
 * @module client/app
 */

import Vue from 'vue';

import app from '../components/app.vue';

window.api_base_url = api_base_url;

new Vue ({
    // the root instance simply renders the app component.
    'render' : h => h (app),
}).$mount ('#app');
