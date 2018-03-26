/**
 * This module implements the popups that show the relatives of a manuscript.
 *
 * @module relatives
 *
 * @author Marcello Perathoner
 */

define ([
    'jquery',
    'lodash',
    'tools',
    'toolbar',
    'css!relatives-css',
],

function ($, _, tools, toolbar) {
    function changed () {
        $ (document).trigger ('changed.ntg.relatives');
    }

    /**
     * Load new data.
     *
     * Display new data in the popup after the user navigated to a different
     * passage.
     *
     * @function load_passage
     *
     * @param {Object} passage - The new passage
     *
     * @return {Promise} Promise, resolved when the new passage has loaded.
     */

    function load_passage (passage) {
        let instance = this;
        // instance.data.passage = passage;

        const params = ['type', 'range', 'limit', 'labez', 'mode', 'include', 'fragments'];

        // replace content
        let ms_id = instance.$panel.data ('ms-id');
        let url   = 'relatives/' + passage.pass_id + '/id' + ms_id
            + '?' + $.param (_.pick (instance.data, params)); // we must use GET, not POST
        let p0 = $.get (url);
        let p1 = toolbar.load_labez_dropdown (
            instance.$toolbar.find ('div.toolbar-labez'), passage, 'labez',
            [['all', 'All'], ['all+lac', 'All+Lac']], []);
        let p2 = toolbar.load_range_dropdown (
            instance.$toolbar.find ('div.toolbar-range'), passage, 'range',
            [{ 'range' : 'This', 'value' : 'x' }], []);

        p0.done ((html) => {
            let $html = $ (html);
            // replace inner div to keep close button etc.
            let $caption_wrap = instance.$panel.find ('div.panel-relatives-caption div');
            let $heading_wrap = instance.$panel.find ('div.panel-relatives-metrics');
            let $table_wrap   = instance.$panel.find ('div.panel-relatives-content');
            $caption_wrap.html ($html.find ('div.relatives-caption'));
            $heading_wrap.html ($html.find ('div.relatives-metrics'));
            $table_wrap.html   ($html.find ('table.relatives'));
        });

        return $.when (p0, p1, p2).done (() => {
            toolbar.set_toolbar_buttons (instance.$toolbar, instance.data);
            // Maybe we changed range while navigating.  Set a new range.
            instance.$toolbar.find ('div.toolbar-range input[data-opt = "x"]')
                .attr ('data-opt', passage.chapter);
            changed ();
        });
    }

    /**
     * Position the popup panel relative to target.
     *
     * Target usually is the element that the user clicked to create the popup.
     *
     * @function position_popup
     *
     * @param {DOM} target    - A DOM element relative to which to position the popup.
     */

    function position_popup (target) {
        let instance = this;

        let rect = target.getBoundingClientRect ();
        let bodyRect = document.body.getBoundingClientRect (); // account for scrolling
        let event = new $.Event ('click');
        event.pageY = rect.top  - bodyRect.top  + (rect.height / 2.0);
        event.pageX = rect.left - bodyRect.left + (rect.width / 2.0);
        instance.$panel.position ({
            'my'        : 'center bottom-15',
            'collision' : 'flipfit flip',
            'of'        : event,
        });
    }

    /**
     * Initialize the module.
     *
     * @function init
     *
     * @param {Object} instance - The panel module instance to inherit from.
     */

    function init (instance) {
        instance.load_passage = load_passage;
        instance.position_popup = position_popup;
        $.extend (instance.data, {
            'type'      : 'rel',
            'range'     : 'All',
            'limit'     : '10',
            'include'   : [],
            'fragments' : [],
            'mode'      : 'sim',
            'labez'     : 'all+lac',
        });
        instance.$panel.on ('changed.panel.visibility', changed);

        return instance;
    }

    return {
        'init'         : init,
        'changed'      : changed,
    };
});
