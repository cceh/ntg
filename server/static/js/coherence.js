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
          apparatus, navigator, panel, relatives, textflow, locstem) {
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

        d3common.insert_css_palette (
            d3common.generate_css_palette (
                d3common.labez_palette,
                d3common.splits_palette
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

        // Click on canvas to close context menus
        $ (document).on ('click', function (dummy_event) {
            $ ('table.contextmenu').fadeOut (function () { $ (this).remove (); });
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

    window.coherence = module;

    return module;
});
