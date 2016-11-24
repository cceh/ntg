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
        $.getJSON ('/passage.json/' + pass_id, function (json) {
            module.passage = json;
            $ (document).trigger ('ntg.passage.changed', json);
        });
    }

    /**
     * Initialize the module.
     *
     * @function init
     *
     * @param {string} title_prefix - The prefix of the page title
     *
     * @returns {dict} - The module object.
     */
    function init (title_prefix) {
        module.title_prefix = title_prefix

        // Tape recorder controls
        $ ('form.passage-selector').on ('click', function (event) {
            var $target = $ (event.target);
            var data = $target.attr ('data');
            var q = $ (event.currentTarget).serializeArray ();
            q.push ({ 'name': 'button', 'value': data });

            $.getJSON ('/passage.json/0?' + $.param (q), function (json) {
                module.passage = json;
                $ (document).trigger ('ntg.passage.changed', json);
            });
        });

        $ (document).on ('ntg.passage.changed', function (event, json) {
            var $form = $ ('form.passage-selector');
            $form.find ('input[name="pass_id"]').val (json.id);
            $form.find ('input[name="dest"]').attr ('placeholder', json.hr);
            $ ('h1').text (module.title_prefix + ' ' + json.hr);
            $ ('title').text (module.title_prefix + ' ' + json.hr);
        });

        return module;
    }

    module.init = init;
    module.set_passage = set_passage;

    return module;
});
