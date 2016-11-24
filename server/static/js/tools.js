/**
 * This module implements helper functions.
 *
 * @module tools
 * @author Marcello Perathoner
 */

define (['jquery', 'lodash'],

function ($, _) {
    'use strict';

    /**
     * Format a string in python fashion.  "{count} items found"
     *
     * @function format
     *
     * @param {string} s - The string to format
     * @param {dict} data - A dictionary of key: value
     *
     * @return {string} - The formatted string
     */
    function format (s, data) {
        return s.replace (/\{([_\w][_\w\d]*)\}/gm, function (match, p1) {
            return data[p1];
        });
    }

    function handle_toolbar_events (event) {
        // change opts according to event

        if (event.type === 'click' || event.type === 'slideStop') {
            var opts    = event.data;
            var $target = $ (event.target);
            var $group  = $target.closest ('.btn-group');
            var name    = $target.attr ('name');

            switch (name) {
            case 'include':
            case 'fragments':
                opts[name] = [];
                $group.find ('input:checked').each (function (i, btn) {
                    opts[name].push ($ (btn).attr ('data-opt'));
                });
                break;
            case 'connectivity': // slider
                opts[name] = $target.bootstrapSlider ('getValue');
                break;
            case 'labez':
                opts[name] = $target.attr ('data-opt');
                $group = $group.parent ().closest ('.btn-group'); // 2 levels deep
                var $dropdown = $group.find ('button[data-toggle="dropdown"]');
                $dropdown.dropdown ('toggle'); // close
                break;
            default:
                opts[name] = $target.attr ('data-opt');
            }
        }
    }

    function set_toolbar_buttons (target, opts) {
        var $target = $ (target);
        var $group;

        // Set bootstrap buttons according to opts

        var $panel = $target.closest ('div.panel');

        _.forEach (opts, function (value, key) {
            var $input;

            switch (key) {
            case 'include':
            case 'fragments':
                $input = $panel.find ('input[name="' + key  + '"]');
                $group = $input.closest ('.btn-group');
                $group.find ('label.btn').removeClass ('active');
                $group.find ('input').prop ('checked', false);

                _.forEach (value, function (v) {
                    $input = $group.find ('input[name="' + key  + '"][data-opt="' + v + '"]');
                    $input.prop ('checked', true);
                    $input.closest ('label.btn').addClass ('active');
                });
                break;
            case 'connectivity': // slider
                $input = $panel.find ('input[name="' + key  + '"]');
                $input.bootstrapSlider ('setValue', +value);
                $panel.find ('span.connectivity-label').text (value);
                break;
            case 'labez':
                var $dropdown = $panel.find ('button.dropdown-toggle-labez');
                $dropdown.attr ('data-labez', value);
                var labez_i18n = $.trim ($panel.find ('.btn-labez[data-labez="' + value + '"]').text ());
                $dropdown.find ('span.btn_text').text (labez_i18n);
                break;
            default:
                $input = $panel.find ('input[name="' + key  + '"][data-opt="' + value + '"]');
                $group = $input.closest ('.btn-group');
                $input.checked = true;
                $group.find ('label.btn').removeClass ('active');
                $input.closest ('label.btn').addClass ('active');
            }
        });
    }

    /**
     * Loads the buttons in the labez dropdown with the labez of the passage.
     *
     * @param {jQuery} $group - The button group
     * @param {int|string} pass_id - The passage id
     *
     * @return {Deferred} - Promise, resolved when the buttons are loaded.
     */
    function load_labez_dropdown ($group, pass_id) {
        var $menu = $group.find ('div[data-toggle="buttons"]');

        var promise = $.get ('/passage.json/' + pass_id);
        promise.done (function (json) {
            $menu.empty ();
            _.forEach (json.variants, function (value) {
                var data = { 'labez': value[0], 'labez_i18n': value[1] };
                var $item = $ (format (
                    '<label class="btn btn-labez bg_labez" data-labez="{labez}">' +
                        '<input type="radio" name="labez" data-opt="{labez}">{labez_i18n}</input></label>', data
                ));
                $menu.append ($item);
            });
        });
        return promise;
    }

    return {
        'format'                : format,
        'handle_toolbar_events' : handle_toolbar_events,
        'set_toolbar_buttons'   : set_toolbar_buttons,
        'load_labez_dropdown'   : load_labez_dropdown,
    };
});
