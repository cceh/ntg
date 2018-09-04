<template>
  <b-button-toolbar class="justify-content-between">
    <b-form-radio-group v-if="'type' in toolbar" v-model="toolbar.type"
                        :options="type_checkbox_options"
                        buttons button-variant="primary" size="sm" />

    <b-form-radio-group v-if="'limit' in toolbar" v-model="toolbar.limit"
                        :options="limit_checkbox_options"
                        buttons button-variant="primary" size="sm" />

    <b-form-checkbox-group v-if="'cliques' in toolbar" v-model="toolbar.cliques"
                           :options="cliques_checkbox_options"
                           buttons button-variant="primary" size="sm" />

    <b-form-checkbox-group v-if="'ortho' in toolbar" v-model="toolbar.ortho"
                           :options="ortho_checkbox_options"
                           buttons button-variant="primary" size="sm" />

    <div v-if="'labez' in toolbar"
         class="btn-group btn-group-sm toolbar-labez">
      <button :data-labez="toolbar.labez" type="button"
              class="btn btn-primary dropdown-toggle dropdown-toggle-labez bg_labez"
              data-toggle="dropdown" aria-haspopup="true" aria-expanded="false">
        Variant:
        <span class="btn_text">{{ toolbar.labez }}</span> <span class="caret" />
      </button>
      <div class="dropdown-menu dropdown-menu-labez">
        <div class="btn-group btn-group-sm">
          <button v-for="[labez, labez_i18n] in dd_labez"
                  :key="labez" :data-labez="labez"
                  type="radio" data-type="dropdown"
                  class="btn btn-primary btn-labez bg_labez"
                  @click="on_dropdown_click ('labez', labez, $event)">{{ labez_i18n }}</button>
        </div>
      </div>
    </div>

    <!-- connectivity slider -->

    <div v-if="'connectivity' in toolbar"
         class="toolbar-connectivity btn-group btn-group-sm" role="group" data-toggle="buttons">

      <label class="btn btn-primary d-flex align-items-center"> <!-- moz needs align-center -->
        <span>Conn:</span>
        <span class="connectivity-label">{{ connectivity_formatter (connectivity) }}</span>
        <input v-model="connectivity" type="range" class="custom-range" min="1" max="21"
               @change="on_connectivity_change" />
        <datalist id="ticks" style="display: none">
          <option value="1"  label="1" />
          <option value="5"  label="5" />
          <option value="10" label="10" />
          <option value="20" label="20" />
          <option value="21" label="All" />
        </datalist>
      </label>
    </div>

    <div v-if="'range' in toolbar"
         class="btn-group btn-group-sm toolbar-range" role="group">
      <button type="button"
              class="btn btn-primary dropdown-toggle dropdown-toggle-range"
              data-toggle="dropdown" aria-haspopup="true" aria-expanded="false">
        Chapter:
        <span class="btn_text">{{ toolbar.range }}</span> <span class="caret" />
      </button>
      <div class="dropdown-menu dropdown-menu-range">
        <div class="btn-group btn-group-sm">
          <button v-for="range in dd_range" :key="range.range" :data-range="range.value"
                  type="radio" data-type="dropdown" class="btn btn-primary btn-range"
                  @click="on_dropdown_click ('range', range.value, $event)">{{ range.range }}</button>
        </div>
      </div>
    </div>

    <b-form-checkbox-group v-if="'include' in toolbar" v-model="toolbar.include"
                           :options="include_checkbox_options"
                           buttons button-variant="primary" size="sm" />

    <b-form-checkbox-group v-if="'fragments' in toolbar" v-model="toolbar.fragments"
                           :options="fragments_checkbox_options"
                           buttons button-variant="primary" size="sm" />

    <b-form-radio-group v-if="'mode' in toolbar" v-model="toolbar.mode"
                        :options="mode_checkbox_options"
                        buttons button-variant="primary" size="sm" />

    <div v-if="'hyp_a' in toolbar"
         class="btn-group btn-group-sm toolbar-hyp_a">
      <button :data-labez="toolbar.hyp_a" type="button"
              class="btn btn-primary dropdown-toggle dropdown-toggle-hyp_a bg_labez"
              data-toggle="dropdown" aria-haspopup="true" aria-expanded="false">
        <span>A =</span> <span class="btn_text">{{ toolbar.hyp_a }}</span> <span class="caret" />
      </button>
      <div class="dropdown-menu dropdown-menu-hyp_a">
        <div class="btn-group btn-group-sm">
          <button v-for="[labez, labez_i18n] in dd_hypa" :key="labez" :data-labez="labez"
                  type="radio" data-type="dropdown" class="btn btn-primary btn-labez bg_labez"
                  @click="on_dropdown_click ('hyp_a', labez, $event)">{{ labez_i18n }}</button>
        </div>
      </div>
    </div>

    <b-button-group size="sm" class="mr-auto">
      <b-button v-if="'save' in toolbar"
                :disabled="!toolbar.save" variant="primary" size="sm" class="d-print-none"
                @click="$emit ('save')">Save</b-button>
    </b-button-group>

    <b-button-group size="sm" class="d-print-none">
      <b-button v-if="'dot' in toolbar"
                variant="primary" title="Download graph in PNG format"
                @click="$emit ('png')">PNG</b-button>
      <b-button v-if="'png' in toolbar"
                variant="primary" title="Download graph in GraphViz .dot format"
                @click="$emit ('dot')">DOT</b-button>
      <b-button v-if="'csv' in toolbar"
                variant="primary" title="Download table in .csv format"
                @click="$emit ('csv')">CSV</b-button>
    </b-button-group>
  </b-button-toolbar>
</template>

<script>
/**
 * This module implements the toolbar that is on most of the cards.
 *
 * @component toolbar
 *
 * @author Marcello Perathoner
 */

