/**
 * This module implements the tape-recorder-controls navigator.  It also keeps
 * track of the current passage for other modules to peek at.
 *
 * @module navigator
 * @author Marcello Perathoner
 */

define (['jquery', 'lodash', 'css!navigator-css'], function ($, _) {
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
     * Get a list of suggestions from the server
     *
     * @function suggest
     *
     * @param {Object} data - Request object with 'term' property, which refers
     *                        to the value currently in the text input.
     *
     * @param {function} complete - The callback
     *
     * @see https://api.jqueryui.com/autocomplete/#option-source
     */
    function suggest (data, complete) {
        var $elem = $ (this.element);

        // collect values from all <input>s
        var $inputs = $elem.closest ('form').find ('input[data-autocomplete]');
        $inputs.each (function () {
            var $this = $ (this);
            data[$this.attr ('data-autocomplete')] = $this.val ();
        });
        // get the name of the current field
        data.currentfield = $elem.attr ('data-autocomplete');

        $.getJSON ('suggest.json', data, complete);
    }

    function on_nav (event) {
        var $target = $ (event.currentTarget);
        var $form   = $target.closest ('form');
        var data    = { 'button' : $target.attr ('data') || 'Go' };

        _.forEach ($form.serializeArray (), function (value) {
            data[value.name] = value.value;
        });

        $.getJSON ('passage.json', data, function (json) {
            module.passage = json;
            window.location.hash = '#' + json.passage;
        });
        return false;
    }

    /**
     * Initialize the module.
     *
     * @function init
     *
     * @returns {Object} - The module object.
     */
    function init () {
        // Tape recorder controls
        $ ('form.passage-selector').on ('click', 'button', on_nav);
        $ ('form.passage-selector').on ('submit', on_nav);

        $ ('form input[data-autocomplete]').autocomplete ( {
            'source'    : suggest,
            'minLength' : 0,
        }).on ('click', function () {
            $(this).autocomplete ('search');
        }).on ('autocompletechange', function () {
            $(this).nextAll ('input').val ('');
        }).on ('autocompleteselect', function (event, ui) {
            var $this = $(this);
            $this.nextAll ('input').val ('');
            if ($this.attr ('data-autocomplete') == 'word') {
                // give the control a chance to update the <input> before we call on_nav ()
                window.setTimeout (function () {
                    on_nav (event);
                });
            }
        });


        $ (document).on ('ntg.passage.changed', function (event, json) {
            var $form = $ ('form.passage-selector');
            $form.find ('input[name="pass_id"]').val (json.id);

            $ ('form input[data-autocomplete]').each (function () {
                var $this = $(this);
                $this.val (json[$this.attr ('data-autocomplete')]);
            });
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
