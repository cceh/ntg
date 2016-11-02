// This is a RequireJS module.

define (['jquery', 'lodash', 'd3', 'd3-stemma', 'tools', 'bootstrap', 'bootstrap-slider', 'jquery-ui'],

function ($, _, d3, d3stemma, tools) {
    'use strict';

    var DEFAULTS = {
        'mode'         : 'rec',
        'chapter'      : '0',
        'connectivity' : '10',
        'include'      : [],
    };

    function changed () {
        // currently unused
        $ (document).trigger ('ntg.coherence_attestation.changed');
    }

    function options (event) {
        var $target = $ (event.target);
        var $panel  = $target.closest ('div.panel');
        var opts    = $panel.data ('options');

        tools.handle_bootstrap_buttons (event);

        d3stemma.init_json ('/coherence.json/' + opts.pass_id + '/attestation/' + opts.labez
                            + '?' + $.param (opts), opts.wrapper_selector, 'ca_');
        changed ();
        event.stopPropagation ();
    }

    function init (params) {
        $ (document).off ('.data-api');

        var $panel = $ ('div.panel-coherence-attestation');
        $panel.data ('options', $.extend (params, DEFAULTS));

        $panel.find ('.dropdown-toggle').dropdown ();

        $panel.find ('input[name="connectivity"]').bootstrapSlider ({
            'value' : 10,
            'ticks' : [1, 5, 10, 20],
        });

        options (new $.Event ('init', { 'target': $panel }));

        // slider
        $ (document).on ('slideStop', 'div.toolbar-coherence-attestation input[name="connectivity"]', options);
        // click on buttons in toolbar
        $ (document).on ('click', 'div.toolbar-coherence-attestation input', options);
    }

    // return an object that defines this module
    return {
        'init' : init,
    };
});