import $ from 'jquery';
import 'bootstrap';

export default {
    'data' : function () {
        const type_checkbox_options = [
            { 'text' : 'Rel', 'value' : 'rel', 'title' : 'Show all relatives'    },
            { 'text' : 'Anc', 'value' : 'anc', 'title' : 'Show only ancestors'   },
            { 'text' : 'Des', 'value' : 'des', 'title' : 'Show only descendants' },
        ];
        const limit_checkbox_options = [
            { 'text' : '10',  'value' : '10', 'title' : 'Show 10 items'  },
            { 'text' : '20',  'value' : '20', 'title' : 'Show 20 items'  },
            { 'text' : 'All', 'value' : '0',  'title' : 'Show all items' },
        ];
        const include_checkbox_options = [
            { 'text' : 'A',   'value' : 'A',  'title' : 'Include A'  },
            { 'text' : 'MT',  'value' : 'MT', 'title' : 'Include Byzantine text' },
            { 'text' : 'Fam', 'value' : 'F',  'title' : 'Include text families'  },
        ];
        const mode_checkbox_options = [
            { 'text' : 'Sim', 'value' : 'sim', 'title' : 'Use simple priority calculation'  },
            { 'text' : 'Rec', 'value' : 'rec', 'title' : 'Use recursive priority calculation' },
        ];
        const cliques_checkbox_options = [
            { 'text' : 'Splits', 'value' : 'cliques', 'title' : 'Show split attestations'  },
        ];
        const ortho_checkbox_options = [
            { 'text' : 'Ortho',  'value' : 'ortho',   'title' : 'Show orthographic variations'  },
        ];
        const fragments_checkbox_options = [
            { 'text' : 'Frag', 'value' : 'fragments', 'title' : 'Include document fragments'  },
        ];

        if (!('connectivity' in this.$parent.toolbar)) {
            include_checkbox_options.push ({
                'text'  : 'Z',
                'value' : 'Z',
                'title' : 'Include mss. lacking this passage',
            });
        }
        return {
            // The trick is to reference the parent's toolbar instead of passing
            // it as prop.  Both the toolbar and the parent will watch the same
            // object.
            'toolbar' : this.$parent.toolbar,

            'limit_checkbox_options'     : limit_checkbox_options,
            'type_checkbox_options'      : type_checkbox_options,
            'include_checkbox_options'   : include_checkbox_options,
            'mode_checkbox_options'      : mode_checkbox_options,
            'cliques_checkbox_options'   : cliques_checkbox_options,
            'ortho_checkbox_options'     : ortho_checkbox_options,
            'fragments_checkbox_options' : fragments_checkbox_options,
            'connectivity'               : 5,
        };
    },
    'computed' : {
        passage () {
            return this.$store.state.passage;
        },
        readings () {
            // FIXME: filter zu
            return this.$store.state.passage.readings || [];
        },
        ranges () {
            return this.$store.state.ranges || [];
        },
        dd_labez () {
            const prefix = this.toolbar.labez_dropdown_prefix || [];
            const suffix = this.toolbar.labez_dropdown_suffix || [];
            return prefix.concat (this.readings).concat (suffix);
        },
        dd_hypa () {
            const prefix = [['A', 'A']];
            return prefix.concat (this.readings);
        },
        dd_range () {
            const prefix = [{ 'range' : 'This', 'value' : this.passage.chapter }];
            return prefix.concat (this.ranges);
        },
    },
    'watch' : {
        readings () {
            // reset toolbar if reading is not in new passage
            const mapped_readings = this.readings.map (item => item[0]);
            if (this.toolbar.labez && this.toolbar.reduce_labez
                && !mapped_readings.includes (this.toolbar.labez)) {
                this.toolbar.labez = mapped_readings[0];
            }
            if (this.toolbar.hyp_a
                && !mapped_readings.includes (this.toolbar.hyp_a)) {
                this.toolbar.hyp_a = 'A';
            }
        },
    },
    'methods' : {
        on_dropdown_click (name, data, event) {
            const $dropdown = $ (event.target).closest ('.dropdown-menu').parent ().find ('[data-toggle="dropdown"]');
            $dropdown.dropdown ('toggle');
            this.toolbar[name] = data;
        },
        on_connectivity_change () {
            this.toolbar.connectivity = this.connectivity;
        },
        connectivity_formatter (s) {
            return (s === '21') ? 'All' : s;
        },
    },
    mounted () {
        $ (this.$el).find ('.dropdown-toggle').dropdown ();
    },
};
</script>

<style lang="scss">
/* toolbar.vue */
@import "bootstrap-custom";

div.btn-toolbar {
    margin-bottom: $spacer * -0.5;
    margin-right: $spacer * -0.5;

    div.btn-group {
        margin-right: $spacer * 0.5;
        margin-bottom: $spacer * 0.5;
    }

    div.dropdown-menu {
        border: 0;
        padding: 0;
        background: transparent;
        min-width: 20rem;

        div.btn-group {
            flex-wrap: wrap;
        }

        button.btn {
            min-width: 2rem;
        }
    }

    div.dropdown-menu-range {
        button.btn {
            min-width: 3rem;
        }
    }

    label.btn.active {
        @media print {
            color: black !important;
        }
    }
}

div.card-relatives {
    div.dropdown-menu-labez {
        button.btn {
            min-width: 3rem;
        }
    }
}

div.toolbar-connectivity {
    label {
        margin-bottom: 0;

        span.connectivity-label {
            display: inline-block;
            width: 1.5em;
            text-align: right;
        }
    }

    input[type="range"] {
        width: 12em;
        padding-left:  ($spacer * 0.5);
        padding-right: ($spacer * 0.5);
    }
}
</style>
