/**
 * This module is just a wrapper around d3stemma for symmetry with the textflow
 * module.
 *
 * @module local-stemma
 * @author Marcello Perathoner
 */

define ([
    'jquery',
    'lodash',
],

function ($, _) {
    'use strict';

    function changed () {
        // currently unused
        $ (document).trigger ('changed.ntg.local-stemma');
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

        var params = ['width', 'fontsize'];

        // provide a width and fontsize for GraphViz to format the graph
        instance.data.width = instance.$wrapper.width ();                            // in px
        instance.data.fontsize = parseFloat (instance.$wrapper.css ('font-size'));   // in px

        instance.graph.load_dot (
            'stemma.dot/' + passage.id + '?' + $.param (_.pick (instance.data, params))
        ).done (function () {
            instance.dirty = false;
            instance.$panel.animate ({ 'width' : (instance.graph.bbox.width + 20) + 'px' });
        });
        changed ();
    }

    /**
     * Initialize the module.
     *
     * @function init
     *
     * @param {Object} instance     - The panel module instance to inherit from.
     * @param {Object} graph_module - The graph module to use.
     * @param {string} id_prefix    - The prefix to use for all generated ids.
     *
     * @returns {Object} - The module instance object.
     */
    function init (instance, graph_module, id_prefix) {
        instance.load_passage = load_passage;
        $.extend (instance.data, {});
        instance.$wrapper = instance.$panel.find ('.panel-content');

        instance.graph = graph_module.init (instance.$wrapper, id_prefix);

        return instance;
    }

    return {
        'init' : init,
    };
});
