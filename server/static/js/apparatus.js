/**
 * This module implements the apparatus table.  It retrieves the apparatus data
 * in JSON format and builds a list of readings and of manuscripts attesting
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
                    'reading' : json.readings[group[0].varnew[0]],
                };
                html.push ('<li class="list-group-item">');
                html.push ('<h4 class="list-group-item-heading">');
                html.push (tools.format (
                    '<a data-labez="{labez}" class="fg_labez" ' +
                        'href="/ms_attesting/{pass_id}/{labez}">{labez} {reading}</a></h4>',
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
     * @param {dict} params - A dictionary containing the parameters.
     *
     * @returns {dict} - The module instance object.
     */
    function init (params) {
        var instance = {};
        instance.wrapper      = $ (params.wrapper_selector);
        instance.load_passage = load_passage;
        return instance;
    }

    return {
        'init' : init,
    };
});
