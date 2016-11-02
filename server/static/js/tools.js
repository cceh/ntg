// This is a RequireJS module.
define (['jquery', 'lodash'],

function ($, _) {
    'use strict';

    function handle_bootstrap_buttons (event) {
        var $target = $ (event.target);
        var $panel  = $target.closest ('div.panel'); // put the options on the panel
        var opts    = $panel.data ('options');
        var $group;

        // change opts according to event

        if (event.type === 'click' || event.type === 'slideStop') {
            var name = $target.attr ('name');
            $group = $target.closest ('.btn-group');
            switch (name) {
            case 'include':
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
                $dropdown.dropdown ('toggle');
                break;
            default:
                opts[name] = $target.attr ('data-opt');
            }
        }

        // Set bootstrap buttons according to opts

        _.forEach (opts, function (value, key) {
            var $input;

            switch (key) {
            case 'include':
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
            default:
                $input = $panel.find ('input[name="' + key  + '"][data-opt="' + value + '"]');
                $group = $input.closest ('.btn-group');
                $input.checked = true;
                $group.find ('label.btn').removeClass ('active');
                $input.closest ('label.btn').addClass ('active');
            }
        });

        $panel.find ('.dropdown-toggle-labez').attr ('data-labez', opts.labez);
        var labez_i18n = $panel.find ('.btn-labez[data-labez="' + opts.labez + '"]').text ();
        $panel.find ('.dropdown-toggle-labez span.btn_text').text (labez_i18n);
    }

    // return an object that defines this module
    return {
        'handle_bootstrap_buttons' : handle_bootstrap_buttons,
    };
});
