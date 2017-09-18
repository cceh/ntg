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
    'panel',
    'bootstrap',
    'css!apparatus-css',
],

function ($, _, tools, panel) {
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
     */
    function load_passage (passage) {
        this.data.passage = passage;

        var that = this;
        var new_list;
        var json_deferred = new $.Deferred ();

        $.getJSON ('apparatus.json/' + passage.pass_id, function (json) {
            var labez_grouper  = function (g) { return g.labez; };
            var clique_grouper = function (g) { return g.labez + (g.clique || ''); };

            var grouper = _.includes (that.data.cliques, 'cliques') ? clique_grouper : labez_grouper;

            var readings = [];
            var html = [];

            // load readings into dictionary for faster lookup
            _.forEach (json.data.readings, function (reading) {
                readings[reading.labez] = reading.lesart;
            });

            // group manuscripts and loop over groups
            _.forEach (_.groupBy (_.sortBy (json.data.manuscripts, grouper), grouper), function (group) {
                var data = {
                    'pass_id' : passage.pass_id,
                    'labez'   : group[0].labez,
                    'clique'  : group[0].clique || '',
                    'group'   : grouper (group[0]),
                };

                data.reading = _.get (readings, data.labez, 'Error: no reading found');

                html.push ('<li class="list-group-item">');
                html.push ('<h4 class="list-group-item-heading">');
                html.push (tools.format (
                    '<a data-labez="{labez}" class="apparatus-labez fg_labez">{group} {reading}</a></h4>', data
                ));

                html.push ('<ul class="list-group-item-text attesting-mss list-inline">');
                _.forEach (_.sortBy (group, ['hsnr']), function (item) {
                    var data2 = {
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
            json_deferred.resolve ();
        });

        var faded_promise = this.$wrapper.animate ({ 'opacity' : 0.0 }, 300);

        $.when (json_deferred.promise (), faded_promise).done (function () {
            var $wrapper = that.$wrapper;
            var old_height = $wrapper.get (0).scrollHeight;
            $wrapper.html (new_list);
            var new_height = $wrapper.get (0).scrollHeight;
            $wrapper.height (old_height);
            $wrapper.animate ({ 'height' : new_height }, 300, function () {
                $wrapper.height ('auto');
                $wrapper.animate ({ 'opacity' : 1.0 }, 300);
            });
            panel.set_toolbar_buttons (that.toolbar, that.data);
            changed ();
        });
    }

    /**
     * Show the attestation in the Coherence panel and scroll to it.
     *
     * @param event
     */

    function goto_attestation (event) {
        event.stopPropagation ();

        var instance = window.coherence.ltextflow;
        var labez = $ (event.currentTarget).attr ('data-labez');
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
