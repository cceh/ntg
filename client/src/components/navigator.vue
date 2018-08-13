<template>
  <div class="navigator_vm">
    <form class="form-inline" @submit="on_nav">

        <button type="button" data="-1" class="btn btn-primary mr-2"
                aria-label="Previous Passage" title="Previous Passage" @click="on_nav">
          <span class="fas fa-chevron-left" />
        </button>

        <div class="input-group">
          <div class="input-group-prepend">
            <span class="input-group-text">Nav:</span>
          </div>

          <input type="text" class="form-control" name="siglum" data-autocomplete="siglum"
                 aria-label="Book" title="Book" />
          <input type="text" class="form-control" name="chapter" data-autocomplete="chapter"
                 aria-label="Chapter" title="Chapter" />

          <div class="input-group-prepend input-group-append">
            <span class="input-group-text">:</span>
          </div>

          <input type="text" class="form-control" name="verse" data-autocomplete="verse"
                 aria-label="Verse" title="Verse" />

          <div class="input-group-prepend input-group-append">
            <span class="input-group-text">/</span>
          </div>

          <input type="text" class="form-control" name="word" data-autocomplete="word"
                 aria-label="Word" title="Word" />

          <span class="input-group-btn input-group-append">
            <button type="button" data="Go" class="btn btn-primary mr-2"
                    aria-label="Go" title="Go" @click="on_nav">
              <span class="fas fa-check" />
            </button>
          </span>
        </div>

        <button type="button" data="1" class="btn btn-primary"
                aria-label="Next Passage" title="Next Passage" @click="on_nav">
          <span class="fas fa-chevron-right" />
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

import 'jquery-ui-css/autocomplete.css';

/*
 * 1. Extend the stock autocomplete to use a <table> instead of a <ul> and give
 * it the bootstrap look.  Using a table we can display the passage id alongside
 * the passage lemma.  2. Give the source function a vm parameter.
 */

$.widget ('custom.tableautocomplete', $.ui.autocomplete, {
    '_renderMenu' : function (ul, items) {
        this._super (ul, items);
        ul.addClass ('custom-dropdown-menu-table'); // give it the bootstrap look
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
            if ((items[0].begadr % 2) === 1) {
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

<style lang="scss">
/* navigator.vue */
@import "bootstrap-custom";

div.navigator_vm {
    @media print {
        display: none;
    }

    form.form-inline {
        margin-bottom: $spacer;
        /* make buttons the same height as inputs */
        align-items: stretch;

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

        .leitzeile-inserted {
            &::before {
                content: '⸆'; /* 2e06 */
            }
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
}

/* displayed outside of parent ! */
.custom-dropdown-menu-table {
    display: table;
    z-index: $zindex-dropdown;
    float: left;
    padding: 5px 0;
    margin: 0;
    font-size: $font-size-base;
    text-align: left;
    background-color: $dropdown-bg;
    border: $dropdown-border-width solid $dropdown-border-color;
    background-clip: padding-box;

    /* stylelint-disable at-rule-no-unknown */
    @include border-radius($dropdown-border-radius);
    @include box-shadow($dropdown-box-shadow);

    &.ui-menu td.ui-menu-item-wrapper {
        padding: 3px 20px;

        &.ui-state-active {
            margin: 0;
            border-width: 0;
            color: $dropdown-link-active-color;
            background: $dropdown-link-active-bg;
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

</style>
