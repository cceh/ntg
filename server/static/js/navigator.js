'use strict';

/**
 * This module implements the tape-recorder-controls navigator.  It also keeps
 * track of the current passage for other modules to peek at.
 *
 * @module navigator
 * @author Marcello Perathoner
 */

define(['jquery', 'lodash', 'urijs/URI', 'jquery-ui', 'css!navigator-css'], function ($, _, urijs) {
    var module = {};

    /*
     * Extend the stock autocomplete to use a <table> instead of a <ul> and give
     * it the bootstrap look.  Using a table we can display the passage id
     * alongside the passage lemma.
     */

    $.widget('custom.tableautocomplete', $.ui.autocomplete, {
        '_renderMenu': function _renderMenu(ul, items) {
            this._super(ul, items);
            ul.addClass('dropdown-menu-table'); // give it the bootstrap look
        },
        '_renderItem': function _renderItem(table, item) {
            var tr = $('<tr></tr>').data('item.autocomplete', item);
            tr.append($('<td class="menu-label">' + item.label + '</td>'));
            if (_.has(item, 'description')) {
                tr.append($('<td class="menu-description">' + item.description + '</td>'));
            }
            tr.appendTo(table);
            return tr;
        }
    });

    /**
     * Set a new passage.  Programmatically set a new passage, eg. at page load.
     *
     * @function set_passage
     *
     * @param {int} pass_id - The new passage id
     */
    function set_passage(pass_id) {
        $.getJSON('passage.json/' + pass_id, function (json) {
            module.passage = json.data;
            $(document).trigger('ntg.panel.reload', [module.passage]);
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
    function suggest(data, complete) {
        var $elem = $(this.element);

        // collect values from all <input>s
        var $inputs = $elem.closest('form').find('input[data-autocomplete]');
        $inputs.each(function (i, e) {
            var $e = $(e);
            data[$e.attr('data-autocomplete')] = $e.val();
        });
        // get the name of the current field
        data.currentfield = $elem.attr('data-autocomplete');

        $.getJSON('suggest.json', data, complete);
    }

    function get_leitzeile(current_pass_id, $div) {
        $.getJSON('leitzeile/' + current_pass_id, function (json) {
            var accumulator = [[]];
            var last_pass_id = null;
            var i = 0;

            // group by pass_id
            var _iteratorNormalCompletion = true;
            var _didIteratorError = false;
            var _iteratorError = undefined;

            try {
                for (var _iterator = json.data.leitzeile[Symbol.iterator](), _step; !(_iteratorNormalCompletion = (_step = _iterator.next()).done); _iteratorNormalCompletion = true) {
                    var item = _step.value;

                    if (item.pass_id !== last_pass_id) {
                        accumulator[++i] = [];
                        last_pass_id = item.pass_id;
                    }
                    accumulator[i].push(item);
                }
            } catch (err) {
                _didIteratorError = true;
                _iteratorError = err;
            } finally {
                try {
                    if (!_iteratorNormalCompletion && _iterator.return) {
                        _iterator.return();
                    }
                } finally {
                    if (_didIteratorError) {
                        throw _iteratorError;
                    }
                }
            }

            var leitzeile = [];
            var _iteratorNormalCompletion2 = true;
            var _didIteratorError2 = false;
            var _iteratorError2 = undefined;

            try {
                for (var _iterator2 = accumulator[Symbol.iterator](), _step2; !(_iteratorNormalCompletion2 = (_step2 = _iterator2.next()).done); _iteratorNormalCompletion2 = true) {
                    var items = _step2.value;

                    if (items.length === 0) continue;
                    var pass_id = items[0].pass_id;
                    var tmp = _.map(items, 'lemma').join(' ');
                    var classes = [];
                    if (tmp === 'om') {
                        classes.push('leitzeile-insert');
                        tmp = '';
                    } else {
                        classes.push(items.length > 1 ? 'leitzeile-many' : 'leitzeile-one');
                    }
                    if (items[0].spanned) classes.push('leitzeile-spanned');
                    if (pass_id === current_pass_id) classes.push('leitzeile-current');
                    var class_ = classes.length ? ' class="' + classes.join(' ') + '"' : '';

                    if (pass_id) {
                        leitzeile.push('<a' + class_ + ' href="#' + pass_id + '">' + tmp + '</a>');
                    } else {
                        leitzeile.push('<span>' + tmp + '</span>');
                    };
                }
            } catch (err) {
                _didIteratorError2 = true;
                _iteratorError2 = err;
            } finally {
                try {
                    if (!_iteratorNormalCompletion2 && _iterator2.return) {
                        _iterator2.return();
                    }
                } finally {
                    if (_didIteratorError2) {
                        throw _iteratorError2;
                    }
                }
            }

            ;

            $div.html(leitzeile.join(' '));
        });
    }

    /**
     * Answer the user input on the navigator buttons.
     *
     * @function on_nav
     *
     * @param {Object} event - The event
     *
     * @return false
     */
    function on_nav(event) {
        var $target = $(event.currentTarget);
        var $form = $target.closest('form');
        var data = { 'button': $target.attr('data') || 'Go' };

        _.forEach($form.serializeArray(), function (value) {
            data[value.name] = value.value;
        });

        $.getJSON('passage.json', data, function (json) {
            module.passage = json.data;
            window.location.hash = '#' + json.data.passage; // trigger the move to the new passage
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
    function init() {
        // Tape recorder controls
        $('form.passage-selector').on('click', 'button', on_nav);
        $('form.passage-selector').on('submit', on_nav);

        $('form input[data-autocomplete]').tableautocomplete({
            'source': suggest,
            'minLength': 0,
            'position': { 'my': 'left top', 'at': 'left bottom+2', 'collision': 'flipfit' }
        }).on('click', function () {
            $(this).tableautocomplete('search');
        }).on('tableautocompletechange', function () {
            // clear following inputs
            $(this).nextAll('input').val('');
        }).on('tableautocompleteselect', function (event, dummy_ui) {
            var $this = $(this);
            $this.nextAll('input').val('');
            if ($this.attr('data-autocomplete') === 'word') {
                // give the control a chance to update the <input> before we call on_nav ()
                window.setTimeout(function () {
                    on_nav(event);
                });
            }
        });

        $(document).on('ntg.panel.reload', function (event, passage) {
            get_leitzeile(passage.pass_id, $('div.leitzeile'));
            var $form = $('form.passage-selector');
            $form.find('input[name="pass_id"]').val(passage.pass_id);

            $('form input[data-autocomplete]').each(function (i, e) {
                var $e = $(e);
                $e.val(passage[$e.attr('data-autocomplete')]);
            });
            $('h1 span.passage').text(passage.hr);
            $('title').text($('h1').text());

            // Fix 'next page' parameter in login / logout links
            var $links = $('a.user_login_link, a.user_logout_link');
            $links.each(function (i, e) {
                var $e = $(e);
                $e.attr('href', urijs($e.attr('href')).query({ 'next': window.location }));
            });
        });

        // User hit back-button, etc.
        $(window).on('hashchange', function () {
            set_passage(window.location.hash.substring(1));
        });

        return module;
    }

    module.init = init;
    module.set_passage = set_passage;
    /** JSON object.  Will be updated on navigation */
    module.passage = null;

    return module;
});

//# sourceMappingURL=navigator.js.map