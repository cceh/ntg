<template>
  <form class="navigator_vm want_hashchange form-inline"
        @hashchange="on_hashchange" @submit.prevent="on_nav">

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

      <div class="input-group-btn input-group-append">
        <button type="submit" data="Go" class="btn btn-primary mr-2"
                aria-label="Go" title="Go">
          <span class="fas fa-check" />
        </button>
      </div>
    </div>

    <button type="button" data="1" class="btn btn-primary"
            aria-label="Next Passage" title="Next Passage" @click="on_nav">
      <span class="fas fa-chevron-right" />
    </button>

    <input :value="this.$store.state.passage.pass_id" name="pass_id" type="hidden" />
  </form>
</template>

<script>
/**
 * This module implements the tape-recorder-controls navigator.
 *
 * It triggers a 'navigator' custom event with the passage id as parameter.
 *
 * @component navigator
 * @author Marcello Perathoner
 */

import $ from 'jquery';
import _ from 'lodash';
import 'jquery-ui/autocomplete.js';

import 'jquery-ui-css/core.css';
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

export default {
    'data' : function () {
        return {
        };
    },
    'computed' : {
        passage () {
            return this.$store.state.passage;
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
         */
        on_nav (event) {
            const $target = $ (event.currentTarget);
            const $form   = $target.closest ('form');
            const data    = { 'button' : $target.attr ('data') || 'Go' };

            _.forEach ($form.serializeArray (), (value) => {
                data[value.name] = value.value;
            });

            // transform user input into pass_id
            this.get ('passage.json/', { 'params' : data }).then ((response) => {
                this.$trigger ('navigator', response.data.data.passage);
            });
        },
        on_hashchange () {
            // update the control if hash changes
            // no need because we watch the store
            // const params = tools.deparam (window.location.hash.substring (1));
            // if ('pass_id' in params) {
            // }
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

.navigator_vm {
    @media print {
        display: none;
    }

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
