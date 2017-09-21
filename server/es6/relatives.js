/**
 * This module implements the popups that show the relatives of a manuscript.
 *
 * @module relatives
 * @author Marcello Perathoner
 */
define ([
    'jquery',
    'lodash',
    'd3',
    'd3-common',
    'tools',
    'panel',
    'navigator',
    'css!relatives-css',
],

function ($, _, d3, d3c, tools, panel, nav) {
    function changed () {
        $ (document).trigger ('changed.ntg.relatives');
    }

    /**
     * Get a list of the mss. currently displayed in any open panel.  Get either
     * the 'source' ms. -- the ms. the panel is all about -- or the target
     * mss. -- the mss. related to the 'source' ms.
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

    function load_passage (passage) {
        var instance = this;
        instance.data.passage = passage;

        // replace content
        var ms_id = instance.$panel.attr ('data-ms-id');
        var url   = 'relatives.html/' + passage.pass_id + '/' + ms_id
            + '?' + $.param (instance.data); // we must use GET, not POST
        var $heading_wrap = instance.$panel.find ('div.panel-relatives-metrics');
        var $table_wrap   = instance.$panel.find ('div.panel-relatives-content');

        var p0 = $.get (url);
        var p1 = panel.load_labez_dropdown (
            instance.$toolbar.find ('div.toolbar-labez'), passage.pass_id, 'labez',
            [['all', 'All'], ['all+lac', 'All+Lac']], []);
        var p2 = panel.load_range_dropdown (
            instance.$toolbar.find ('div.toolbar-range'), passage.pass_id, 'range',
            [{ 'range' : 'This', 'value' : 'x' }], []);

        p0.done (function (html) {
            var $html = $ (html);
            $heading_wrap.html ($html.find ('div.relatives-metrics'));
            $table_wrap.html   ($html.find ('table.relatives'));
        });

        return $.when (p0, p1, p2).done (function () {
            panel.set_toolbar_buttons (instance.$toolbar, instance.data);
            // Maybe we changed range while navigating.  Set a new range.
            instance.$toolbar.find ('div.toolbar-range input[data-opt = "x"]')
                .attr ('data-opt', passage.chapter);
            changed ();
        });
    }

    /**
     * Create a popup panel.
     *
     * @function create_panel
     *
     * @param {integer} ms_id - The manuscript id.
     * @param {DOM} target    - A DOM element relative to which to position the popup.
     */

    function create_panel (ms_id, target) {
        $.get ('relatives/' + nav.passage.pass_id + '/' + ms_id, function (html) {
            // create
            var $popup = $ (html).hide ();
            $popup.appendTo ('#floating-panels');
            $popup.fadeIn ();
            $popup.on ('changed.panel.visibility', changed);

            var instance = init (panel.init ($popup));
            instance.load_passage (nav.passage).done (function () {
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
            $popup.draggable ();
            $popup.on ('dragstart', function () {
                // FIXME: $popup.appendTo ('#floating-panels'); // bring to top
            });

            // notify others
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
            'range'     : 'All',
            'limit'     : '10',
            'include'   : [],
            'fragments' : [],
            'mode'      : 'sim',
            'labez'     : 'all+lac',
        });

        // Install handler for reloading
        $ (document).on ('ntg.panel.reload', function (event, passage) {
            instance.load_passage (passage);
        });

        return instance;
    }

    return {
        'init'                   : init,
        'create_panel'           : create_panel,
        'get_ms_ids_from_popups' : get_ms_ids_from_popups,
    };
});
