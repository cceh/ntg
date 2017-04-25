/**
 * This module implements helper functions and is a container for all stuiff
 * that doesn't fit elsewhere.
 *
 * @module tools
 * @author Marcello Perathoner
 */

define ([],

function () {
    'use strict';

    /**
     * Format a string in python fashion.  "{count} items found"
     *
     * @function format
     *
     * @param {string} s - The string to format
     * @param {dict} data - A dictionary of key: value
     *
     * @return {string} - The formatted string
     */
    function format (s, data) {
        return s.replace (/\{([_\w][_\w\d]*)\}/gm, function (match, p1) {
            return data[p1];
        });
    }

    /**
     * Return a map of the query parameters in the url of this page.
     *
     * @function get_query_params
     *
     * @return {Oject} A map of parameter = value
     */

    function get_query_params () {
        var query = {};
        location.search.substr (1).split ('&').forEach (function (item) {
            var s = item.split ('=');
            query[s[0]] = s[1];
        });
        return query;
    }

    /**
     * Position a context menu aside an svg element.
     *
     * Since jQuery doesn't grok the SVG DOM, we have to calculate the position
     * of the menu manually.
     *
     * @param menu
     * @param target
     */

    function svg_contextmenu (menu, target) {
        $ (target).closest ('div.panel').append (menu);

        var rect = target.getBoundingClientRect ();
        var bodyRect = document.body.getBoundingClientRect (); // account for scrolling
        var ev = new $.Event ('click');
        ev.pageY = rect.top   - bodyRect.top;
        ev.pageX = rect.right - bodyRect.left;
        menu.position ({
            'my'        : 'left top',
            'collision' : 'flipfit flip',
            'of'        : ev,
        });
    }

    function close_alert () {
        var $parent = $ (this).closest ('.alert');
        $parent.slideUp (function () { $parent.remove (); });
    }

    function init () {
        var selector = '[data-dismiss="alert"]';
        // Enable the closing button of the flashed alert messages
        $ (document).on ('click', selector, close_alert);
        // Close flashed messages after delay
        var $alerts = $ (selector);
        var timeout = $alerts.length * 5000;
        setTimeout (function () { $alerts.each (close_alert); }, timeout);
    }

    return {
        'init'             : init,
        'format'           : format,
        'get_query_params' : get_query_params,
        'svg_contextmenu'  : svg_contextmenu,
    };
});
