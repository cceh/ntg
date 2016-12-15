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

    function changed () {
        // currently unused
        $ (document).trigger ('ntg.apparatus.changed');
    }

    function options (event) {
        var instance = event.data;
        var data = instance.data;
        event.data = data;

        tools.handle_toolbar_events (event);
        instance.load_passage (data.passage);
        event.stopPropagation ();
    }

    /**
     * Load a new passage.
     *
     * @function load_passage
     *
     * @param {int} pass_id - The passage id
     */
    function load_passage (passage) {
        this.data.passage = passage;

        var that = this;
        var new_list;
        var json_deferred = new $.Deferred ();

        $.getJSON ('apparatus.json/' + passage.id, function (json) {
            var grouper = _.includes (that.data.splits, 'splits') ? 'varnew' : 'varid';
            var groups  = _.groupBy (json.manuscripts, grouper);
            var html = [];

            _.forEach (groups, function (group) {
                var data = {
                    'pass_id' : passage.id,
                    'labez'   : group[0].varnew[0],
                    'group'   : group[0][grouper],
                    'reading' : _.get (json.readings, group[0].varnew, json.readings[group[0].varnew[0]])
                };
                html.push ('<li class="list-group-item">');
                html.push ('<h4 class="list-group-item-heading">');
                html.push (tools.format (
                    '<a data-labez="{labez}" class="fg_labez" ' +
                        'href="ms_attesting/{pass_id}/{group}">{group} {reading}</a></h4>',
                    data));

                html.push ('<ul class="list-group-item-text attesting-mss list-inline">');
                _.forEach (_.sortBy (group, ['hsnr']), function (item) {
                    var data2 = {
                        'ms_id' : item.ms_id,
                        'hs'    : item.hs,
                    };
                    html.push (tools.format ('<li><a class="ms" data-ms-id="{ms_id}">{hs}.</a></li>', data2));
                });
                html.push ('</ul>');
                html.push ('</li>');
            });
            new_list = $ (html.join (''));
            json_deferred.resolve ();
        });

        var faded_promise = this.wrapper.animate ({ 'opacity' : 0.0 }, 300);

        $.when (json_deferred.promise (), faded_promise).done (function () {
            var wrapper = that.wrapper;
            var old_height = wrapper.get(0).scrollHeight;
            wrapper.html (new_list);
            var new_height = wrapper.get(0).scrollHeight;
            wrapper.height (old_height);
            wrapper.animate ({ 'height' : new_height }, 300, function () {
                wrapper.height ('auto');
                wrapper.animate ({ 'opacity' : 1.0 }, 300);
            });
            tools.set_toolbar_buttons (that.toolbar, that.data);
            changed ();
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
     * @param {string} toolbar_selector - The toolbar to initialize and use.
     *
     * @returns {dict} - The module instance object.
     */
    function init (wrapper_selector, id_prefix, toolbar_selector) {
        var instance = {};
        instance.wrapper      = $ (wrapper_selector);
        instance.toolbar      = $ (toolbar_selector);
        instance.id_prefix    = $ (id_prefix);
        instance.load_passage = load_passage;
        instance.data         = {
            'passage' : null,
            /* Show splits or not. */
            'splits'  : ['splits'],
        };

        // Answer toolbar activity.
        $ (document).on ('click', toolbar_selector + ' input', instance, options);

        return instance;
    }

    return {
        'init' : init,
    };
});
