/**
 * This module implements the main page.  The main page contains lots of colored
 * gadgets to impress our customers.
 *
 * @module coherence
 * @author Marcello Perathoner
 */

define (['jquery', 'lodash', 'tools', 'd3', 'd3-common', 'd3-stemma', 'd3-force',
         'navigator', 'apparatus', 'relatives', 'textflow', 'bootstrap'],

function ($, _, tools, d3, d3common, d3stemma, d3force, navigator, apparatus, relatives, textflow) {
    'use strict';

    var module = {};

    /**
     * Set a new passage.  Changes all gadgets on the page
     *
     * @function set_passage
     *
     * @param {int} pass_id - The new passage id
     */
    function set_passage (json) {
        module.apparatus.load_passage (json.id);
        module.d3stemma.load_dot ('/stemma.dot/' + json.id);
        module.textflow.load_passage (json.id, 'a');
        module.d3force.set_attestation ('/attestation.json/' + json.id);
    }

    /**
     * Initialize the module.
     *
     * @function init
     *
     * @param {dict} params - A dictionary containing the parameters.
     *
     * @returns {dict} - The module object.
     */
    function init (params) {
        var pass_id = params.pass_id;

        $ (document).off ('.data-api');
        $.fn.bootstrapTooltip = $.fn.tooltip.noConflict ();

        module.navigator = navigator.init (params.title_prefix);

        module.apparatus = apparatus.init ($.extend (params, {
            'wrapper_selector' : '#apparatus-wrapper',
        }));

        relatives.init ();

        module.d3stemma = d3stemma.init ('#local-stemma-wrapper', 'ls_');

        module.textflow = textflow.init ('#passage-stemma-wrapper', 'div.toolbar-textflow', 'tf_');

        module.d3force = d3force.init ('#force-layout-wrapper', 'aff_');
        module.d3force.load_json ('/affinity.json', function () {
            module.d3force.set_attestation ('/attestation.json/' + pass_id); // FIXME use promise
        });

        module.navigator.set_passage (pass_id);

        var css = d3common.generate_css_palette (d3common.attestation_palette);
        d3common.insert_css_palette (css);

        // click on ms in list of labez or in relatives popup
        $ (document).on ('click', '.ms[data-ms-id]', function (event) {
            var $target = $ (event.target);
            relatives.init_tooltip ($target);
            $target.relatives_tooltip ('open');
        });

        // click on node in textflow diagram
        $ (document).on ('click', '#passage-stemma-wrapper g.node', function (event) {
            var $target = $ (event.currentTarget); // the g.node, not the circle
            relatives.init_svg_tooltip ($target);
            $target.svg_tooltip ('open');
        });

        // click on node in force diagram
        $ (document).on ('click', '#force-layout-wrapper g.node', function (event) {
            var $target = $ (event.currentTarget); // the g.node, not the circle
            relatives.init_svg_tooltip ($target);
            $target.svg_tooltip ('open');
        });

        // Content of popup changed.  Redo force graph highlighting.
        $ (document).on ('ntg.popup.changed', function () {
            var sources = relatives.get_ms_ids_from_popups ('source');
            var targets = relatives.get_ms_ids_from_popups ('target');
            module.d3force.highlight (sources, targets);
        });

        // User navigated to new passage
        $ (document).on ('ntg.passage.changed', function (event, json) {
            set_passage (json);
        });
    }

    module.init = init;
    module.set_passage = set_passage;

    return module;
});
