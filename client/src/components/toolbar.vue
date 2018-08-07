<template>
  <div :class="'panel-heading panel-slidable panel-toolbar panel-' + name + '-toolbar'">
    <div :class="'btn-toolbar toolbar ' + name + '-toolbar'" role="toolbar">

      <div v-if="mode == 'relatives'" class="relatives-type btn-group btn-group-xs" data-toggle="buttons">
        <label class="btn btn-primary">
          <input type="radio" name="type" data-opt="rel" />Rel
        </label>
        <label class="btn btn-primary">
          <input type="radio" name="type" data-opt="anc" />Anc
        </label>
        <label class="btn btn-primary">
          <input type="radio" name="type" data-opt="des" />Des
        </label>
      </div>

      <div v-if="mode == 'relatives'" class="relatives-limit btn-group btn-group-xs" data-toggle="buttons">
        <label class="btn btn-primary">
          <input type="radio" name="limit" data-opt="10" />10
        </label>
        <label class="btn btn-primary">
          <input type="radio" name="limit" data-opt="20" />20
        </label>
        <label class="btn btn-primary">
          <input type="radio" name="limit" data-opt="0" />All
        </label>
      </div>

      <div v-if="['apparatus', 'variant'].includes (mode)"
           class="apparatus-cliques btn-group btn-group-xs" data-toggle="buttons">
        <label class="btn btn-primary">
          <input type="checkbox" name="cliques" data-opt="cliques" />Splits
        </label>
      </div>

      <div v-if="['local', 'relatives'].includes (mode)" class="toolbar-labez btn-group btn-group-xs">
        <button :data-labez="toolbar.labez" type="button"
                class="btn btn-primary dropdown-toggle dropdown-toggle-labez bg_labez"
                data-toggle="dropdown" aria-haspopup="true" aria-expanded="false">
          Variant:
          <span class="btn_text">{{ toolbar.labez }}</span> <span class="caret" />
        </button>
        <div class="dropdown-menu dropdown-menu-horiz dropdown-menu-labez">
          <div class="btn-group btn-group-xs" data-toggle="buttons">
            <template v-for="[labez, labez_i18n] in dd_labez">
              <label :key="labez" :data-labez="labez"
                     class="btn btn-primary btn-labez bg_labez">
                <input :data-opt="labez" type="radio"
                       data-type="dropdown" name="labez" />{{ labez_i18n }}
              </label>
            </template>
          </div>
        </div>
      </div>

      <div v-if="['local', 'variant'].includes (mode)" class="toolbar-connectivity btn-group btn-group-xs"
           data-toggle="buttons">
        <label class="btn btn-primary">
          Conn:
          <span class="connectivity-label">{{ connectivity_formatter (toolbar.connectivity) }}</span>
          <input :value="toolbar.connectivity" type="text" data-type="slider" name="connectivity" />
        </label>
      </div>

      <div v-if="['global', 'local', 'variant', 'relatives'].includes (mode)"
           class="toolbar-range btn-group btn-group-xs">
        <button type="button" class="btn btn-primary dropdown-toggle dropdown-toggle-range"
                data-toggle="dropdown" aria-haspopup="true" aria-expanded="false">
          Chapter:
          <span class="btn_text">{{ toolbar.range }}</span> <span class="caret" />
        </button>
        <div class="dropdown-menu dropdown-menu-horiz dropdown-menu-range">
          <div class="btn-group btn-group-xs" data-toggle="buttons">
            <template v-for="range in dd_range">
              <label :key="range.range" :data-range="range.value"
                     class="btn btn-primary btn-range">
                <input :data-opt="range.value" type="radio"
                       data-type="dropdown" name="range" />{{ range.range }}
              </label>
            </template>
          </div>
        </div>
      </div>

      <div v-if="['global', 'local', 'variant', 'relatives'].includes (mode)"
           class="toolbar-include btn-group btn-group-xs" data-toggle="buttons">
        <label class="btn btn-primary" title="Include A">
          <input type="checkbox" name="include" data-opt="A" />A
        </label>
        <label class="btn btn-primary" title="Include Byzantine Text">
          <input type="checkbox" name="include" data-opt="MT" />MT
        </label>
        <label class="btn btn-primary" title="Include text families">
          <input type="checkbox" name="include" data-opt="F" />Fam
        </label>
        <label v-if="mode === 'global'" class="btn btn-primary" title="Include mss. lacking this passage">
          <input type="checkbox" name="include" data-opt="Z" />Z
        </label>
      </div>

      <div v-if="['local', 'relatives'].includes (mode)"
           class="coherence-fragments btn-group btn-group-xs" data-toggle="buttons">
        <label class="btn btn-primary">
          <input type="checkbox" name="fragments" data-opt="fragments" />Frag
        </label>
      </div>

      <div v-if="['global', 'local', 'variant', 'relatives'].includes (mode)"
           class="toolbar-mode btn-group btn-group-xs" data-toggle="buttons">
        <label class="btn btn-primary">
          <input type="radio" name="mode" data-opt="rec" />Rec
        </label>
        <label class="btn btn-primary">
          <input type="radio" name="mode" data-opt="sim" />Sim
        </label>
      </div>

      <div v-if="['local', 'variant'].includes (mode)" class="toolbar-hyp_a btn-group btn-group-xs">
        <button :data-labez="toolbar.hyp_a" type="button"
                class="btn btn-primary dropdown-toggle dropdown-toggle-hyp_a bg_labez"
                data-toggle="dropdown" aria-haspopup="true" aria-expanded="false">
          <span>A =</span> <span class="btn_text">{{ toolbar.hyp_a }}</span> <span class="caret" />
        </button>
        <div class="dropdown-menu dropdown-menu-horiz dropdown-menu-hyp_a">
          <div class="btn-group btn-group-xs" data-toggle="buttons">
            <template v-for="[labez, labez_i18n] in dd_hypa">
              <label :key="labez" :data-labez="labez"
                     class="btn btn-primary btn-labez bg_labez">
                <input :data-opt="labez" type="radio"
                       data-type="dropdown" name="hyp_a" />{{ labez_i18n }}
              </label>
            </template>
          </div>
        </div>
      </div>

      <div v-if="mode == 'notes'" class="coherence-notes btn-group btn-group-xs" data-toggle="buttons">
        <button type="button" class="btn btn-primary" name="save" data-opt="save"
                title="Save Notes">Save</button>
      </div>

      <div v-if="['stemma', 'global', 'local', 'variant'].includes (mode)"
           class="coherence-dot btn-group btn-group-xs" data-toggle="buttons">
        <a :href="$parent.toolbar.png_url"
           type="button" class="btn btn-primary" name="png" data-opt="png"
           title="Download graph in PNG format">PNG</a>
        <a :href="$parent.toolbar.dot_url" :download="$parent.caption.trim () + '.dot'"
           type="button" class="btn btn-primary" name="dot" data-opt="dot"
           title="Download graph in GraphViz .dot format">DOT</a>
      </div>
    </div>
  </div>
