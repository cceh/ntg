/**
 * This module displays the apparatus table.  It retrieves the apparatus data in
 * JSON format and builds a list of readings and of the manuscripts that attest
 * that reading.
 *
 * @module apparatus
 * @author Marcello Perathoner
 */

define (['jquery', 'lodash', 'tools', 'bootstrap'],

function ($, _, tools) {
    'use strict';

    /**
     * Load a new passage.
     *
     * @function load_passage
     *
     * @param {int} pass_id - The passage id
     */
    function load_passage (pass_id) {
        this.pass_id = pass_id;

        var that = this;
        $.getJSON ('/apparatus.json/' + pass_id, function (json) {
            var html = [];
            var groups = _.groupBy (json.manuscripts, 'varnew');

            _.forEach (groups, function (group) {
                var data = {
                    'pass_id' : pass_id,
                    'labez'   : group[0].varnew[0],
                    'varnew'  : group[0].varnew,
                    'reading' : json.readings[group[0].varnew[0]],
                };
                html.push ('<li class="list-group-item">');
                html.push ('<h4 class="list-group-item-heading">');
                html.push (tools.format (
                    '<a data-labez="{labez}" class="fg_labez" ' +
                        'href="/ms_attesting/{pass_id}/{labez}">{varnew} {reading}</a></h4>',
                    data));

                html.push ('<ul class="list-group-item-text attesting-mss list-inline">');
                _.forEach (group, function (item) {
                    var data2 = {
                        'ms_id' : item.ms_id,
                        'hs'    : item.hs,
                    };
                    html.push (tools.format ('<li><a class="ms" data-ms-id="{ms_id}">{hs}.</a></li>', data2));
                });
                html.push ('</ul>');
                html.push ('</li>');
            });
            that.wrapper.html ($ (html.join ('')));
        });
    }

    /**
     * Initialize the module.
     *
     * @function init
     *
     * @param {string} wrapper_selector - The element that should contain the apparatus table.
     *
     * @param {string} id_prefix - Prefix to use for all for the ids. (currently unused)
     *
     * @returns {dict} - The module instance object.
     */
    function init (wrapper_selector, id_prefix) {
        var instance = {};
        instance.wrapper      = $ (wrapper_selector);
        instance.id_prefix    = $ (id_prefix);
        instance.load_passage = load_passage;
        return instance;
    }

    return {
        'init' : init,
    };
});
