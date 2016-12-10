/**
 * This module displays a textflow diagram.  A TD consists of one or more DAGs
 * (directed acyclic graphs) that show the relationship of all manuscripts that
 * have the same reading at one passage.  It can be used to deduce where a
 * reading came from.  This module also displays a string of controls to refine
 * the TD.
 *
 * @module textflow
 * @requires d3-stemma-layout
 * @author Marcello Perathoner
 */

define (['jquery', 'lodash', 'd3', 'd3-stemma', 'relatives', 'tools', 'bootstrap', 'bootstrap-slider', 'jquery-ui'],

function ($, _, d3, d3stemma, relatives, tools) {
    'use strict';

    function changed () {
        // currently unused
        $ (document).trigger ('ntg.textflow.changed');
    }

    function options (event) {
        var instance = event.data;
        var data = instance.data;
        event.data = data;

        tools.handle_toolbar_events (event);
        instance.load_passage (data.pass_id, data.labez);
        event.stopPropagation ();
    }

    /**
     * Load a new passage.
     *
     * @function load_passage
     *
     * @param {int} pass_id - The passage to display.
     *
     * @param {string} labez - The labez to display.
     */
    function load_passage (passage, labez) {
        this.data.pass_id = passage.id;
        this.data.labez = labez;

        this.graph.load_dot (
            'textflow.dot/' + passage.id + '/attestation/' + labez + '?' +
                $.param (_.pick (this.data, ['connectivity', 'chapter', 'include', 'fragments', 'mode']))
        );
        var promise = tools.load_labez_dropdown (this.toolbar.find ('div.textflow-labez'), passage.id);
        var that = this;
        promise.done (function () {
            tools.set_toolbar_buttons (that.toolbar, that.data);
            // Maybe we changed chapter while navigating.  Set a new chapter.
            that.toolbar.find ('div.textflow-chapter input[data-opt != "0"]').attr ('data-opt', passage.chapter);
            changed ();
        });
    }

    /**
     * Initialize the module.
     *
     * @function init
     *
     * @param {string} wrapper_selector - The element that should contain the apparatus table.
     *
     * @param {string} id_prefix - Prefix to use for all for the ids. (currently unused)
     *
     * @param {string} toolbar_selector - The toolbar to initialize and use.
     *
     * @returns {dict} - The module instance object.
     */
    function init (wrapper_selector, id_prefix, toolbar_selector) {
        var instance = {};
        instance.wrapper      = $ (wrapper_selector);
        instance.toolbar      = $ (toolbar_selector);
        instance.id_prefix    = id_prefix;
        instance.graph        = d3stemma.init (wrapper_selector, id_prefix);
        instance.load_passage = load_passage;
        instance.data         = {
            'pass_id'      : 1,
            'labez'        : 'a',
            'connectivity' : '10',
            'chapter'      : '0',
            'include'      : [],
            'fragments'    : [],
            'mode'         : 'rec',
        };

        // Init toolbar.
        instance.toolbar.find ('.dropdown-toggle').dropdown ();
        instance.toolbar.find ('input[name="connectivity"]').bootstrapSlider ({
            'value' : 10,
            'ticks' : [1, 5, 10, 20],
        });

        // Answer toolbar activity.
        $ (document).on ('click',     toolbar_selector + ' input', instance, options);
        $ (document).on ('slideStop', toolbar_selector + ' input[name="connectivity"]', instance, options);

        return instance;
    }

    return {
        'init' : init,
    };
});
