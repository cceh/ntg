/**
 * This module implements helper functions and is a container for all stuff
 * that doesn't fit elsewhere.
 *
 * @module client/tools
 * @author Marcello Perathoner
 */

import { pick }  from 'lodash';
import qs        from 'qs';
import Velocity  from 'velocity-animate/velocity';

Velocity.defaults.duration = 250;
const velocity_opts = { 'duration' : 250 };


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

const qs_options = {
    'arrayFormat' : 'brackets',
    'skipNulls'   : true,
};

/**
 * Parse a query string.
 *
 * @function deparam
 *
 * @param {String} query_string - A string in the form "p=1&q=2"
 *
 * @returns {Object} { p : 1, q : 2 }
 */

export function deparam (query_string) {
    return qs.parse (query_string, qs_options);
}

/**
 * Build a query string.
 *
 * @function param
 *
 * @param {Object} params    - Object of params, eg. { p : 1, q : 2 }
 * @param {Array}  pick_list - Pick only these members, eg. ['p', 'q']
 *
 * @returns {String} - A string in the form "p=1&q=2"
 */

export function param (params, pick_list = null) {
    return qs.stringify ((pick_list ? pick (params, pick_list) : params), qs_options);
}

export function set_hash (params, pick_list = null) {
    window.location.hash = '#' + param (params, pick_list);
}

export function get_hash () {
    // FIXME ??? window.location.hash ? window.location.hash.substring (1) : '';
    return deparam (window.location.hash.substring (1));
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
        for (const n of edges.filter (is_adjacent)) {
            var id = n.elems[1].id;
            if (ids.indexOf (id) === -1) {
                ids.push (id);
                queue.push (id);
            }
        }
        cur = queue.shift ();
    }
    return ids;
}

export function get_scroll_height (el) {
    let height = el.scrollHeight;
    if (height === el.clientHeight) {
        // content height is smaller than element height
        const old_height = el.style.height;
        el.style.height = '1px';
        height = el.scrollHeight;
        el.style.height = old_height;
    }
    return parseInt (height, 10);
}

export function slide_fade_in (el, auto = false) {
    return el
        .velocity ({ 'height' : get_scroll_height (el) }, {
            'complete' : () => {
                if (auto) {
                    el.style.height = 'auto';
                }
            }, ... velocity_opts })
        .velocity ({ 'opacity' : 1.0 }, velocity_opts);
}

export function slide_fade_out (el) {
    // actually fade then slide out
    return el
        .velocity ({ 'opacity' : 0.0 }, velocity_opts)
        .velocity ({ 'height' : 0 }, velocity_opts);
}

export function fade_out (el) {
    return el.velocity ({ 'opacity' : 0.0 }, velocity_opts);
}

export function fade_in (el) {
    return el.velocity ({ 'opacity' : 1.0 }, velocity_opts);
}

export default {
    format,
    natural_sort,
    param,
    deparam,
    set_hash,
    get_hash,
    bfs,
    get_scroll_height,
    slide_fade_in,
    slide_fade_out,
    fade_in,
    fade_out,
    velocity_opts,
};
