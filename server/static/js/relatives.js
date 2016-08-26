// This is a RequireJS module.

define (['jquery', 'd3', 'd3-common', 'lodash', 'bootstrap', 'jquery-ui'],
        function ($, d3, d3c, _, bs) {

    var pass_id = 0;

    var DEFAULTS = {
        type:    'rel',
        chapter: '0',
        limit:   '10',
        labez:   'all',
    };

    var URLS = {
        rel: '/relatives/',
        anc: '/ancestors/',
        des: '/descendants/',
    };

    function changed () {
        $(document).trigger ('ntg.popup.changed');
    }

    $.widget ('custom.d3_tooltip', $.ui.tooltip, {
        // This is a jquery-ui tooltip that groks the SVG DOM.
        options: {
            items: 'g.node',
            classes: { 'ui-tooltip' : 'tooltip-relatives tooltip-relatives-data' },
            position: {
                my: 'center bottom-3'
            },
            content: function (callback) {
                var hsnr = d3c.to_d3 ($(this)).datum ().hsnr;
                $.get (URLS[DEFAULTS.type] + pass_id + '/' + hsnr, DEFAULTS, function (data) {
                    callback (data);
                });
            },
            open: function (event, ui) {
                var el = ui.tooltip;
                el.data ('options', $.extend ({}, DEFAULTS));
                check_bootstrap_buttons (el, el.data ('options'));
                el.find ('.dropdown-toggle').dropdown ();
                changed ();
            }
        },
        _create: function () {
            this._super ();
            // open only on click
            this._off (this.element, 'mouseover focusin');
        },
        _open: function (event, target, content) {
            this._superApply (arguments);
            this._off (target, 'mouseleave focusout');

            // Reposition the popup manually because jquery doesn't grok the SVG
            // DOM.
            var rect = target.get (0).getBoundingClientRect ();
            var bodyRect = document.body.getBoundingClientRect (); // account for scrolling
            var tooltipData = this._find (target);
		    var $tooltip = tooltipData.tooltip;
            event = $.Event ('click');
            event.pageY = rect.top - bodyRect.top;
            event.pageX = rect.left - bodyRect.left + rect.width / 2.0;
            $tooltip.position ({
                my: 'center bottom-3',
                collision: 'flipfit flip',
                of: event
            });

            $tooltip.draggable ();
        },
	    _removeTooltip: function (tooltip) {
            // _removeTooltip () is called when the closing animation is completed.
            this._superApply (arguments);
            // At this point the tooltip has been removed from the DOM.
            changed ();
	    },
    });

    function init_jquery_popup (node) {
        node.on ('click.jquery_ui', function (d) {
            var $this = $(this);
            $this.d3_tooltip ();
            $this.d3_tooltip ('open');
        });
    }

    function close_jquery_popups () {
        $('g.node[aria-describedby]').d3_tooltip ('close');
    }

    function popup_to_elem ($popup) {
        var id = $popup.attr ('id');
        return $('[aria-describedby="' + id + '"]');
    }

    function init_bootstrap_popup (node) {
        // Implement node popups with bootstrap.
        //
        // We have to manage popups manually because bootstrap makes it
        // impossible to have the popup content loaded by XHR.  The 'content'
        // function is unusable because it requires a synchronous call to XHR in
        // the main thread.  The same holds for 'show.bs.popover' event, because
        // if we do XHR asynchronously in it, we will not manage to set the new
        // content before the popup is already displayed, producing a 'flash of
        // old content'.  (Error message: XMLHttpRequest on the main thread is
        // deprecated because of its detrimental effects to the end user's
        // experience. For more help, check https://xhr.spec.whatwg.org/.)  The
        // only solution found so far is to manage the popup manually
        // ourselves. jquery-ui handles XHR easily.
        //
        // N.B. Also needs a patch in Tooltip.prototype.getPosition to make
        // bootstrap grok the SVG DOM.

        node.on ('click.bootstrap', function (d) {
            var $this = $(this);
            if (!$this.data ('bs.popover')) {
                $.get ('/relatives/' + pass_id + '/' + d.hsnr, function (data) {
                    var $data = $(data);
                    $('body').on ('inserted.bs.popover', function (e) {
                        $(e.target).data ('bs.popover').$tip.draggable ();
                    });
                    $this.popover ({
                        trigger: 'manual',
                        title: $('div.panel-heading', $data).html (),
                        content: $('table.relatives', $data)[0].outerHTML,
                        container: 'body',
                        html: true,
                        placement: 'auto top',
                        template: '<div class="popover popover-relatives" role="tooltip"><div class="arrow"></div><h3 class="popover-title"></h3><div class="popover-content"></div></div>'
                    }).popover ('show');
                });
            } else {
                $this.popover ('destroy');
            }
            // d3.event.stopPropagation ();
        });
    }

    function close_bootstrap_popups () {
        $('g.node').filter (function () {
            return $(this).data ('bs.popover');
        }).popover ('destroy');
    }

    function options (event) {

        var $target  = $(event.target);
        var $tooltip = $target.closest ('.ui-tooltip');
        var $panel   = $target.closest ('div.panel-relatives');

        var options = $tooltip.data ('options');
        options[$target.attr ('name')] = $target.attr ('data-opt');

        var hsnr    = $panel.attr  ('data-hsnr');

        $.get (URLS[options.type] + pass_id + '/' + hsnr, options, function (data) {
            $panel.replaceWith (data);
            // transfer old state to new elements
            check_bootstrap_buttons ($tooltip, options);
            $tooltip.find ('.dropdown-toggle').dropdown ();
            changed ();
        });

        event.stopPropagation ();
    }

    function check_bootstrap_buttons ($panel, options) {
        _.forEach (options, function (value, key) {
            var $input = $panel.find ('input[name="' + key  + '"][data-opt="' + value + '"]');
            var $group = $input.closest ('.btn-group');
            $input.checked = true;
            $group.find ('label.btn').removeClass ('active');
            $input.closest ('label.btn').addClass ('active');
        });
        $panel.find ('.dropdown-toggle-labez')
            .attr ('data-labez', options.labez);
        var labez_i18n = $panel.find ('.btn-labez[data-labez="' + options.labez+ '"]').text ();
        $panel.find ('.dropdown-toggle-labez span.btn_text').text (labez_i18n);
    }

    function get_ms_ids_from_popups (what) {
        // what == source or target
        var ms_ids = {};
        $('div.tooltip-relatives-data .hilite-' + what + '[data-ms-id]').each (function (index) {
            ms_ids[$(this).attr ('data-ms-id')] = true;
        });
        return ms_ids;
    }

    function init (_pass_id) {
        pass_id = _pass_id;

        $(document).off ('.data-api');

        // click on buttons in toolbar
        $(document).on ('click', 'div.toolbar-relatives input', options);

        // click on close icon in jquery-ui popup
        $(document).on ('click', '.ui-tooltip .tooltip-close', function (event) {
            $popup = $(this).parents ('.ui-tooltip');
            popup_to_elem ($popup).d3_tooltip ('close');
            changed ();
            event.stopPropagation ();
        });

        // click on minimize icon in jquery-ui popup
        $(document).on ('click', '.ui-tooltip .tooltip-minimize', function (event) {
            var $this = $(this);
            var $popup = $this.parents ('.ui-tooltip');
            $popup.find ('.panel-relatives-content').slideUp ();
            $popup.find ('.panel-relatives-toolbar').slideUp ();
            // Remove content from sight of get_ms_ids_from_popups ().
            $popup.removeClass ('tooltip-relatives-data');
            changed ();
            event.stopPropagation ();
        });

        // click on maximize icon in jquery-ui popup
        $(document).on ('click', '.ui-tooltip .tooltip-maximize', function (event) {
            var $this = $(this);
            var $popup = $this.parents ('.ui-tooltip');
            $popup.parent().append($popup); // bring to front
            $popup.find ('.panel-relatives-content').slideDown ();
            $popup.find ('.panel-relatives-toolbar').slideDown ();
            // Put content in sight of get_ms_ids_from_popups ().
            $popup.addClass ('tooltip-relatives-data');
            changed ();
            event.stopPropagation ();
        });

        // click on close icon in bootstrap popup
        $(document).on ('click', '.popover .tooltip-close', function (event) {
            $popup = $(this).parents ('.popover');
            popup_to_elem ($popup).popover ('destroy');
            changed ();
            event.stopPropagation ();
        });
    }

    // return an object that defines this module
    return {
        init:                   init,
        init_jquery_popup:      init_jquery_popup,
        init_bootstrap_popup:   init_bootstrap_popup,
        get_ms_ids_from_popups: get_ms_ids_from_popups,
    };
});
