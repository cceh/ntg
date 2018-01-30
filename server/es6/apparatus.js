/**
 * This module displays the apparatus table.  It retrieves the apparatus data in
 * JSON format and builds a list of readings and of the manuscripts that attest
 * that reading.
 *
 * @module apparatus
 * @author Marcello Perathoner
 */

define ([
    'jquery',
    'lodash',
    'tools',
    'toolbar',
    'css!apparatus-css',
],

function ($, _, tools, toolbar) {
    function changed () {
        // currently unused
        $ (document).trigger ('ntg.apparatus.changed');
    }

    /**
     * Load a new passage.
     *
     * @function load_passage
     *
     * @param {Object} passage - Which passage to load.
     *
     * @return {Promise} Promise, resolved when the new passage has loaded.
     */
    function load_passage (passage) {
        let instance = this;
        instance.data.passage = passage;
        let new_list;

        let xhr = $.getJSON ('apparatus.json/' + passage.pass_id);
        xhr.done ((json) => {
            let labez_grouper  = (g) => g.labez;
            let clique_grouper = (g) => g.labez_clique;

            let grouper = _.includes (instance.data.cliques, 'cliques') ? clique_grouper : labez_grouper;

            let readings = [];
            let html = [];

            // load readings into dictionary for faster lookup
            _.forEach (json.data.readings, (reading) => {
                readings[reading.labez] = reading.lesart;
            });

            // group manuscripts and loop over groups
            _.forEach (_.groupBy (_.sortBy (json.data.manuscripts, grouper), grouper), (group) => {
                let data = {
                    'pass_id'      : passage.pass_id,
                    'labez'        : group[0].labez,
                    'labez_clique' : group[0].labez_clique,
                    'group'        : grouper (group[0]),
                };

                data.reading = _.get (readings, data.labez, 'Error: no reading found');

                html.push ('<li class="list-group-item">');
                html.push ('<h4 class="list-group-item-heading">');
                html.push (tools.format (
                    '<a data-labez="{labez}" class="apparatus-labez fg_labez">{group} {reading}</a></h4>', data
                ));

                html.push ('<ul class="list-group-item-text attesting-mss list-inline">');
                _.forEach (_.sortBy (group, ['hsnr']), (item) => {
                    let data2 = {
                        'ms_id'     : item.ms_id,
                        'hs'        : item.hs,
                        'certainty' : (item.certainty === 1.0) ? '' : '?',
                    };
                    html.push (tools.format (
                        '<li><a class="ms" data-ms-id="{ms_id}">{hs}{certainty}.</a></li>', data2));
                });
                html.push ('</ul>');
                html.push ('</li>');
            });
            new_list = $ (html.join (''));
        });

        let faded_promise = instance.$wrapper.animate ({ 'opacity' : 0.0 }, 300);

        return $.when (xhr, faded_promise).done (() => {
            let $wrapper = instance.$wrapper;
            let old_height = $wrapper.prop ('scrollHeight');
            $wrapper.html (new_list);
            let new_height = $wrapper.prop ('scrollHeight');
            $wrapper.height (old_height);
            $wrapper.animate ({ 'height' : new_height }, 300, () => {
                $wrapper.height ('auto');
                $wrapper.animate ({ 'opacity' : 1.0 }, 300);
            });
            toolbar.set_toolbar_buttons (instance.$toolbar, instance.data);
            changed ();
        });
    }

    /**
     * Show the attestation in the Coherence panel and scroll to it.
     *
     * @function goto_attestation
     *
     * @param {Object} event - The event
     */

    function goto_attestation (event) {
        event.stopPropagation ();

        let instance = window.coherence.ltextflow;
        let labez = $ (event.currentTarget).attr ('data-labez');
        instance.data.labez = labez;
        instance.load_passage (instance.data.passage);

        $ ('html, body').animate ({
            'scrollTop' : $ ('div.panel-local-textflow').offset ().top,
        }, 500);
    }

    /**
     * Initialize the module.
     *
     * @function init
     *
     * @param {Object} instance - The panel module instance to inherit from.
     *
     * @returns {Object} - The module instance object.
     */
    function init (instance) {
        instance.load_passage = load_passage;
        instance.$wrapper = instance.$panel.find ('.panel-content');
        $.extend (instance.data, {
            'passage' : null,
            /* Show readings or cliques. */
            'cliques' : [],
        });

        // Click on attestation
        $ (document).on ('click', 'a.apparatus-labez', goto_attestation);

        return instance;
    }

    return {
        'init' : init,
    };
});
