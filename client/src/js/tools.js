/**
 * This module implements helper functions and is a container for all stuff
 * that doesn't fit elsewhere.
 *
 * @module tools
 * @author Marcello Perathoner
 */

import $      from 'jquery';
import _      from 'lodash';

/**
 * Format a string in python fashion.  "{count} items found"
 *
 * @function format
 *
 * @param {String} s  - The string to format
 * @param {dict} data - A dictionary of key: value
 *
 * @returns {String} The formatted string
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
 * @param {String} s - The input string
 *
 * @returns {String} The transformed string
 */

export function natural_sort (s) {
    return s.replace (/\d+/g, (match, dummy_offset, dummy_string) => match.length + match);
}

/**
 * The inverse of the jQuery.param () function.
 *
 * @function deparam
 *
 * @param {String} query_string - A string in the form "p=1&q=2"
 *
 * @returns {Object} { p : 1, q : 2 }
 */

export function deparam (query_string) {
    var params = {};
    query_string.split ('&').forEach (item => {
        if (item.length) {
            var s = item.split ('=').map (i => decodeURIComponent (i.replace ('+', ' ')));
            params[s[0]] = s[1];
        }
    });
    return params;
}

/**
 * Display an auto-closing alert window.
 *
 * @function xhr_alert
 *
 * @param {Object} reason - The parameter that was passed to Promise.then ()
 *                          or Promise.catch ().
 * @param {jQuery} $card - The card to append the window to.
 */

export function xhr_alert (reason, $card) {
    if (!$card) {
        $card = $ ('body');
    }

    let message = '';
    let category = '';

    if (reason.data && reason.data.message) {
        message = reason.data.message;
        category = 'success';
    }
    if (reason.response && reason.response.data && reason.response.data.message) {
        message = reason.response.data.message;
        category = 'danger';
    }

    var $alert = $ (`
        <div class="alert alert-${category} alert-dismissible alert-margins" role="alert">
            <button type="button" class="close" data-dismiss="alert"
                    aria-label="Close"><span aria-hidden="true">&times;</span></button>
            ${message}
        </div>
        `);
    $alert.appendTo ($card).hide ();
    $alert.on ('click', 'button[data-dismiss="alert"]', function () {
        $alert.stop (true, true).slideUp (function () { $alert.remove (); });
    });
    $alert.slideDown ().delay (5000).slideUp ();
}

/**
 * Breadth first search in graph
 *
 * @function bfs
 *
 * @param {Object} edges - The edges list
 * @param {String} start - The start node id
 *
 * @returns A list of node ids in breadth-first order
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

export function slide_from ($el, old_height, set_auto = true) {
    // slide an element to its new height
    $el.height (1);
    const new_height = $el.prop ('scrollHeight');
    $el.height (old_height);
    $el.animate ({ 'height' : new_height }, 300, () => {
        if (set_auto) {
            $el.height ('auto');
        };
        $el.animate ({ 'opacity' : 1.0 }, 300);
    });
}

export function save_height ($el) {
    return $el.height ();
}

export default {
    format,
    natural_sort,
    deparam,
    xhr_alert,
    bfs,
    slide_from,
    save_height,
};
