// This is a RequireJS module.
define (['jquery', 'lodash', 'tools', 'd3', 'd3-common', 'd3-stemma', 'd3-force',
         'relatives', 'coherence-attestation', 'bootstrap'],

function ($, _, tools, d3, d3common, d3stemma, d3force, relatives, ca) {
    'use strict';

    function init (params) {
        var pass_id = params.pass_id;

        $ (document).off ('.data-api');
        $.fn.bootstrapTooltip = $.fn.tooltip.noConflict ();

        relatives.init (pass_id);

        d3stemma.init_json (
            '/stemma.json/' + pass_id,
            '#local-stemma-wrapper',
            'local_stemma_'
        );

        ca.init ($.extend (params, {
            'wrapper_selector' : '#passage-stemma-wrapper',
        }));

        d3force.init ('#force-layout-wrapper');
        d3force.set_attestation (pass_id);

        d3common.insert_css_attestation_colors ();

        // click on ms in list of labez or in relatives popup
        $ (document).on ('click', '.ms[data-ms-id]', function (event) {
            var $target = $ (event.target);
            relatives.init_tooltip ($target, pass_id);
            $target.relatives_tooltip ('open');
        });
    }

    // return an object that defines this module
    return {
        'init' : init,
    };
});
