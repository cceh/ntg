// This is a RequireJS module.
define (['jquery', 'd3', 'lodash'], function ($, d3, _) {
    'use strict';

    var attestation_color = d3.scaleOrdinal ()
        .domain (d3.range (20))
        .range (['#cccccc', '#1f77b4', '#2ca02c', '#d62728',
                 '#e7ba52', '#ff7f0e', '#9467bd', '#8c564b',
                 '#e377c2', '#17becf', '#aec7e8', '#ffbb78',
                 '#98df8a', '#ff9896', '#c5b0d5', '#c49c94',
                 '#f7b6d2', '#dbdb8d', '#9edae5', '#7f7f7f']);

    function generate_attestation_colors_css (d3_scale) {
        var style;
        function labezFromCharCode (code) {
            return code > 0 ? String.fromCharCode (code + 96) : 'lac';
        }
        style = _.map (_.zip (d3_scale.domain (), d3_scale.range ()), function (pair) {
            var code = labezFromCharCode (pair[0]);
            return '.fg_labez[data-labez="' + code + '"] { color: ' + pair[1] +
                ' !important; fill: ' + pair[1] + '; }\n' +
                '.bg_labez[data-labez="' + code + '"] { background-color: ' +
                pair[1] + ' !important; }';
        });
        style.push ('.fg_labez[data-labez="all"] { color: black !important; fill: black; }');
        style.push ('.bg_labez[data-labez="all"] { background-color: black !important; }');
        style.push ('.fg_labez[data-labez="all+lac"] { color: black !important; fill: black; }');
        style.push ('.bg_labez[data-labez="all+lac"] { background-color: black !important; }');
        return style.join ('\n');
    }

    function insert_css_attestation_colors () {
        var css = generate_attestation_colors_css (attestation_color);
        $ ('<style type="text/css">' + css + '</style>').appendTo ('head');
    }

    // For D3 and jQuery Interoperability see:
    //   http://collaboradev.com/2014/03/18/d3-and-jquery-interoperability/

    function to_jquery (d3_selection) {
        return $ (d3_selection.nodes ());
    }

    function to_d3 (jquery_selection) {
        return d3.selectAll (jquery_selection.toArray ());
    }

    // return an object that defines this module
    return {
        'insert_css_attestation_colors'   : insert_css_attestation_colors,
        'attestation_color'               : attestation_color,
        'generate_attestation_colors_css' : generate_attestation_colors_css,
        'to_jquery'                       : to_jquery,
        'to_d3'                           : to_d3,
    };
});
