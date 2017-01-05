/**
 * This module implements the popups that show the relatives of a manuscript.
 *
 * @module relatives
 * @author Marcello Perathoner
 */
define (['jquery', 'lodash', 'd3', 'd3-common', 'tools', 'navigator'],

function ($, _, d3, d3c, tools, nav) {
    'use strict';

    var DEFAULTS = {
        'type'      : 'rel',
        'chapter'   : '0',
        'limit'     : '10',
        'include'   : [],
        'fragments' : [],
        'mode'      : 'rec',
        'labez'     : 'all+lac',
    };

    var URLS = {
        'rel' : 'relatives/',
        'anc' : 'ancestors/',
        'des' : 'descendants/',
    };

    function changed () {
        $ (document).trigger ('ntg.popup.changed');
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
     * Handle toolbar events
     *
     * @function handle_toolbar_events
     *
     * @param event {Object} jQuery event
     */
    function handle_toolbar_events (event) {
        var $panel = $ (event.target).closest ('div.panel');

        event.data = $panel.data ('options');
        tools.handle_toolbar_events (event);
        tools.set_toolbar_buttons ($panel, event.data);

        // replace content
        var ms_id    = $panel.attr ('data-ms-id');
        var url      = URLS[event.data.type] + nav.passage.id + '/' + ms_id
            + '?' + $.param (event.data); // we must use GET, not POST
        var $content = $panel.find ('div.panel-relatives-content');
        $content.load (url + ' div.panel-relatives-content', function () {
            changed ();
        });

        event.stopPropagation ();
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
        $.get (URLS[DEFAULTS.type] + nav.passage.id + '/' + ms_id, DEFAULTS, function (html) {
            // create
            var $popup = $ (html).hide ();
            $popup.appendTo ('body');
            $popup.fadeIn (function () {
                $popup.on ('ntg.popup.visibility', changed);
            });

            // initialize buttons
            var data = $.extend ({}, DEFAULTS);
            $popup.data ('options', data);
            tools.set_toolbar_buttons ($popup, data);
            $popup.find ('.dropdown-toggle').dropdown ();
            tools.create_panel_controls ($popup);

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

            // make draggable
            $popup.draggable ();
            $popup.on ('dragstart', function () {
                $popup.appendTo ('body'); // bring to top
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
    function init () {
        // click on buttons in toolbar
        $ (document).on ('click', 'div.toolbar-relatives input', handle_toolbar_events);
    }

    return {
        'init'                   : init,
        'create_panel'           : create_panel,
        'get_ms_ids_from_popups' : get_ms_ids_from_popups,
    };
});
