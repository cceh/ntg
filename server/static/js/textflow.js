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
         'navigator',
         'tools',
         'd3-common',
         'bootstrap',
         'bootstrap-slider',
         'jquery-ui',
         'css!textflow-css',
        ],

function ($, _, panel, navigator, tools, d3common) {
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

        var url = 'textflow.dot/' + passage.id + '?' + $.param (_.pick (instance.data, params));
        var png_url = 'textflow.png/' + passage.id + '?' + $.param (_.pick (instance.data, params));
        instance.graph.load_dot (url).done (function () {
            instance.dirty = false;
            instance.$panel.animate ({ 'width' : (instance.graph.bbox.width + 20) + 'px' });
        });
        var name = $.trim (instance.$panel.find ('.panel-caption').text ());
        instance.$toolbar.find ('a[name="dot"]').attr ('href', url).attr ('download', name + '.dot');
        instance.$toolbar.find ('a[name="png"]').attr ('href', png_url);

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
     * Open a context menu when right clicked on a node.
     *
     * The context menu can be used to reassign the node to a different split.
     *
     * @param event
     */

    function open_contextmenu (event) {
        event.preventDefault ();

        var xhr = $.getJSON ('splits.json/' + navigator.passage.id);
        xhr.done (function (json) {
            var splits = _.filter (json.data, function (o) { return o[0][0] !== 'z'; });

            var instance = event.data;
            var labez    = event.target.dataset.labez;
            var varold   = event.target.dataset.varnew;
            var msid     = event.target.parentNode.dataset.msId;

            // build the menu contents
            var menu  = $ ('<table class="contextmenu"></table>');
            menu.append ($ (
                tools.format (
                    '<tr class="ui-state-disabled" data-varnew="{varold}">' +
                        '<td class="bg_labez" data-labez="{varold0}"></td>' +
                        '<td>{varold}</td>' +
                        '</tr>',
                    { 'varold' : varold, 'varold0' : varold[0] }
                )
            ));
            menu.append ($ ('<tr><td>-</td><td>-</td></tr>'));

            _.forEach (splits, function (value) {
                var varnew = value[0];
                if (varnew[0] === labez && varnew !== varold) {
                    menu.append ($ (tools.format (
                        '<tr data-action="move-subtree" data-varnew="{varnew}">' +
                            '<td class="bg_labez" data-labez="{varnew0}"></td>' +
                            '<td>Move subtree to {varnew}</td>' +
                            '</tr>',
                        { 'varnew' : varnew, 'varnew0' : varnew[0] })));
                }
            });

            menu.menu ({
                'select' : function (ev, ui) {
                    var tr     = ui.item[0];
                    var action = tr.dataset.action;

                    // console.log ('Selected: ' + $ (tr).text ());

                    var xhr = $.getJSON ('stemma-edit/' + navigator.passage.id, {
                        'action' : action,
                        'varold' : varold,
                        'varnew' : tr.dataset.varnew,
                        'ms_ids' : d3common.bfs (instance.graph.edges, msid),
                    });
                    xhr.done (function (json) {
                        $ (document).trigger ('ntg.passage.changed', json.data);
                    });
                    xhr.fail (function (xhrobj) {
                        tools.xhr_alert (xhrobj, event.data.$wrapper);
                    });
                    menu.fadeOut (function () { menu.remove (); });
                },
            });
            tools.svg_contextmenu (menu, event.target);
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
            'connectivity' : '5',
            'chapter'      : '0',
            'include'      : [],
            'fragments'    : [],
            'mode'         : 'sim',
            'hyp_a'        : 'A',
            'var_only'     : var_only ? ['var_only'] : [],
            'splits'       : [],
        });
        instance.$wrapper = instance.$panel.find ('.panel-content'); // see: dirty hack

        instance.graph = graph_module.init (instance.$wrapper, id_prefix);

        // Init toolbar.
        instance.$toolbar.find ('input[name="connectivity"]').bootstrapSlider ({
            'value'           : 5,
            'ticks'           : [1,  5, 10, 20,  21],
            'ticks_positions' : [0, 25, 50, 90, 100],
            'formatter'       : panel.connectivity_formatter,
        });

        if (is_editor) {
            instance.$panel.on ('contextmenu', 'g.node', instance, open_contextmenu);
        }

        return instance;
    }

    return {
        'init' : init,
    };
});
