/**
 * This module implements helper functions and is a container for all stuiff
 * that doesn't fit elsewhere.
 *
 * @module tools
 * @author Marcello Perathoner
 */

import _ from 'lodash';

/**
 * Format a string in python fashion.  "{count} items found"
 *
 * @function format
 *
 * @param {string} s  - The string to format
 * @param {dict} data - A dictionary of key: value
 *
 * @return {string} - The formatted string
 */

export function format (s, data) {
    return s.replace (/\{([_\w][_\w\d]*)\}/gm, (match, p1) => data[p1]);
}

/**
 * Transform a string so that numbers in the string sort naturally.
 *
 * Transform any contiguous run of digits so that it sorts
 * naturally during an alphabetical sort. Every run of digits gets
 * the length of the run prepended, eg. 123 => 3123, 123456 =>
 * 6123456.
 *
 * @function natural_sort
 *
 * @param {string} s - The input string
 *
 * @return {string} - The transformed string
 */

export function natural_sort (s) {
    return s.replace (/\d+/g, (match, dummy_offset, dummy_string) => match.length + match);
}

/**
 * The inverse of the jQuery.param () function.
 *
 * @function deparam
 *
 * @param {string} query_string - A string in the form "p=1&q=2"
 *
 * @return {Object} { p : 1, q : 2 }
 */

export function deparam (query_string) {
    var params = {};
    query_string.split ('&').forEach (item => {
        var s = item.split ('=').map (i => decodeURIComponent (i.replace ('+', ' ')));
        params[s[0]] = s[1];
    });
    return params;
}

/**
 * Position a context menu aside an svg element.
 *
 * Since jQuery doesn't grok the SVG DOM, we have to calculate the
 * position of the menu manually.
 *
 * @function svg_contextmenu
 *
 * @param {Object} menu   - The menu
 * @param {Object} target - The DOM object to attach the menu to
 */

export function svg_contextmenu (menu, target) {
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

/**
 * Display an auto-closing alert window.
 *
 * @function xhr_alert
 *
 * @param {Object} xhr - The server response containing the
 *                          message.  The JSON response must
 *                          contain an Object with a message
 *                          field.
 * @param {jQuery} $panel - The panel to append the window to.
 */

export function xhr_alert (reason, $panel) {
    if (!$panel) {
        $panel = $ ('body');
    }
    var category = 'danger';

    if (reason.response) {
        var $alert = $ (`
            <div class="alert alert-${category} alert-dismissible alert-margins" role="alert">
                <button type="button" class="close" data-dismiss="alert"
                        aria-label="Close"><span aria-hidden="true">&times;</span></button>
                ${reason.response.data.message}
             </div>
            `);
        $alert.appendTo ($panel).hide ();
        $alert.on ('click', 'button[data-dismiss="alert"]', function () {
            $alert.stop (true, true).slideUp (function () { $alert.remove (); });
        });
        $alert.slideDown ().delay (5000).slideUp ();
    }
}

/**
 * Breadth first search in graph
 *
 * @function bfs
 *
 * @param {Object} edges - The edges list
 * @param {string} start - The start node id
 *
 * @return A list of node ids in breadth-first order
 */

export function bfs (edges, start) {
    var ids   = [start];
    var queue = [];
    var cur   = start;
    function is_adjacent (edge) {
        return edge.elems[0].id === cur;
    }
    while (cur) {
        _.forEach (_.filter (edges, is_adjacent), function (n) {
            var id = n.elems[1].id;
            if (_.indexOf (ids, id) === -1) {
                ids.push (id);
                queue.push (id);
            }
        });
        cur = queue.shift ();
    }
    return ids;
}

export function slide_from ($el, old_height) {
    // slide an element to its new height
    const new_height = $el.prop ('scrollHeight');
    $el.height (old_height);
    $el.animate ({ 'height' : new_height }, 300, () => {
        $el.height ('auto');
        $el.animate ({ 'opacity' : 1.0 }, 300);
    });
}

export function save_height ($el) {
    return $el.prop ('scrollHeight');
}

export default {
    format,
    natural_sort,
    deparam,
    svg_contextmenu,
    xhr_alert,
    bfs,
    slide_from,
    save_height,
};
