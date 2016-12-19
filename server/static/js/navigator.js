/**
 * This module implements the tape-recorder-controls navigator.  It also keeps
 * track of the current passage for other modules to peek at.
 *
 * @module navigator
 * @author Marcello Perathoner
 */

define (['jquery'], function ($) {
    'use strict';

    var module = {};

    /**
     * Set a new passage.  Programmatically set a new passage, eg. at page load.
     *
     * @function set_passage
     *
     * @param {int} pass_id - The new passage id
     */
    function set_passage (pass_id) {
        $.getJSON ('passage.json/' + pass_id, function (json) {
            module.passage = json;
            $ (document).trigger ('ntg.passage.changed', json);
        });
    }

    /**
     * Initialize the module.
     *
     * @function init
     *
     * @returns {dict} - The module object.
     */
    function init () {
        // Tape recorder controls
        $ ('form.passage-selector').on ('click', function (event) {
            var $target = $ (event.target);
            var data = $target.attr ('data');
            var q = $ (event.currentTarget).serializeArray ();
            q.push ({ 'name': 'button', 'value': data });

            $.getJSON ('passage.json/0?' + $.param (q), function (json) {
                module.passage = json;
                $ (document).trigger ('ntg.passage.changed', json);
                window.location.hash = '#' + json.passage;
            });
        });

        $ (document).on ('ntg.passage.changed', function (event, json) {
            var $form = $ ('form.passage-selector');
            $form.find ('input[name="pass_id"]').val (json.id);
            $form.find ('input[name="dest"]').attr ('placeholder', json.hr);
            $ ('h1 span.passage').text (json.hr);
            $ ('title').text ($ ('h1').text ());
        });

        // User hit back-button, etc.
        $ (window).on ('hashchange', function () {
            var hash = window.location.hash.substring (1);
            $.getJSON ('passage.json/' + hash, function (json) {
                module.passage = json;
                $ (document).trigger ('ntg.passage.changed', json);
            });
        });

        return module;
    }

    module.init = init;
    module.set_passage = set_passage;

    return module;
});
