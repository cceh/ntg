/**
 * This module is the main entry point and displays the main page.  This module
 * is only a container for the other modules that actually display the gadgets.
 *
 * @module coherence
 * @author Marcello Perathoner
 */

define (['jquery', 'lodash', 'tools', 'd3', 'd3-common', 'd3-stemma', 'affinity',
         'apparatus', 'navigator', 'relatives', 'textflow', 'bootstrap',
         'css!bootstrap-css',
         'css!bootstrap-slider-css',
         'css!jquery-ui-css',
         'css!site-css',
         'css!coherence-css',
         'css!relatives-css',
         'css!textflow-css'],

function ($, _, tools, d3, d3common, d3stemma, affinity, apparatus, navigator, relatives, textflow) {
    'use strict';

    var module = {}; // singleton

    /**
     * Set a new passage.  Update all gadgets on the page.
     *
     * @function set_passage
     *
     * @param {Object} json - The new passage object from the server.
     */
    function set_passage (json) {
        module.apparatus.load_passage (json);
        module.local_stemma.load_dot ('stemma.dot/' + json.id);
        module.ltextflow.load_passage (json, 'a', 'A',   false);
        module.vtextflow.load_passage (json, null, null, true);
        module.gtextflow.load_passage (json, null, null, false);

        // make sure attestation gets set *after* the nodes are loaded
        module.affinity_promise.done (function () {
            module.affinity.set_attestation ('attestation.json/' + json.id);
        });
    }


    /**
     * Initialize the module.
     *
     * @function init
     */
    function init () {
        $ (document).off ('.data-api');

        module.navigator    = navigator.init ();
        module.apparatus    = apparatus.init ('#apparatus-wrapper',        'app_', 'div.toolbar-apparatus');
        module.local_stemma = d3stemma.init  ('#local-stemma-wrapper',     'ls_');
        module.ltextflow    = textflow.init  ('#local-textflow-wrapper',   'tf_',  'div.local-toolbar-textflow');
        module.vtextflow    = textflow.init  ('#variant-textflow-wrapper', 'vtf_', 'div.variant-toolbar-textflow');
        module.gtextflow    = textflow.init  ('#global-textflow-wrapper',  'gtf_', 'div.global-toolbar-textflow');
        module.affinity     = affinity.init  ('#affinity-wrapper',         'aff_');
        relatives.init ();

        module.affinity_promise = module.affinity.load_json ('affinity.json');

        d3common.insert_css_palette (
            d3common.generate_css_palette (
                d3common.attestation_palette
            )
        );

        tools.create_panel_controls ($ ('div.panel'));
        tools.init_panel_events ();

        // Click on a ms. in the apparatus or in a relatives popup.
        $ (document).on ('click', '.ms[data-ms-id]', function (event) {
            var ms_id = $ (event.target).attr ('data-ms-id');
            relatives.create_panel (ms_id, event.target);
        });

        // Click on a node in the textflow diagram.
        $ (document).on ('click', 'div.panel-textflow g.node', function (event) {
            var ms_id = $ (event.currentTarget).attr ('data-ms-id'); // the g.node, not the circle
            relatives.create_panel (ms_id, event.currentTarget);
        });

        // Click on a node in the affinity cloud.
        $ (document).on ('click', '#affinity-wrapper g.node', function (event) {
            var ms_id = $ (event.currentTarget).attr ('data-ms-id'); // the g.node, not the circle
            relatives.create_panel (ms_id, event.currentTarget);
        });

        // Content of popup changed.  Redo force graph highlighting.
        $ (document).on ('ntg.popup.changed', function () {
            var sources = relatives.get_ms_ids_from_popups ('source');
            var targets = relatives.get_ms_ids_from_popups ('target');
            module.affinity.highlight (sources, targets);
        });

        // The user navigated to new passage.
        $ (document).on ('ntg.passage.changed', function (event, json) {
            set_passage (json);
        });

        // Simulate user navigation set the passage on all modules.
        if (window.location.hash) {
            var hash = window.location.hash.substring (1);
            module.navigator.set_passage (hash);
        }
    }

    module.init = init;
    module.set_passage = set_passage;

    return module;
});