</template>

<script>
/**
 * This module implements the toolbar that is on most of the panels.
 *
 * @module toolbar
 *
 * @author Marcello Perathoner
 */

import $ from 'jquery';
import _ from 'lodash';
import 'tools';
import 'bootstrap';
import 'bootstrap-slider';

import 'bootstrap-slider.css';

function get_control_type ($input) {
    return $input.attr ('data-type') || $input.attr ('type') || 'button';
}

/**
 * Read the status of the toolbar buttons after event
 *
 * @function handle_toolbar_events
 *
 * @param {Object} event - The event.  The status is saved in
 *                         event.data.data
 */

function handle_toolbar_events (event, opts) {
    if (event.type === 'click' || event.type === 'slideStop') {
        var $target = $ (event.target);
        var $group  = $target.closest ('.btn-group');
        var name    = $target.attr ('name');
        var type    = get_control_type ($target);

        switch (type) {
        case 'checkbox':
            opts[name] = [];
            $group.find ('input:checked').each (function (i, btn) {
                opts[name].push ($ (btn).attr ('data-opt'));
            });
            return 1;
        case 'radio':
            opts[name] = $target.attr ('data-opt');
            return 1;
        case 'slider':
            opts[name] = $target.bootstrapSlider ('getValue');
            return 1;
        case 'dropdown':
            opts[name] = $target.attr ('data-opt');
            var $dropdown = $group.parent ().closest ('.btn-group').find ('button[data-toggle="dropdown"]');
            $dropdown.dropdown ('toggle'); // close
            return 1;
        default:
        }
    }
    return 0;
}

/**
 * Set the status of the toolbar buttons
 *
 * @function set_toolbar_buttons
 *
 * @param {Object} vm - The Vue instance
 */

