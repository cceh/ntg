/**
 * This module implements helper functions.
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

    function get_query_params () {
        var query = {};
        location.search.substr (1).split ('&').forEach (function (item) {
            var s = item.split ('=');
            query[s[0]] = s[1];
        });
        return query;
    }

    return {
        'format'           : format,
        'get_query_params' : get_query_params,
    };
});
