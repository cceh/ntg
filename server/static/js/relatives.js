/**
 * This module implements the popups that show the relatives of a manuscript.
 *
 * The popups are currently implemented as jquery-ui tooltips, which probably
 * was a bad idea, mainly because only one popup per element is possible and you
 * cannot easily open multiple popups for one manuscript.
 *
 * @module relatives
 * @author Marcello Perathoner
 */
define (['jquery', 'lodash', 'd3', 'd3-common', 'tools', 'navigator', 'jquery-ui'],

function ($, _, d3, d3c, tools, nav) {
    'use strict';

    var DEFAULTS = {
        'type'      : 'rel',
        'chapter'   : '0',
        'limit'     : '10',
        'include'   : [],
        'fragments' : [],
        'mode'      : 'rec',
        'labez'     : 'all+lac',
    };

    var URLS = {
        'rel' : '/relatives/',
        'anc' : '/ancestors/',
        'des' : '/descendants/',
    };

    function changed () {
        $ (document).trigger ('ntg.popup.changed');
    }

    // Create and register a custom jquery-ui tooltip that opens on click and
    // stays open until explicitly closed by the user.

    $.widget ('custom.relatives_tooltip', $.ui.tooltip, {
        'options' : {
            'classes'  : { 'ui-tooltip': 'tooltip-relatives tooltip-relatives-data' },
            'position' : { 'my': 'center bottom-3' },
            'open'     : function (event, ui) {
                var $el = ui.tooltip;
                var $panel = $el.find ('div.panel');
                var data = $.extend ({}, DEFAULTS);
                $panel.data ('options', data);
                tools.set_toolbar_buttons ($panel, data);
                $el.find ('.dropdown-toggle').dropdown ();
                changed ();
            },
            'content' : function (callback) {
                var ms_id = $ (this).attr ('data-ms-id');
                $.get (URLS[DEFAULTS.type] + nav.passage.id + '/' + ms_id, DEFAULTS, function (data) {
                    callback (data);
                });
            },
        },
        '_create' : function () {
            this._super ();
            // open only on click
            this._off (this.element, 'mouseover focusin');
        },
        '_open' : function (event, target, dummy_content) {
            this._superApply (arguments);
            this._off (target, 'mouseleave focusout');

            var tooltipData = this._find (target);
            var $tooltip = tooltipData.tooltip;
            $tooltip.draggable ();
        },
        '_removeTooltip' : function (dummy_tooltip) {
            // _removeTooltip () is called when the closing animation is completed.
            this._superApply (arguments);
            // At this point the tooltip has been removed from the DOM.
            changed ();
        },
    });

    // Create and register a custom jquery-ui tooltip like the above one, that
    // also groks the SVG DOM.

    $.widget ('custom.relatives_svg_tooltip', $.custom.relatives_tooltip, {
        '_open' : function (event, target, dummy_content) {
            this._superApply (arguments);

            // After opening reposition the popup manually because jquery
            // doesn't grok the SVG DOM.
            var rect = target.get (0).getBoundingClientRect ();
            var bodyRect = document.body.getBoundingClientRect (); // account for scrolling
            var tooltipData = this._find (target);
            var $tooltip = tooltipData.tooltip;
            event = new $.Event ('click');
            event.pageY = rect.top - bodyRect.top;
            event.pageX = rect.left - bodyRect.left + (rect.width / 2.0);
            $tooltip.position ({
                'my'        : 'center bottom-3',
                'collision' : 'flipfit flip',
                'of'        : event,
            });
        },
    });

    /*
    function close_jquery_popups () {
        $ ('g.node[aria-describedby]').relatives_svg_tooltip ('close');
    }
    */

    function popup_to_elem ($popup) {
        var id = $popup.attr ('id');
        return $ ('[aria-describedby="' + id + '"]');
    }

    function options (event) {
        var $target  = $ (event.target);
        var $panel   = $target.closest ('div.panel');
        var $tooltip = $target.closest ('.ui-tooltip');

        event.data = $panel.data ('options');
        var ms_id  = $panel.attr ('data-ms-id');

        tools.handle_toolbar_events (event);

        $.get (URLS[event.data.type] + nav.passage.id + '/' + ms_id, event.data, function (data) {
            var $newpanel = $ (data);
            $newpanel.data ('options', event.data);
            $panel.replaceWith ($newpanel);
            $tooltip.find ('.dropdown-toggle').dropdown ();
            tools.set_toolbar_buttons ($newpanel, event.data);
            changed ();
        });

        event.stopPropagation ();
    }

    /**
     * Get a list of the mss. currently displayed in the tooltip.  Get either
     * the 'source' ms. -- the ms. this tooltip is all about -- or the target
     * mss. -- the mss. related to the 'source' ms.
     *
     * N.B.  When you open a tooltip, the nodes listed in the tooltip are also
     * highlighted in the affinity cloud.  The affinity cloud uses this function
     * to find out which nodes to highlight.
     *
     * @function get_ms_ids_from_popups
     *
     * @param {string} what - 'source' or 'target'
     *
     * @return {Object} - Array of ms_ids
     */
    function get_ms_ids_from_popups (what) {
        var ms_ids = {};
        $ ('div.tooltip-relatives-data .hilite-' + what + '[data-ms-id]').each (function () {
            ms_ids[$ (this).attr ('data-ms-id')] = true;
        });
        return ms_ids;
    }

    /**
     * Initialize the module.
     *
     * @function init
     */
    function init () {
        // click on buttons in toolbar
        $ (document).on ('click', 'div.toolbar-relatives input', options);

        // click on close icon in jquery-ui popup
        $ (document).on ('click', '.ui-tooltip .tooltip-close', function (event) {
            var $popup = $ (this).closest ('.ui-tooltip');
            var $elem = popup_to_elem ($popup);
            if ($elem.length) {
                // FIXME: Since relatives_svg_tooltip inherits from relatives_tooltip, find
                // a way to use a "virtual function" here.
                try {
                    $elem.relatives_svg_tooltip ('close');
                } catch (e) {
                    $elem.relatives_tooltip ('close');
                }
            } else {
                // workaround for when the element doesn't exist anymore
                $popup.remove ();
            }
            changed ();
            event.stopPropagation ();
        });

        // click on minimize icon in jquery-ui popup
        $ (document).on ('click', '.ui-tooltip .tooltip-minimize', function (event) {
            var $this = $ (this);
            var $popup = $this.closest ('.ui-tooltip');
            $popup.find ('.panel-relatives-content').slideUp ();
            $popup.find ('.panel-relatives-toolbar').slideUp ();
            // Remove content from sight of get_ms_ids_from_popups ().
            $popup.removeClass ('tooltip-relatives-data');
            changed ();
            event.stopPropagation ();
        });

        // click on maximize icon in jquery-ui popup
        $ (document).on ('click', '.ui-tooltip .tooltip-maximize', function (event) {
            var $this = $ (this);
            var $popup = $this.closest ('.ui-tooltip');
            $popup.parent ().append ($popup); // bring to front
            $popup.find ('.panel-relatives-content').slideDown ();
            $popup.find ('.panel-relatives-toolbar').slideDown ();
            // Put content in sight of get_ms_ids_from_popups ().
            $popup.addClass ('tooltip-relatives-data');
            changed ();
            event.stopPropagation ();
        });
    }

    return {
        'init'                   : init,
        'get_ms_ids_from_popups' : get_ms_ids_from_popups,
    };
});
