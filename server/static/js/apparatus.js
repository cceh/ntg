/**
 * This module displays the apparatus table.  It retrieves the apparatus data in
 * JSON format and builds a list of readings and of the manuscripts that attest
 * that reading.
 *
 * @module apparatus
 * @author Marcello Perathoner
 */

define (['jquery', 'lodash', 'tools', 'panel', 'bootstrap'],

function ($, _, tools, panel) {
    'use strict';

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

        $.getJSON ('apparatus.json/' + passage.id, function (json) {
            var grouper = _.includes (that.data.splits, 'splits') ? 'varnew' : 'varid';
            var groups  = _.groupBy (json.manuscripts, grouper);
            var html = [];

            _.forEach (groups, function (group) {
                var data = {
                    'pass_id' : passage.id,
                    'labez'   : group[0].varnew[0],
                    'group'   : group[0][grouper],
                    'reading' : _.get (json.readings, group[0].varnew, json.readings[group[0].varnew[0]]),
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
            /* Show splits or not. */
            'splits'  : ['splits'],
        });

        return instance;
    }

    return {
        'init' : init,
    };
});
