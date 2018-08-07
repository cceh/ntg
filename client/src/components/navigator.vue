<template>
  <div class="navigator">
    <form class="passage-selector form-inline" @submit="on_nav">

      <label class="sr-only">Previous Passage:</label>
      <button type="button" data="-1" class="btn btn-primary" title="Previous Passage" @click="on_nav">
        <span class="glyphicon glyphicon-triangle-left"/>
      </button>

      <div class="form-group">
        <div class="input-group">
          <span class="input-group-addon input-group-addon-leftmost">Nav:</span>

          <label class="sr-only">Book:</label>
          <input type="text" class="form-control" name="siglum" data-autocomplete="siglum" title="Book" />

          <label class="sr-only">Chapter:</label>
          <input type="text" class="form-control" name="chapter" data-autocomplete="chapter" title="Chapter" />

          <span class="input-group-addon input-group-addon-chapter">:</span>

          <label class="sr-only">Verse:</label>
          <input type="text" class="form-control" name="verse" data-autocomplete="verse" title="Verse" />

          <span class="input-group-addon input-group-addon-verse">/</span>

          <label class="sr-only">Word:</label>
          <input type="text" class="form-control" name="word" data-autocomplete="word" title="Word" />

          <span class="input-group-btn">
            <label class="sr-only">Go:</label>
            <button type="button" data="Go" class="btn btn-primary" title="Go" @click="on_nav">
              <span class="glyphicon glyphicon-ok"/>
            </button>
          </span>
        </div>
      </div>

      <label class="sr-only">Next Passage:</label>
      <button type="button" data="1" class="btn btn-primary" title="Next Passage" @click="on_nav">
        <span class="glyphicon glyphicon-triangle-right"/>
      </button>

      <input :value="this.$store.state.passage.pass_id" name="pass_id" type="hidden" />
    </form>

    <div class="leitzeile" v-html="leitzeile" />
  </div>
</template>

<script>
/**
 * This module implements the tape-recorder-controls navigator.
 *
 * To actually navigate this module changes the hash.
 *
 * @module navigator
 * @author Marcello Perathoner
 */

import $ from 'jquery';
import _ from 'lodash';
import 'jquery-ui/autocomplete.js';

import 'jquery-ui-css/all.css';

/*
 * 1. Extend the stock autocomplete to use a <table> instead of a <ul> and give
 * it the bootstrap look.  Using a table we can display the passage id alongside
 * the passage lemma.  2. Give the source function a vm parameter.
 */

$.widget ('custom.tableautocomplete', $.ui.autocomplete, {
    '_renderMenu' : function (ul, items) {
        this._super (ul, items);
        ul.addClass ('dropdown-menu-table'); // give it the bootstrap look
    },
    '_renderItem' : (table, item) => {
        let tr = $ ('<tr></tr>').data ('item.autocomplete', item);
        tr.append ($ ('<td class="menu-label">' + item.label + '</td>'));
        if (_.has (item, 'description')) {
            tr.append ($ ('<td class="menu-description">' + item.description + '</td>'));
        }
        tr.appendTo (table);
        return tr;
    },
    '_search' : function (value) {
        this.pending += 1;
        this._addClass ('ui-autocomplete-loading');
        this.cancelSearch = false;

        this.source ({ 'term' : value }, this._response (), this.options.vm);
    },
});

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
function suggest (data, complete, vm) {
    let $elem = $ (this.element);

    // collect values from all <input>s
    let $inputs = $elem.closest ('form').find ('input[data-autocomplete]');
    $inputs.each ((i, e) => {
        let $e = $ (e);
        data[$e.attr ('data-autocomplete')] = $e.val ();
    });
    // get the name of the current field
    data.currentfield = $elem.attr ('data-autocomplete');

    vm.get ('suggest.json', { 'params' : data }).then ((response) => complete (response.data));
}

function compute_leitzeile_html (leitzeile_json, current_pass_id) {
    let accumulator = [[]];
    let last_pass_id = null;
    let i = 0;

    // group by pass_id
    for (const item of leitzeile_json) {
        if (item.pass_id !== last_pass_id) {
            i += 1;
            accumulator[i] = [];
            last_pass_id = item.pass_id;
        }
        accumulator[i].push (item);
    }

    const leitzeile = [];
    for (const items of accumulator) {
        if (items.length !== 0) {
            const pass_id = items[0].pass_id;
            const classes = [];
            let tmp = _.map (items, 'lemma').join (' ');
            if ((items[0].anfadr % 2) === 1) {
                classes.push ('leitzeile-inserted');
                tmp = '';
            } else if (items[0].replaced) {
                classes.push ('leitzeile-replaced');
            } else {
                classes.push ('leitzeile-deleted');
            }
            classes.push ((items.length > 1) ? 'leitzeile-many' : 'leitzeile-one');
            if (items[0].spanned) {
                classes.push ('leitzeile-spanned');
            }
            if (pass_id === current_pass_id) {
                classes.push ('leitzeile-current');
            }
            const class_ = (classes.length) ? ` class="${classes.join (' ')}"` : '';

            if (pass_id) {
                leitzeile.push (`<a${class_} href="#${pass_id}">${tmp}</a>`);
            } else {
                leitzeile.push (`<span>${tmp}</span>`);
            }
        }
    }
    return leitzeile.join (' ');
}