function set_toolbar_buttons (vm) {
    const $root = $ (vm.$el);
    const opts = vm.toolbar;

    _.forEach (opts, function (value, key) {
        var $input = $root.find ('input[name="' + key  + '"]');
        var $group = $input.closest ('.btn-group');
        var type   = get_control_type ($input);

        switch (type) {
        case 'checkbox':
            $group.find ('label.btn').removeClass ('active');
            $group.find ('input').prop ('checked', false);

            _.forEach (value, function (v) {
                $input = $group.find ('input[name="' + key  + '"][data-opt="' + v + '"]');
                $input.prop ('checked', true);
                $input.closest ('label.btn').addClass ('active');
            });
            break;
        case 'radio':
            $input = $group.find ('input[name="' + key  + '"][data-opt="' + value + '"]');
            $input.checked = true;
            $group.find ('label.btn').removeClass ('active');
            $input.closest ('label.btn').addClass ('active');
            break;
        case 'slider':
            // $input.bootstrapSlider ('setValue', +value);
            // $root.find ('span.connectivity-label').text (connectivity_formatter (value));
            break;
        case 'dropdown':
            /* if (key === 'hyp_a') {
                key = 'labez';
            }
            var $dropdown = $group.parent ().closest ('.btn-group').find ('button[data-toggle="dropdown"]');
            $dropdown.attr ('data-' + key, value);
            var i18n = $.trim ($group.find (`label.btn[data-${key}="${value}"]`).text ());
            $dropdown.find ('span.btn_text').text (i18n);
            */
            break;
        default:
        }
    });
}

export default {
    'props' : ['name', 'mode'],
    'data'  : function () {
        return {
        };
    },
    'computed' : {
        toolbar () {
            return this.$parent.toolbar;
        },
        passage () {
            return this.$store.state.passage;
        },
        readings () {
            return this.$store.state.passage.readings || [];
        },
        ranges () {
            return this.$store.state.ranges || [];
        },
        dd_labez () {
            const prefix = this.toolbar.labez_dropdown_prefix || [];
            return prefix.concat (this.readings);
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
            if (this.toolbar.labez
                && !mapped_readings.includes (this.toolbar.labez)) {
                this.toolbar.labez = mapped_readings[0];
            }
            if (this.toolbar.hyp_a
                && !mapped_readings.includes (this.toolbar.hyp_a)) {
                this.toolbar.hyp_a = 'A';
            }
            set_toolbar_buttons (this);
        },
        ranges () {
            set_toolbar_buttons (this);
        },
    },
    'methods' : {
        connectivity_formatter (s) {
            return (s === 21) ? 'All' : s;
        },
    },
    mounted () {
        let $toolbar = $ (this.$el);

        // Init toolbar.
        $toolbar.find ('.dropdown-toggle').dropdown ();

        $toolbar.find ('input[name="connectivity"]').bootstrapSlider ({
            'value'           : 5,
            'ticks'           : [1,  5, 10, 20,  21],
            'ticks_positions' : [0, 25, 50, 90, 100],
            'formatter'       : this.connectivity_formatter,
        });

        const vm = this;
        set_toolbar_buttons (vm);
        $toolbar.on ('click slideStop', 'input', this, function (event) {
            if (handle_toolbar_events (event, vm.toolbar)) {
                // Answer toolbar activity.
                vm.$parent.get_view_vm ().load_passage ();  // reload the view with the new params
                set_toolbar_buttons (vm);
            }
            event.stopPropagation ();
        });
    },
};
</script>

<style lang="less">
@import "@{BS}/variables.less";
@import "@{BS}/mixins.less";

div.toolbar-connectivity {
    .slider {
        margin-left: 1em;
        margin-right: 1em;
    }

    span.connectivity-label {
        display: inline-block;
        width: 1.5em;
        text-align: right;
    }
}

div.panel-toolbar {
    .slider-handle {
        width: 12px;
        height: 12px;
        opacity: 1;
    }

    .slider-tick {
        width: 8px;
        height: 8px;
        opacity: 1;
    }

    .slider.slider-horizontal {
        width: 200px;
        height: 16px;

        .slider-handle {
            top: 50%;
            margin-top: -6px;
            margin-left: -6px;
        }

        .slider-tick {
            top: 50%;
            margin-top: -4px;
            margin-left: -4px;
        }

        .slider-track {
            top: 50%;
            height: 4px;
            margin-top: -2px;
        }

        .slider-tick-container {
            top: 50%;
        }
    }
}

div.btn-toolbar {
    margin-top: -5px;

    > div.btn-group {
        margin-top: 5px;

        &.coherence-dot {
            float: right;
        }
    }
}

div.dropdown-menu div.btn-group {
    margin-top: 0;
}

div.dropdown-menu-horiz {
    position: absolute;
    top: 100%;
    left: 0;
    border-width: 0;
    padding: 0;
    min-width: 20px;
    width: 160px;
    width: -moz-max-content;
    width: -webkit-max-content;
    width: max-content;
}
</style>
