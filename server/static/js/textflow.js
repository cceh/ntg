/**
 * This module displays a textflow diagram.  A TD consists of one or more DAGs
 * (directed acyclic graphs) that show the relationship of all manuscripts that
 * have the same reading at one passage.  It can be used to deduce where a
 * reading came from.  This module also displays a string of controls to refine
 * the TD.
 *
 * @module textflow
 * @author Marcello Perathoner
 */

define (['jquery',
         'lodash',
         'panel',
         'bootstrap',
         'bootstrap-slider',
         'jquery-ui',
         'css!textflow-css',
        ],

function ($, _, panel) {
    'use strict';

    function changed () {
        // currently unused
        $ (document).trigger ('ntg.textflow.changed');
    }

    /**
     * Load a new passage.
     *
     * @function load_passage
     *
     * @param {Object} passage - Which passage to load.
     */
    function load_passage (passage) {
        var instance = this;
        var params = ['labez', 'connectivity', 'chapter', 'include', 'fragments',
                      'mode', 'hyp_a', 'var_only', 'width', 'fontsize', 'splits'];

        // dirty hack! Make panel visible so SVG getBBox () will work.
        instance.$wrapper.slideDown ();

        // provide a width and fontsize for GraphViz to format the graph
        instance.data.width = instance.$wrapper.width ();                            // in px
        instance.data.fontsize = parseFloat (instance.$wrapper.css ('font-size'));   // in px

        instance.graph.load_dot (
            'textflow.dot/' + passage.id + '?' + $.param (_.pick (instance.data, params))
        ).done (function () {
            instance.dirty = false;
            instance.$panel.animate ({ 'width' : (instance.graph.bbox.width + 20) + 'px' });
        });

        var p1 = panel.load_labez_dropdown (
            this.$toolbar.find ('div.toolbar-labez'), passage.id, 'labez', []);
        var p2 = panel.load_labez_dropdown (
            this.$toolbar.find ('div.toolbar-hyp_a'), passage.id, 'hyp_a', [['A', 'A']]);
        var p3 = panel.load_chapter_dropdown (
            this.$toolbar.find ('div.toolbar-chapter'), 'chapter', [['0', 'All'], ['x', 'This']]);
        $.when (p1, p2, p3).done (function () {
            panel.set_toolbar_buttons (instance.$toolbar, instance.data);
            // Maybe we changed chapter while navigating.  Set a new chapter.
            instance.$toolbar.find ('div.toolbar-chapter input[data-opt = "x"]').attr ('data-opt', passage.chapter);
            changed ();
        });
    }

    /**
     * Initialize the module.
     *
     * @function init
     *
     * @param {Object} instance     - The panel instance to inherit from.
     * @param {Object} graph_module - The graph module to use.
     * @param {string} id_prefix    - The prefix to use for all generated ids.
     * @param {bool}   var_only     - Display only nodes and links between different readings.
     *
     * @returns {Object} - The module instance object.
     */
    function init (instance, graph_module, id_prefix, var_only) {
        instance.load_passage = load_passage;
        $.extend (instance.data, {
            'passage'      : null,
            'labez'        : '',
            'connectivity' : '10',
            'chapter'      : '0',
            'include'      : [],
            'fragments'    : [],
            'mode'         : 'rec',
            'hyp_a'        : 'A',
            'var_only'     : var_only ? ['var_only'] : [],
            'splits'       : [],
        });
        instance.$wrapper = instance.$panel.find ('.panel-content'); // see: dirty hack

        instance.graph = graph_module.init (instance.$wrapper, id_prefix);

        // Init toolbar.
        instance.$toolbar.find ('input[name="connectivity"]').bootstrapSlider ({
            'value' : 10,
            'ticks'           : [1,  5, 10, 20,  21],
            'ticks_positions' : [0, 25, 50, 90, 100],
            'formatter'       : panel.connectivity_formatter,
        });

        return instance;
    }

    return {
        'init' : init,
    };
});
