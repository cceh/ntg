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

define ([
    'jquery',
    'lodash',
    'panel',
    'tools',
    'css!textflow-css',
],

function ($, _, panel, tools) {
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
        instance.passage = passage;

        var params = [
            'labez', 'connectivity', 'range', 'include', 'fragments',
            'mode', 'hyp_a', 'var_only', 'width', 'fontsize', 'cliques',
        ];

        // reset dropdown selection if reading is not in new passage
        if (!instance.data.global && _.findIndex (
            passage.readings, function (o) { return o[0] === instance.data.labez; }) === -1) {
            instance.data.labez = passage.readings[0][0];
            instance.data.hyp_a = 'A';
        }

        // dirty hack! Make panel visible so SVG getBBox () will work.
        instance.$wrapper.slideDown ();

        // provide a width and fontsize for GraphViz to format the graph
        instance.data.width = instance.$wrapper.width ();                            // in px
        instance.data.fontsize = parseFloat (instance.$wrapper.css ('font-size'));   // in px

        var url = 'textflow.dot/' + passage.pass_id + '?' + $.param (_.pick (instance.data, params));
        var png_url = 'textflow.png/' + passage.pass_id + '?' + $.param (_.pick (instance.data, params));
        instance.graph.load_dot (url).done (function () {
            instance.$panel.animate ({ 'width' : (instance.graph.bbox.width + 20) + 'px' });
        });
        var name = $.trim (instance.$panel.find ('.panel-caption').text ());
        instance.$toolbar.find ('a[name="dot"]').attr ('href', url).attr ('download', name + '.dot');
        instance.$toolbar.find ('a[name="png"]').attr ('href', png_url);

        var p1 = panel.load_labez_dropdown (
            this.$toolbar.find ('div.toolbar-labez'), passage.pass_id, 'labez', [], []);
        var p2 = panel.load_labez_dropdown (
            this.$toolbar.find ('div.toolbar-hyp_a'), passage.pass_id, 'hyp_a', [['A', 'A']], []);
        var p3 = panel.load_range_dropdown (
            this.$toolbar.find ('div.toolbar-range'), passage.pass_id, 'range',
            [{ 'range' : 'This', 'value' : 'x' }], []);

        $.when (p1, p2, p3).done (function () {
            panel.set_toolbar_buttons (instance.$toolbar, instance.data);
            // Maybe we changed range while navigating.  Set a new range.
            instance.$toolbar.find ('div.toolbar-range input[data-opt = "x"]')
                .attr ('data-opt', passage.chapter);
            changed ();
        });
    }

    /**
     * Open a context menu when right clicked on a node.
     *
     * The context menu can be used to reassign the node to a different split.
     *
     * @function open_contextmenu
     *
     * @param {Object} event - The event
     */

    function open_contextmenu (event) {
        event.preventDefault ();

        var passage = event.data.passage;
        var xhr = $.getJSON ('cliques.json/' + passage.pass_id);
        xhr.done (function (json) {
            var instance = event.data;
            var msid     = event.target.parentNode.dataset.msId;
            var dataset  = event.target.dataset;
            var data = {
                'labez_old'  : dataset.labez,
                'clique_old' : dataset.clique,
            };

            // build the context menu
            var menu  = $ ('<table class="contextmenu"></table>');
            menu.append ($ (
                tools.format (
                    '<tr class="ui-state-disabled">' +
                        '<td class="bg_labez" data-labez="{labez_old}"></td>' +
                        '<td>{labez_old}{clique_old}</td>' +
                        '</tr>',
                    data
                )
            ));
            menu.append ($ ('<tr><td>-</td><td>-</td></tr>'));

            var cliques = _.filter (json.data, function (o) { return o[0][0] !== 'z'; });
            _.forEach (cliques, function (value) {
                data.labez_new  = value[0];
                data.clique_new = value[1];

                if (data.labez_new === data.labez_old && data.clique_new !== data.clique_old) {
                    menu.append ($ (tools.format (
                        '<tr data-action="move-manuscripts" ' +
                            'data-labez_old="{labez_old}" data-clique_old="{clique_old}" ' +
                            'data-labez_new="{labez_new}" data-clique_new="{clique_new}">' +
                            '<td class="bg_labez" data-labez="{labez_old}"></td>' +
                            '<td>Move subtree to {labez_new}{clique_new}</td>' +
                            '</tr>',
                        data
                    )));
                }
            });

            menu.menu ({
                'select' : function (ev, ui) {
                    var tr = ui.item[0];

                    // console.log ('Selected: ' + $ (tr).text ());

                    var xhr2 = $.getJSON (
                        'stemma-edit/' + passage.pass_id,
                        // do not extend the dataset itself,
                        // because arrays cannot be part of
                        // datasets
                        $.extend ({}, tr.dataset, {
                            'ms_ids' : tools.bfs (instance.graph.edges, msid),
                        })
                    );
                    xhr2.done (function (json2) {
                        // stemma-edit returns the changed passage
                        $ (document).trigger ('ntg.panel.reload', json2.data);
                    });
                    xhr2.fail (function (xhrobj) {
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
     * This module inherits from module :mod:`panel` and uses module
     * :mod:`d3-stemma-layout` to actually draw the graph.
     *
     * @function init
     *
     * @param {Object} instance     - The panel instance to inherit from.
     * @param {Object} graph_module - The graph module to use.
     * @param {string} id_prefix    - The prefix to use for all generated ids.
     * @param {bool}   global       - Display global textual flow
     * @param {bool}   var_only     - Display only nodes and links between different readings.
     *
     * @returns {Object} The module instance object.
     */
    function init (instance, graph_module, id_prefix, global, var_only) {
        instance.load_passage = load_passage;
        $.extend (instance.data, {
            'passage'      : null,
            'global'       : global,
            'labez'        : '',
            'connectivity' : '5',
            'range'        : 'All',
            'include'      : [],
            'fragments'    : [],
            'mode'         : 'sim',
            'hyp_a'        : 'A',
            'var_only'     : var_only ? ['var_only'] : [],
            'cliques'      : [],
        });
        instance.$wrapper = instance.$panel.find ('.panel-content'); // see: dirty hack

        instance.graph = graph_module.init (instance.$wrapper, id_prefix);

        if (is_editor) {
            instance.$panel.on ('contextmenu', 'g.node', instance, open_contextmenu);
        }

        return instance;
    }

    return {
        'init' : init,
    };
});
