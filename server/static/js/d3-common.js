/**
 * This module contains common functions built around the D3 library.
 *
 * @module d3-common
 * @author Marcello Perathoner
 */

define (['jquery', 'd3', 'lodash'], function ($, d3, _) {
    'use strict';

    /**
     * A D3 color palette suitable for attestations.
     *
     * @var {d3.scale} attestation_palette
     */
    var attestation_palette = d3.scaleOrdinal ()
        .domain (d3.range (20))
        .range (['#888888', '#1f77b4', '#2ca02c', '#d62728',
                 '#e7ba52', '#ff7f0e', '#9467bd', '#8c564b',
                 '#e377c2', '#17becf', '#aec7e8', '#ffbb78',
                 '#98df8a', '#ff9896', '#c5b0d5', '#c49c94',
                 '#f7b6d2', '#dbdb8d', '#9edae5', '#7f7f7f']);

    /**
     * Generates a CSS color palette from a D3 scale.
     *
     * @function generate_css_palette
     *
     * @param d3_scale {d3.scale} - The color palette as D3 scale.
     *
     * @return {string} - The color palette as CSS
     */
    function generate_css_palette (d3_scale) {
        var style;
        function labezFromCharCode (code) {
            return code > 0 ? String.fromCharCode (code + 96) : 'z';
        }
        style = _.map (_.zip (d3_scale.domain (), d3_scale.range ()), function (pair) {
            var code = labezFromCharCode (pair[0]);
            return '.fg_labez[data-labez="' + code + '"] { color: ' + pair[1] +
                ' !important; fill: ' + pair[1] + '; }\n' +
                '.bg_labez[data-labez="' + code + '"] { background-color: ' +
                pair[1] + ' !important; }';
        });
        style.unshift ('.fg_labez { color: black !important; fill: black; }');
        style.unshift ('.bg_labez { background-color: black !important; }');
        return style.join ('\n');
    }

    /**
     * Insert a CSS color palette into the DOM making it active.
     *
     * @function insert_css_palette
     *
     * @param css {string} - The color palette as CSS.
     */
    function insert_css_palette (css) {
        $ ('<style type="text/css">' + css + '</style>').appendTo ('head');
    }

    // For D3 and jQuery Interoperability see:
    //   http://collaboradev.com/2014/03/18/d3-and-jquery-interoperability/

    /**
     * Convert a D3 selection object into a jQuery selection object.
     *
     * @function to_jquery
     *
     * @param {d3.selection} d3_selection - The D3 selection object
     *
     * @return {jQuery.selection} - The jQuery selection object.
     */
    function to_jquery (d3_selection) {
        return $ (d3_selection.nodes ());
    }

    /**
     * Convert a jQuery selection object into a D3 selection object.
     *
     * @function to_d3
     *
     * @param {jQuery.selection} jquery_selection - The jQuery selection object
     *
     * @return {D3.selection} - The D3 selection object.
     */
    function to_d3 (jquery_selection) {
        return d3.selectAll (jquery_selection.toArray ());
    }

    return {
        'attestation_palette'  : attestation_palette,
        'insert_css_palette'   : insert_css_palette,
        'generate_css_palette' : generate_css_palette,
        'to_jquery'            : to_jquery,
        'to_d3'                : to_d3,
    };
});
