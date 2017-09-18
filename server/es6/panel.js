/**
 * This module is the base for a panel. It implements the toolbars and the
 * minimize/maximize functionality and updates the panel only while it is open.
 *
 * @module panel
 * @author Marcello Perathoner
 */

define ([
    'jquery',
    'lodash',
    'tools',
    'css!panel-css',
],

function ($, _, tools) {
    function on_maximizing_panel_visibility (event) {
        var instance = event.data;

        instance.visible = true;
        if (instance.dirty) {
            instance.load_passage (instance.data.passage);
        }
    }

    function on_minimizing_panel_visibility (event) {
        var instance = event.data;

        instance.visible = false;
    }

    /**
     * Retrieve and display new gagdet content.
     *
     * @function load
     *
     * @param {Object} passage - Passage data
     */
    function load (passage) {
        var instance = this;

        instance.data.passage = passage;
        if (instance.visible) {
            instance.load_passage (passage);
        } else {
            instance.dirty = true;
        }
    }

    function get_control_type ($input) {
        return $input.attr ('data-type') || $input.attr ('type') || 'button';
    }

    function connectivity_formatter (s) {
        return (s === 21) ? 'All' : s;
    }

    function handle_toolbar_events (event) {
        // change opts according to event

        if (event.type === 'click' || event.type === 'slideStop') {
            var opts    = event.data.data;
            var $target = $ (event.target);
            var $group  = $target.closest ('.btn-group');
            var name    = $target.attr ('name');
            var type    = get_control_type ($target);

            switch (type) {
            case 'checkbox':
                opts[name] = [];
                $group.find ('input:checked').each (function (i, btn) {
                    opts[name].push ($ (btn).attr ('data-opt'));
                });
                break;
            case 'radio':
                opts[name] = $target.attr ('data-opt');
                break;
            case 'slider':
                opts[name] = $target.bootstrapSlider ('getValue');
                break;
            case 'dropdown':
                opts[name] = $target.attr ('data-opt');
                var $dropdown = $group.parent ().closest ('.btn-group').find ('button[data-toggle="dropdown"]');
                $dropdown.dropdown ('toggle'); // close
                break;
            default:
            }
        }
    }

    function on_toolbar (event) {
        var instance = event.data;

        handle_toolbar_events (event);
        instance.load_passage (instance.data.passage);

        event.stopPropagation ();
    }

    function set_toolbar_buttons (target, opts) {
        var $target = $ (target);

        // Set bootstrap buttons according to opts

        var $panel = $target.closest ('div.panel');

        _.forEach (opts, function (value, key) {
            var $input = $panel.find ('input[name="' + key  + '"]');
            var $group = $input.closest ('.btn-group');
            var type   = get_control_type ($input);

            switch (type) {
            case 'checkbox':
                $group.find ('label.btn').removeClass ('active');
                $group.find ('input').prop ('checked', false);

                _.forEach (value, function (v) {
                    $input = $group.find ('input[name="' + key  + '"][data-opt="' + v + '"]');
                    $input.prop ('checked', true);
                    $input.closest ('label.btn').addClass ('active');
                });
                break;
            case 'radio':
                $input = $group.find ('input[name="' + key  + '"][data-opt="' + value + '"]');
                $input.checked = true;
                $group.find ('label.btn').removeClass ('active');
                $input.closest ('label.btn').addClass ('active');
                break;
            case 'slider':
                $input.bootstrapSlider ('setValue', +value);
                $panel.find ('span.connectivity-label').text (connectivity_formatter (value));
                break;
            case 'dropdown':
                if (key === 'hyp_a') {
                    key = 'labez';
                }
                var $dropdown = $group.parent ().closest ('.btn-group').find ('button[data-toggle="dropdown"]');
                $dropdown.attr ('data-' + key, value);
                var i18n = $.trim ($group.find ('label.btn[data-' + key + '="' + value + '"]').text ());
                $dropdown.find ('span.btn_text').text (i18n);
                break;
            default:
            }
        });
    }

    /**
     * Loads the buttons in the labez dropdown with the labez of the passage.
     *
     * @function load_labez_dropdown
     *
     * @param {jQuery} $group      - The button group
     * @param {int|string} pass_id - The passage id
     * @param {string} name        - The button(s) name
     * @param {Array} prefixes     - Strings to prepend to the list.
     * @param {Array} suffixes     - Strings to append to the list.
     *
     * @return {Promise} - Promise, resolved when the buttons are loaded.
     */
    function load_labez_dropdown ($group, pass_id, name, prefixes, suffixes) {
        var $menu = $group.find ('div[data-toggle="buttons"]');

        var promise = $.getJSON ('passage.json/' + pass_id);
        promise.done (function (json) {
            $menu.empty ();
            var readings = prefixes.concat (json.data.readings).concat (suffixes);
            _.forEach (readings, function (value) {
                var data = { 'name' : name, 'labez' : value[0], 'labez_i18n' : value[1] };
                var $item = $ (tools.format (
                    '<label class="btn btn-primary btn-labez bg_labez" data-labez="{labez}">' +
                        '<input type="radio" data-type="dropdown" name="{name}" ' +
                        'data-opt="{labez}">{labez_i18n}</input></label>', data
                ));
                $menu.append ($item);
            });
        });
        return promise;
    }

    /**
     * Loads the buttons in the range dropdown.
     *
     * @function load_range_dropdown
     *
     * @param {jQuery} $group  - The button group
     * @param {string} name    - The button(s) name
     * @param {Array} prefixes - Strings to prepend to the list.
     * @param {Array} suffixes - Strings to append to the list.
     *
     * @return {Promise} - Promise, resolved when the buttons are loaded.
     */
    function load_range_dropdown ($group, name, prefixes, suffixes) {
        var $menu = $group.find ('div[data-toggle="buttons"]');

        var promise = $.getJSON ('ranges.json');
        promise.done (function (json) {
            $menu.empty ();
            var ranges = prefixes.concat (json.data.ranges).concat (suffixes);
            _.forEach (ranges, function (data) {
                data.name = name;
                var $item = $ (tools.format (
                    '<label class="btn btn-primary btn-range" data-range="{value}">' +
                        '<input type="radio" data-type="dropdown" name="{name}" ' +
                        'data-opt="{value}">{range}</input></label>', data
                ));
                $menu.append ($item);
            });
        });
        return promise;
    }

    /**
     * Put min-max and close buttons onto panels.
     *
     * Put min-max buttons on panels that contain div.panel-slidable panes.
     * Put close buttons on panels that contain div.panel-closable panes.
     *
     * @param $panels {jQuery}  The panels to consider.
     *
     * @function create_panel_controls
     */
    function create_panel_controls ($panels) {
        $panels.each (function () {
            var $panel = $ (this);
            if ($panel.find ('div.panel-slidable').length > 0) {
                $panel.find ('div.panel-caption').prepend (
                    '<a class="close panel-minimize"><span class="glyphicon glyphicon-collapse-up"></span></a>' +
                    '<a class="close panel-maximize"><span class="glyphicon glyphicon-collapse-down"></span></a>'
                );
            }
            // append the buttons in inverse order because they float right
            if ($panel.hasClass ('panel-closable')) {
                $panel.find ('div.panel-caption').prepend (
                    '<a class="close panel-close"><span class="glyphicon glyphicon-remove"></span></a>'
                );
            }
        });
    }

    /**
     * Init panel button events
     *
     * @function init_panel_events
     */
    function init_panel_events () {
        // Click on minimize icon
        $ (document).on ('click', 'a.panel-minimize', function (event) {
            var $this = $ (this);
            var $panel = $this.closest ('div.panel');
            $panel.trigger ('minimizing.panel.visibility');
            $panel.find ('.panel-slidable').slideUp (function () {
                $panel.trigger ('minimized.panel.visibility');
                $panel.trigger ('changed.panel.visibility');
            });
            event.stopPropagation ();
        });

        // Click on maximize icon
        $ (document).on ('click', 'a.panel-maximize', function (event) {
            var $this = $ (this);
            var $panel = $this.closest ('div.panel');
            $panel.trigger ('maximizing.panel.visibility');
            $panel.find ('.panel-slidable').slideDown (function () {
                $panel.trigger ('maximized.panel.visibility');
                $panel.trigger ('changed.panel.visibility');
            });
            event.stopPropagation ();
        });

        // Click on close icon
        $ (document).on ('click', 'a.panel-close', function (event) {
            var $this = $ (this);
            var $panel = $this.closest ('div.panel');
            $panel.trigger ('closing.panel.visibility');
            $panel.fadeOut (function () {
                $panel.trigger ('closed.panel.visibility');
                $panel.trigger ('changed.panel.visibility');
                $panel.remove ();
            });
            event.stopPropagation ();
        });
    }

    /**
     * Initialize the module.
     *
     * @function init
     *
     * @param {Object} $panel - The panel element.
     *
     * @returns {dict} - The module instance object.
     */
    function init ($panel) {
        var instance = {};
        instance.load             = load;
        instance.visible          = true;
        instance.dirty            = true;
        instance.data             = {};

        instance.$panel           = $panel;
        instance.$toolbar         = $panel.find ('div.toolbar');

        // Init toolbar.
        instance.$toolbar.find ('.dropdown-toggle').dropdown ();

        // Answer toolbar activity.
        instance.$toolbar.on ('click slideStop', 'input', instance, on_toolbar);

        // Answer maximizing / minimizing
        instance.$panel.on ('maximizing.panel.visibility', instance, on_maximizing_panel_visibility);
        instance.$panel.on ('minimizing.panel.visibility', instance, on_minimizing_panel_visibility);

        return instance;
    }

    return {
        'init'                   : init,
        'handle_toolbar_events'  : handle_toolbar_events,
        'connectivity_formatter' : connectivity_formatter,
        'set_toolbar_buttons'    : set_toolbar_buttons,
        'load_labez_dropdown'    : load_labez_dropdown,
        'load_range_dropdown'    : load_range_dropdown,
        'create_panel_controls'  : create_panel_controls,
        'init_panel_events'      : init_panel_events,
    };
});
