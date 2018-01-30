'use strict';

/**
 * This module is the main entry point and displays the main page.  This module
 * is only a container for the other modules that actually display the gadgets.
 *
 * @module coherence
 * @author Marcello Perathoner
 */

define(['jquery', 'd3-common', 'd3-stemma', 'd3-chord', 'apparatus', 'navigator', 'panel', 'relatives', 'textflow', 'local-stemma', 'notes', 'css!bootstrap-css', 'css!jquery-ui-css', 'css!site-css', 'css!coherence-css'], function ($, d3common, d3stemma, d3chord, apparatus, navigator, panel, relatives, textflow, locstem, notes) {
    var module = {}; // singleton

    /**
     * Create a new popup managed by the relatives module.
     *
     * We have to create these dynamically because there may be many open at once.
     *
     * @function create_relatives_popup
     *
     * @param {integer} ms_id - The manuscript id
     * @param {Object} passage - The passage
     * @param {jQuery} target - An element. The popup will be positioned relative to this element.
     *
     * @returns {Promise} Resolved when popup is created.
     */

    function create_relatives_popup(ms_id, passage, target) {
        var $popup = $($('#relatives-template').html());
        $popup.hide().appendTo('#floating-panels').fadeIn();
        $popup.draggable();
        $popup.data('ms-id', ms_id);
        var instance = relatives.init(panel.init($popup));
        instance.load(passage).done(function () {
            instance.position_popup(target);
        });
        panel.create_panel_controls($popup);
        // notify others
        relatives.changed();
    }

    /**
     * Initialize the module.
     *
     * @function init
     */
    function init() {
        $(document).off('.data-api');

        module.navigator = navigator.init();

        // create the panels

        module.apparatus = apparatus.init(panel.init($('div.panel-apparatus')));

        module.local_stemma = locstem.init(panel.init($('div.panel-local-stemma')), d3stemma, 'ls_');

        // only editors will have this
        if (is_editor && $('div.panel-notes').length) {
            module.notes = notes.init(panel.init($('div.panel-notes')), 'notes_');
        }

        module.vtextflow = textflow.init(panel.init($('div.panel-variant-textflow')), d3stemma, 'vtf_', true, true);

        module.vtextflow2 = textflow.init(panel.init($('div.panel-variant-textflow-2')), d3chord, 'vtf2_', true, true);

        module.ltextflow = textflow.init(panel.init($('div.panel-local-textflow')), d3stemma, 'tf_', false, false);

        module.gtextflow = textflow.init(panel.init($('div.panel-global-textflow')), d3stemma, 'gtf_', true, false);

        panel.create_panel_controls($('div.panel'));

        // this panel is closed by default
        $('div.panel-variant-textflow-2 .panel-slidable').slideUp();
        module.vtextflow2.visible = false;

        // insert css for color palettes
        d3common.insert_css_palette(d3common.generate_css_palette(d3common.labez_palette, d3common.cliques_palette));

        // install event handlers

        // Click on a ms. in the apparatus or in a relatives popup.
        $(document).on('click', '.ms[data-ms-id]', function (event) {
            event.stopPropagation();
            var ms_id = $(event.target).attr('data-ms-id');
            create_relatives_popup(ms_id, module.navigator.passage, event.target);
        });

        // Click on a comparison row in the apparatus or in a relatives popup.
        $(document).on('click', 'tr.comparison[data-ms2-id]', function (event) {
            event.stopPropagation();
            var ms1_id = $(event.currentTarget).attr('data-ms1-id');
            var ms2_id = $(event.currentTarget).attr('data-ms2-id');
            var win = window.open('comparison#ms1=id' + ms1_id + '&ms2=id' + ms2_id, '_blank');
            win.focus();
        });

        // Click on a node in the textflow diagram.
        $(document).on('click', 'div.panel-textflow g.node', function (event) {
            var ms_id = $(event.currentTarget).attr('data-ms-id'); // the g.node, not the circle
            create_relatives_popup(ms_id, module.navigator.passage, event.currentTarget);
        });

        // Click on canvas to close context menus
        $(document).on('click', function (dummy_event) {
            var $menu = $('table.contextmenu');
            $menu.fadeOut(function () {
                return $menu.remove();
            });
        });

        // The user navigated to a new passage.
        $(document).on('ntg.panel.reload', function (event, passage) {
            $('div.panel').trigger('ntg.panel.reload', passage);
        });

        // Simulate user navigation set the passage on all modules.
        if (window.location.hash) {
            var hash = window.location.hash.substring(1);
            module.navigator.set_passage(hash);
        }
    }

    module.init = init;

    window.coherence = module;

    return module;
});

//# sourceMappingURL=coherence.js.map