/**
 * This module implements the popups that show the relatives of a manuscript.
 *
 * @module relatives
 *
 * @author Marcello Perathoner
 */

define ([
    'jquery',
    'lodash',
    'tools',
    'panel',
    'css!relatives-css',
],

function ($, _, tools, panel) {
    function changed () {
        $ (document).trigger ('changed.ntg.relatives');
    }

    /**
     * Get a list of the mss. currently displayed in the panel.
     *
     * Get either the 'source' ms. -- the ms. the panel is all about -- or the
     * 'target' mss. -- the mss. related to the 'source' ms.  Only returns
     * target mss. if the panel body is open.
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
     * Display new data in the popup after the user navigated to a different
     * passage.
     *
     * @function load_passage
     *
     * @param {Object} passage - The new passage
     */

    function load_passage (passage) {
        var instance = this;
        instance.data.passage = passage;

        // replace content
        var ms_id = instance.$panel.attr ('data-ms-id');
        var url   = 'relatives.html/' + passage.pass_id + '/id' + ms_id
            + '?' + $.param (instance.data); // we must use GET, not POST
        var p0 = $.get (url);
        var p1 = panel.load_labez_dropdown (
            instance.$toolbar.find ('div.toolbar-labez'), passage.pass_id, 'labez',
            [['all', 'All'], ['all+lac', 'All+Lac']], []);
        var p2 = panel.load_range_dropdown (
            instance.$toolbar.find ('div.toolbar-range'), passage.pass_id, 'range',
            [{ 'range' : 'This', 'value' : 'x' }], []);

        p0.done (function (html) {
            var $html = $ (html);
            // replace inner div to keep close button etc.
            var $caption_wrap = instance.$panel.find ('div.panel-relatives-caption div');
            var $heading_wrap = instance.$panel.find ('div.panel-relatives-metrics');
            var $table_wrap   = instance.$panel.find ('div.panel-relatives-content');
            $caption_wrap.html ($html.find ('div.relatives-caption'));
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
     * Position the popup panel relative to the element that created the popup.
     *
     * @function position_popup
     *
     * @param {DOM} target    - A DOM element relative to which to position the popup.
     */

    function position_popup (target) {
        var instance = this;

        var rect = target.getBoundingClientRect ();
        var bodyRect = document.body.getBoundingClientRect (); // account for scrolling
        var event = new $.Event ('click');
        event.pageY = rect.top  - bodyRect.top  + (rect.height / 2.0);
        event.pageX = rect.left - bodyRect.left + (rect.width / 2.0);
        instance.$panel.position ({
            'my'        : 'center bottom-15',
            'collision' : 'flipfit flip',
            'of'        : event,
        });
    };

    /**
     * Initialize the module.
     *
     * @function init
     *
     * @param {Object} instance - The panel module instance to inherit from.
     */

    function init (instance) {
        instance.load_passage = load_passage;
        instance.position_popup = position_popup;
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

    /**
     * Create a popup panel.
     *
     * @function create_popup
     *
     * @param {integer} ms_id  - The manuscript id.
     * @param {Object} passage - The passage.
     * @param {DOM} target     - A DOM element relative to which to position the popup.
     */

    function create_popup (ms_id, passage, target) {
        // get the popup skeleton
        $.get ('relatives/id' + ms_id, function (html) {
            // append the skeleton to the floating panels section
            var $popup = $ (html).hide ();
            $popup.appendTo ('#floating-panels');
            $popup.fadeIn ();
            $popup.on ('changed.panel.visibility', changed);

            var instance = init (panel.init ($popup));
            instance.load_passage (passage).done (function () {
                instance.position_popup (target);
            });

            panel.create_panel_controls ($popup);
            $popup.draggable ();

            deferred.resolve ();
            // notify others
            changed ();
        });
    }

    return {
        'init'                   : init,
        'create_popup'           : create_popup,
        'get_ms_ids_from_popups' : get_ms_ids_from_popups,
    };
});
