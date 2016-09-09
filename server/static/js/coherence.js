// This is a RequireJS module.
define (['jquery', 'd3', 'd3-common', 'lodash', 'relatives', 'd3-force', 'jquery-ui'],

function ($, d3, d3c, _) {
    'use strict';

    function node_data (d, labez_ord) {
        return labez_ord > 0 ? String.fromCharCode (labez_ord + 96) : 'lac';
    }

    function init () {
        // click on data-ms-id
        $ (document).on ('click', '.ms[data-ms-id]', function (event) {
            var ms_id = $ (event.target).attr ('data-ms-id');
            var node = $ ('g[data-ms-id="' + ms_id + '"]');
            node.d3_tooltip ();
            node.d3_tooltip ('open');
        });
        // click on data-href
        $ (document).on ('click', 'circle[data-href]', function (event) {
            window.location = $ (event.target).attr ('data-href');
        });
    }

    function set_attestation (pass_id) {
        // Change the color of the nodes in the graph to reflect the attestation
        // of a passage.  Also change the color of the items in the attestation
        // list which functions as legend.

        d3c.insert_css_attestation_colors ();

        d3.json ('/coherence.json/' + pass_id, function (error, json) {
            if (error) {
                throw error;
            }

            d3.selectAll ('#svg-wrapper circle.node')
                .attr ('data-labez', function (d) {
                    d.labez = _.get (json.attestations, d.id, 1); // set labez on data!
                    return node_data (d, d.labez);
                });
        });
    }

    // return an object that defines this module
    return {
        'init'            : init,
        'set_attestation' : set_attestation,
    };
});
