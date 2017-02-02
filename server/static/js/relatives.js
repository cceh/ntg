/**
 * This module implements the popups that show the relatives of a manuscript.
 *
 * @module relatives
 * @author Marcello Perathoner
 */
define (['jquery',
         'lodash',
         'd3',
         'd3-common',
         'tools',
         'panel',
         'navigator',
         'css!relatives-css',
],

function ($, _, d3, d3c, tools, panel, nav) {
    'use strict';

    function changed () {
        $ (document).trigger ('changed.ntg.relatives');
    }

    /**
     * Get a list of the mss. currently displayed in any open panel.  Get either
     * the 'source' ms. -- the ms. the panel is all about -- or the target
     * mss. -- the mss. related to the 'source' ms.
     *
     * N.B.  When you open a panel, the nodes listed in the panel are also
     * highlighted in the affinity cloud.  The affinity cloud uses this function
     * to find out which nodes to highlight.
     *
     * @function get_ms_ids_from_popups
     *
     * @param {string} what - 'source' or 'target'
     *
     * @return {Object} - Array of ms_ids
     */
    function get_ms_ids_from_popups (what) {
        var ms_ids = {};
        $ ('div.panel-relatives div:visible .hilite-' + what + '[data-ms-id]').each (function () {
            ms_ids[$ (this).attr ('data-ms-id')] = true;
        });
        return ms_ids;
    }

    /**
     * Load new data.
     *
     * @function load_passage
     */
    function load_passage (dummy_passage) {
        var instance = this;

        // replace content
        var ms_id = instance.$panel.attr ('data-ms-id');
        var url   = 'relatives.json/' + nav.passage.id + '/' + ms_id
            + '?' + $.param (instance.data); // we must use GET, not POST
        var $content = instance.$panel.find ('div.panel-relatives-content');
        $content.load (url + ' table.relatives', function () {
            changed ();
        });

        var p1 = panel.load_labez_dropdown (
            instance.$toolbar.find ('div.toolbar-labez'),
            nav.passage.id, 'labez', [['all', 'All'], ['all+lac', 'All+Lac']]);
        var p2 = panel.load_chapter_dropdown (
            instance.$toolbar.find ('div.toolbar-chapter'),
            'chapter', [['0', 'All'], ['x', 'This']]);
        return $.when (p1, p2).done (function () {
            panel.set_toolbar_buttons (instance.$toolbar, instance.data);
            // Maybe we changed chapter while navigating.  Set a new chapter.
            instance.$toolbar.find ('div.toolbar-chapter input[data-opt = "x"]')
                .attr ('data-opt', nav.passage.chapter);
            changed ();
        });
    }

    /**
     * Initialize the module.
     *
     * @function init
     */
    function init (instance) {
        instance.load_passage = load_passage;
        $.extend (instance.data, {
            'type'      : 'rel',
            'chapter'   : '0',
            'limit'     : '10',
            'include'   : [],
            'fragments' : [],
            'mode'      : 'rec',
            'labez'     : 'all+lac',
        });

        return instance;
    }

    /**
     * Create a popup panel.
     *
     * @function create_panel
     *
     * @param ms_id {integer} The manuscript id.
     * @param elem {DOM} A DOM element relative to which to position the popup.
     */
    function create_panel (ms_id, target) {
        $.get ('relatives/' + nav.passage.id + '/' + ms_id, function (html) {
            // create
            var $popup = $ (html).hide ();
            $popup.appendTo ('#floating-panels');
            $popup.fadeIn ();
            $popup.on ('changed.panel.visibility', changed);

            var instance = init (panel.init ($popup));
            instance.load_passage ().done (function () {
                // position popup
                var rect = target.getBoundingClientRect ();
                var bodyRect = document.body.getBoundingClientRect (); // account for scrolling
                var event = new $.Event ('click');
                event.pageY = rect.top - bodyRect.top;
                event.pageX = rect.left - bodyRect.left + (rect.width / 2.0);
                $popup.position ({
                    'my'        : 'center bottom-3',
                    'collision' : 'flipfit flip',
                    'of'        : event,
                });
            });

            panel.create_panel_controls ($popup);
            // make draggable
            $popup.draggable ();
            $popup.on ('dragstart', function () {
                // FIXME: $popup.appendTo ('#floating-panels'); // bring to top
            });

            // notify others
            changed ();
        });
    }

    return {
        'init'                   : init,
        'create_panel'           : create_panel,
        'get_ms_ids_from_popups' : get_ms_ids_from_popups,
    };
});
