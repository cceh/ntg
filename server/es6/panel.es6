/**
 * This module is the base for a panel.  It implements the toolbars and the
 * minimize/maximize functionality and updates the panel only while it is open.
 *
 * @module panel
 *
 * @author Marcello Perathoner
 */

define ([
    'jquery',
    'lodash',
    'bootstrap',
    'bootstrap-slider',
    'css!panel-css',
    'css!bootstrap-slider-css',
],

function ($, _) {
    function on_maximizing_panel_visibility (event) {
        var instance = event.data;

        instance.visible = true;
        if (instance.dirty) {
            instance.dirty = false;
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

    /**
     * Read the status of the toolbar buttons after event
     *
     * @function handle_toolbar_events
     *
     * @param {Object} event - The event.  The status is saved in
     *                         event.data.data
     */

    function handle_toolbar_events (event) {
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

    /**
     * Set the status of the toolbar buttons
     *
     * @function set_toolbar_buttons
     *
     * @param {jQuery} $toolbar   - The toolbar
     * @param {Object} new_status - The new status of the toolbar buttons
     */

    function set_toolbar_buttons ($toolbar, new_status) {
        var $panel = $toolbar.closest ('div.panel');

        _.forEach (new_status, function (value, key) {
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
                var i18n = $.trim ($group.find (`label.btn[data-${key}="${value}"]`).text ());
                $dropdown.find ('span.btn_text').text (i18n);
                break;
            default:
            }
        });
    }

    /**
     * Loads the buttons in the labez dropdown.
     *
     * Loads the buttons in the labez dropdown with the labez of the readings of
     * the passage.
     *
     * @function load_labez_dropdown
     *
     * @param {jQuery} $group      - The button group
     * @param {int|string} pass_id - The passage id
     * @param {string} input_name  - <input name=name ...>
     * @param {Array} prefixes     - Strings to prepend to the list.
     * @param {Array} suffixes     - Strings to append to the list.
     *
     * @return {Promise} Promise, resolved when the buttons are loaded.
     */

    function load_labez_dropdown ($group, pass_id, input_name, prefixes, suffixes) {
        var deferred = $.Deferred ();
        var $menu = $group.find ('div[data-toggle="buttons"]');

        $.getJSON ('passage.json/' + pass_id, json => {
            $menu.empty ();
            var readings = prefixes.concat (json.data.readings).concat (suffixes);
            for (const [labez, labez_i18n] of readings) {
                if (labez[0] !== 'z') {
                    $menu.append (`<label class="btn btn-primary btn-labez bg_labez" data-labez="${labez}">
                                     <input type="radio" data-type="dropdown" name="${input_name}"
                                            data-opt="${labez}">${labez_i18n}</input>
                                   </label>`);
                }
            };
            deferred.resolve ();
        });
        return deferred.promise ();
    }

    /**
     * Loads the buttons in the cliques dropdown.
     *
     * Loads the buttons in the cliques dropdown with the cliques of the
     * passage.
     *
     * @function load_cliques_dropdown
     *
     * @param {jQuery} $group      - The button group
     * @param {int|string} pass_id - The passage id
     * @param {string} input_name  - <input name=name ...>
     * @param {Array} prefixes     - Strings to prepend to the list.
     * @param {Array} suffixes     - Strings to append to the list.
     *
     * @return {Promise} Promise, resolved when the buttons are loaded.
     */

    function load_cliques_dropdown ($group, pass_id, input_name, prefixes, suffixes) {
        var deferred = $.Deferred ();
        var $menu = $group.find ('div[data-toggle="buttons"]');

        $.getJSON ('passage.json/' + pass_id, json => {
            $menu.empty ();
            var cliques = prefixes.concat (json.data.cliques).concat (suffixes);
            for (const [labez, , clique] of cliques) {
                if (labez[0] !== 'z') {
                    $menu.append (`<label class="btn btn-primary btn-labez bg_labez" data-labez="${labez}">
                                     <input type="radio" data-type="dropdown" name="${input_name}"
                                            data-opt="${clique}">${clique}</input>
                                   </label>`);
                }
            };
            deferred.resolve ();
        });
        return deferred.promise ();
    }

    /**
     * Loads the buttons in the range dropdown.
     *
     * Loads the buttons in the range dropdown with the ranges of the book.
     *
     * @function load_range_dropdown
     *
     * @param {jQuery} $group      - The button group
     * @param {int|string} pass_id - The passage id
     * @param {string} input_name  - The button(s) name
     * @param {Array} prefixes     - Strings to prepend to the list.
     * @param {Array} suffixes     - Strings to append to the list.
     *
     * @return {Promise} Promise, resolved when the buttons are loaded.
     */

    function load_range_dropdown ($group, pass_id, input_name, prefixes, suffixes) {
        var deferred = $.Deferred ();
        var $menu = $group.find ('div[data-toggle="buttons"]');

        $.getJSON ('ranges.json/' + pass_id, json => {
            $menu.empty ();
            var ranges = prefixes.concat (json.data.ranges).concat (suffixes);
            for (const range of ranges) {
                $menu.append (`<label class="btn btn-primary btn-range" data-range="${range.value}">
                                 <input type="radio" data-type="dropdown" name="${input_name}"
                                        data-opt="${range.value}">${range.range}</input>
                               </label>`);
            };
            deferred.resolve ();
        });
        return deferred.promise ();
    }

    /**
     * Put min-max and close buttons onto panels.
     *
     * Put minimize and maximize buttons on panels that contain
     * div.panel-slidable panes.  Put close buttons on panels that contain
     * div.panel-closable panes.
     *
     * @function create_panel_controls
     *
     * @param {jQuery} $panels - The panel(s)
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
     * Setup the minimize, maximize, and close button event handlers.
     *
     * @function setup_button_event_handlers
     */

    function setup_button_event_handlers () {
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
     * @returns {Object} The module instance object.
     */

    function init ($panel) {
        var instance = {};
        instance.load             = load;
        instance.visible          = true;
        instance.dirty            = true;
        instance.data             = {};

        instance.$panel           = $panel;
        instance.$toolbar         = $panel.find ('div.toolbar');

        // The user navigated to new passage.
        $ (document).on ('ntg.panel.reload', function (event, passage) {
            instance.load (passage);
        });

        setup_button_event_handlers ();

        // Init toolbar.
        instance.$toolbar.find ('.dropdown-toggle').dropdown ();

        instance.$toolbar.find ('input[name="connectivity"]').bootstrapSlider ({
            'value'           : 5,
            'ticks'           : [1,  5, 10, 20,  21],
            'ticks_positions' : [0, 25, 50, 90, 100],
            'formatter'       : connectivity_formatter,
        });

        // Answer toolbar activity.
        instance.$toolbar.on ('click slideStop', 'input', instance, on_toolbar);

        // Answer maximizing / minimizing
        instance.$panel.on ('maximizing.panel.visibility', instance, on_maximizing_panel_visibility);
        instance.$panel.on ('minimizing.panel.visibility', instance, on_minimizing_panel_visibility);

        return instance;
    }

    return {
        'init'                  : init,
        'set_toolbar_buttons'   : set_toolbar_buttons,
        'load_labez_dropdown'   : load_labez_dropdown,
        'load_cliques_dropdown' : load_cliques_dropdown,
        'load_range_dropdown'   : load_range_dropdown,
        'create_panel_controls' : create_panel_controls,
    };
});