export default {
    'data' : function () {
        return {
        };
    },
    'computed' : {
        passage () {
            return this.$store.state.passage;
        },
        leitzeile () {
            return compute_leitzeile_html (this.$store.state.leitzeile, this.$store.state.passage.pass_id);
        },
    },
    'methods' : {
        /**
         * Set a new passage.  Programmatically set a new passage, eg. at page load.
         *
         * @function set_passage
         *
         * @param {int} pass_id - The new passage id
         */
        set_passage (pass_id) {
            const vm = this;
            const requests = [
                vm.get ('passage.json/'   + pass_id),
                vm.get ('ranges.json/'    + pass_id),
                vm.get ('leitzeile.json/' + pass_id),
            ];
            Promise.all (requests).then ((responses) => {
                vm.$store.commit ('passage', {
                    'passage'   : responses[0].data.data,
                    'ranges'    : responses[1].data.data,
                    'leitzeile' : responses[2].data.data,
                });
            });
        },
        /**
         * Answer the user input on the navigator buttons.
         *
         * @function on_nav
         *
         * @param {Object} event - The event
         *
         * @return false
         */
        on_nav (event) {
            let $target = $ (event.currentTarget);
            let $form   = $target.closest ('form');
            let data    = { 'button' : $target.attr ('data') || 'Go' };

            _.forEach ($form.serializeArray (), (value) => {
                data[value.name] = value.value;
            });

            this.get ('passage.json/', { 'params' : data }).then ((response) => {
                // a hash change triggers the actual navigation
                window.location.hash = '#' + response.data.data.passage;
            });
            return false;
        },
    },
    'watch' : {
        passage () {
            const vm = this;
            $ ('form input[data-autocomplete]').each ((i, e) => {
                const $e = $ (e);
                $e.val (vm.passage[$e.attr ('data-autocomplete')]);
            });
        },
    },
    /**
     * Initialize the module.
     *
     * @function created
     */
    mounted () {
        const vm = this;

        $ ('form input[data-autocomplete]').tableautocomplete ({
            'vm'        : vm,
            'source'    : suggest,
            'minLength' : 0,
            'position'  : { 'my' : 'left top', 'at' : 'left bottom+2', 'collision' : 'flipfit' },
        })
            .on ('click', function () {
                $ (this).tableautocomplete ('search');
            })
            .on ('tableautocompletechange', function () {
                // clear following inputs
                $ (this).nextAll ('input').val ('');
            })
            .on ('tableautocompleteselect', function (event, dummy_ui) {
                let $this = $ (this);
                $this.nextAll ('input').val ('');
                if ($this.attr ('data-autocomplete') === 'word') {
                    // give the control a chance to update the <input> before we call on_nav ()
                    vm.$nextTick (() => {
                        vm.on_nav (event);
                    });
                }
            });
    },
};
</script>

<style lang="less">
@import "@{BS}/variables.less";
@import "@{BS}/mixins.less";

form.passage-selector {
    margin-bottom: 20px;

    input[type=text] {
        width: 12em;
    }

    .input-group {
        input.form-control {
            text-align: right;
            width: 3.5em;

            &[name=siglum] {
                text-align: left;
                border-right-width: 0;
            }

            &[name=word] {
                width: 6.5em;
            }
        }

        span.input-group-addon-chapter,
        span.input-group-addon-verse {
            padding: 6px;
            border-width: 1px 0;
        }
    }

    span.glyphicon {
        top: 2px;
        font-size: 90%;
    }
}

.dropdown-menu-table {
    display: table;
    z-index: @zindex-dropdown;
    float: left;
    padding: 5px 0;
    margin: 0;
    font-size: @font-size-base;
    text-align: left;
    background-color: @dropdown-bg;
    border: 1px solid @dropdown-fallback-border;
    border: 1px solid @dropdown-border;
    border-radius: @border-radius-base;
    background-clip: padding-box;
    .box-shadow(0 6px 12px rgba(0,0,0,.175));

    &.ui-menu td.ui-menu-item-wrapper {
        padding: 3px 20px;

        &.ui-state-active {
            margin: 0;
            border-width: 0;
            color: @dropdown-link-active-color;
            background: @dropdown-link-active-bg;
        }
        &.menu-label { text-align: right; }
        &.menu-description { padding-left: 0; }
    }

    tr.ui-menu-item {
        &.ui-state-active {
            margin: 0;
            border-width: 0;
            background: #ccc;
        }
    }
}

div.leitzeile {
    margin-bottom: 20px;
    font-size: larger;

    .leitzeile-current {
        color: #d62728;
        pointer-events: none;
    }

    .leitzeile-spanned {
        display: none;
        border-bottom: 1px dotted grey;
    }

    .xxx {
        .leitzeile-replaced.leitzeile-one {
            &::before {
                content: '⸀'; /* 2e00 */
            }
        }

        .leitzeile-replaced.leitzeile-many {
            &::before {
                content: '⸂';
            }

            &::after {
                content: '⸃';
            }
        }

        .leitzeile-inserted {
            &::before {
                content: '⸆'; /* 2e06 */
            }
        }

        .leitzeile-deleted.leitzeile-one {
            &::before {
                content: '⸋'; /* 2e0b */
            }
        }

        .leitzeile-deleted.leitzeile-many {
            &::before {
                content: '⸍'; /* 2e0d */
            }

            &::after {
                content: '⸌'; /* 2e0c */
            }
        }
    }
}
</style>
