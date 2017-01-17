/**
 * This module is the main entry point and displays the main page.  This module
 * is only a container for the other modules that actually display the gadgets.
 *
 * @module coherence
 * @author Marcello Perathoner
 */

define (['jquery',
         'lodash',
         'tools',
         'd3',
         'd3-common',
         'd3-stemma',
         'd3-chord',
         'affinity',
         'apparatus',
         'navigator',
         'panel',
         'relatives',
         'textflow',
         'local-stemma',
         'bootstrap',
         'css!bootstrap-css',
         'css!bootstrap-slider-css',
         'css!jquery-ui-css',
         'css!site-css',
         'css!coherence-css',
        ],

function ($, _, tools, d3, d3common, d3stemma, d3chord,
          affinity, apparatus, navigator, panel, relatives, textflow, locstem) {
    'use strict';

    var module = {}; // singleton

    /**
     * Set a new passage.  Update all gadgets on the page.
     *
     * @function set_passage
     *
     * @param {Object} json - The new passage object from the server.
     */
    function set_passage (passage) {
        module.apparatus.load (passage);
        module.local_stemma.load (passage);
        module.ltextflow.data.labez = 'a';
        module.ltextflow.data.hyp_a = 'A';
        module.ltextflow.load  (passage);
        module.vtextflow.load  (passage);
        module.vtextflow2.load (passage);
        module.gtextflow.load  (passage);

        // make sure attestation gets set *after* the nodes are loaded
        module.affinity_promise.done (function () {
            module.affinity.load (passage);
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

        module.apparatus    = apparatus.init (panel.init ($ ('div.panel-apparatus')));

        module.local_stemma = locstem.init  (
            panel.init ($ ('div.panel-local-stemma')),
            d3stemma,
            'ls_'
        );

        module.ltextflow    = textflow.init  (
            panel.init ($ ('div.panel-local-textflow')),
            d3stemma,
            'tf_',
            false
        );

        module.vtextflow    = textflow.init  (
            panel.init ($ ('div.panel-variant-textflow')),
            d3stemma,
            'vtf_',
            true
        );

        module.vtextflow2   = textflow.init  (
            panel.init ($ ('div.panel-variant-textflow-2')),
            d3chord,
            'vtf2_',
            true
        );

        module.gtextflow    = textflow.init  (
            panel.init ($ ('div.panel-global-textflow')),
            d3stemma,
            'gtf_',
            false
        );

        module.affinity     = affinity.init (
            panel.init ($ ('div.panel-affinity')),
            'aff_'
        );

        module.affinity_promise = module.affinity.load_json ('affinity.json');

        d3common.insert_css_palette (
            d3common.generate_css_palette (
                d3common.attestation_palette
            )
        );

        panel.create_panel_controls ($ ('div.panel'));
        panel.init_panel_events ();

        $ ('div.panel-variant-textflow-2 .panel-slidable').slideUp ();
        module.vtextflow2.visible = false;

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
