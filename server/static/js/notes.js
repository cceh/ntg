'use strict';

/**
 * This module implements the editor notes panel.
 *
 * @module notes
 * @author Marcello Perathoner
 */

define(['jquery', 'tools', 'css!notes-css'], function ($, tools) {
    function dyn_resize(instance) {
        var $ta = instance.$textarea;
        var old_height = $ta.prop('clientHeight');
        $ta.css('height', '1px'); // to get the correct value if smaller than the old value
        var new_height = $ta.prop('scrollHeight');
        $ta.css('height', old_height); // reset old value
        $ta.animate({ 'height': new_height }, { 'duration': 300, 'queue': false });
    }

    function changed(instance) {
        dyn_resize(instance);
        instance.$save_button.prop('disabled', instance.original_text === instance.$textarea.val());
        $(document).trigger('changed.ntg.notes');
    }

    /**
     * Load a new passage.
     *
     * @function load_passage
     *
     * @param {Object} passage - Which passage to load.
     *
     * @return {Promise} Promise, resolved when the new passage has loaded.
     */
    function load_passage(passage) {
        var instance = this;
        instance.passage = passage;
        var $ta = instance.$textarea;

        var url = 'notes.txt/' + passage.pass_id;
        var faded = $ta.animate({ 'opacity': 0.0 }, 300);
        var req = $.get(url);

        return $.when(req, faded).done(function () {
            $ta.val(req.responseText);
            $ta.animate({ 'opacity': 1.0 }, 300);
            instance.original_text = $ta.val();
            changed(instance);
        });
    }

    /**
     * Save an edited passage.
     *
     * @function save_passage
     *
     * @param {Object} instance - The module instance
     */
    function save_passage(instance) {
        var url = 'notes.txt/' + instance.passage.pass_id;
        var xhr = $.ajax({
            'url': url,
            'method': 'PUT',
            'data': { 'remarks': instance.$textarea.val() }
        }).done(function (dummy_result) {
            instance.original_text = instance.$textarea.val();
            changed(instance);
            tools.xhr_alert(xhr, instance.$wrapper);
        });
    }

    /**
     * Initialize the module.
     *
     * @function init
     *
     * @param {Object} instance     - The panel module instance to inherit from.
     * @param {string} id_prefix    - The prefix to use for all generated ids.
     *
     * @returns {Object} - The module instance object.
     */
    function init(instance, dummy_id_prefix) {
        instance.load_passage = load_passage;
        $.extend(instance.data, {});
        instance.$wrapper = instance.$panel.find('.panel-content');
        instance.$textarea = instance.$wrapper.find('textarea');
        instance.$textarea.on('input', function () {
            changed(instance);
        });
        instance.$save_button = instance.$toolbar.find('button[name="save"]');
        instance.$save_button.on('click', function () {
            save_passage(instance);
        });
        return instance;
    }

    return {
        'init': init
    };
});

//# sourceMappingURL=notes.js.map