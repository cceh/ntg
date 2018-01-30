'use strict';

/**
 * This module is the base for a panel.  It implements the minimize/maximize
 * functionality and updates the panel only while it is open.
 *
 * @module panel
 *
 * @author Marcello Perathoner
 */

define(['jquery', 'lodash', 'toolbar', 'bootstrap', 'css!panel-css'], function ($, _, toolbar) {
    function on_maximizing_panel_visibility(event) {
        var instance = event.data;

        instance.visible = true;
        if (instance.dirty) {
            instance.dirty = false;
            instance.load_passage(instance.data.passage);
        }
    }

    function on_minimizing_panel_visibility(event) {
        var instance = event.data;

        instance.visible = false;
    }

    /**
     * Retrieve and display new gagdet content.
     *
     * @function load
     *
     * @param {Object} passage - Passage data
     *
     * @return {Promise} Promise, resolved when the new passage has loaded.
     */

    function load(passage) {
        var instance = this;

        instance.data.passage = passage;
        if (instance.visible) {
            return instance.load_passage(passage);
        }
        instance.dirty = true;
        return $.Deferred().resolve().promise();
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

    function create_panel_controls($panels) {
        $panels.each(function (i, el) {
            var $panel = $(el);
            if ($panel.find('div.panel-slidable').length > 0) {
                $panel.find('div.panel-caption').prepend('<a class="close panel-minimize"><span class="glyphicon glyphicon-collapse-up"></span></a>' + '<a class="close panel-maximize"><span class="glyphicon glyphicon-collapse-down"></span></a>');
            }
            // append the buttons in inverse order because they float right
            if ($panel.hasClass('panel-closable')) {
                $panel.find('div.panel-caption').prepend('<a class="close panel-close"><span class="glyphicon glyphicon-remove"></span></a>');
            }
        });
    }

    /**
     * Setup the minimize, maximize, and close button event handlers.
     *
     * @function setup_button_event_handlers
     */

    function setup_button_event_handlers() {
        // Click on minimize icon
        $(document).on('click', 'a.panel-minimize', function (event) {
            var $this = $(this);
            var $panel = $this.closest('div.panel');
            $panel.trigger('minimizing.panel.visibility');
            $panel.find('.panel-slidable').slideUp(function () {
                $panel.trigger('minimized.panel.visibility');
                $panel.trigger('changed.panel.visibility');
            });
            event.stopPropagation();
        });

        // Click on maximize icon
        $(document).on('click', 'a.panel-maximize', function (event) {
            var $this = $(this);
            var $panel = $this.closest('div.panel');
            $panel.trigger('maximizing.panel.visibility');
            $panel.find('.panel-slidable').slideDown(function () {
                $panel.trigger('maximized.panel.visibility');
                $panel.trigger('changed.panel.visibility');
            });
            event.stopPropagation();
        });

        // Click on close icon
        $(document).on('click', 'a.panel-close', function (event) {
            var $this = $(this);
            var $panel = $this.closest('div.panel');
            $panel.trigger('closing.panel.visibility');
            $panel.fadeOut(function () {
                $panel.trigger('closed.panel.visibility');
                $panel.trigger('changed.panel.visibility');
                $panel.remove();
            });
            event.stopPropagation();
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

    function init($panel) {
        var instance = {};
        instance.load = load;
        instance.visible = true;
        instance.dirty = true;
        instance.data = {};

        instance.$panel = $panel;
        toolbar.init(instance, $panel.find('div.toolbar'));

        // The user navigated to a new passage.
        instance.$panel.on('ntg.panel.reload', function (event, passage) {
            // NB. this closure keeps instance alive!  That is important for the
            // relatives popup.
            instance.load(passage);
            event.stopPropagation();
        });

        setup_button_event_handlers();

        // Answer maximizing / minimizing
        instance.$panel.on('maximizing.panel.visibility', instance, on_maximizing_panel_visibility);
        instance.$panel.on('minimizing.panel.visibility', instance, on_minimizing_panel_visibility);

        return instance;
    }

    return {
        'init': init,
        'create_panel_controls': create_panel_controls
    };
});

//# sourceMappingURL=panel.js.map