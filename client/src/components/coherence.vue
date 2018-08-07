<template>
  <div>
    <!-- the parent for all floating panels must be at the top of the page so
         the panels will not move around on page resizes etc. this element will
         only contain absolute-positioned stuff and thus has a height of 0 -->
    <div id="floating-panels">
      <panel v-for="panel in floating_panels" :key="panel.id"
             :panel_id="panel.id" :position_target="panel.position_target"
             class="panel-closable panel-draggable panel-relatives">
        <toolbar name="relatives" mode="relatives" />
        <relmetrics :ms_id="panel.ms_id" />
        <relatives :ms_id="panel.ms_id" />
      </panel>
    </div>

    <navigator ref="nav" />

    <panel cssclass="panel-apparatus" static_caption="Apparatus">
      <toolbar name="apparatus" mode="apparatus" />
      <apparatus />
    </panel>

    <panel cssclass="panel-local-stemma" static_caption="Local Stemma">
      <toolbar name="stemma" mode="stemma" />
      <localstemma cssclass="stemma-wrapper local-stemma-wrapper">
        <d3stemma prefix="ls_" />
      </localstemma>
    </panel>

    <panel v-if="this.$store.state.current_user.is_editor"
           cssclass="panel-notes" static_caption="Notes" default_closed="true">
      <toolbar name="notes" mode="notes" />
      <notes />
    </panel>

    <panel cssclass="panel-textflow panel-variant-textflow"
           static_caption="Coherence at Variant Passages (GraphViz)">
      <toolbar name="variant" mode="variant" />
      <textflow cssclass="textflow-wrapper variant-textflow-wrapper"
                global="true" var_only="true">
        <d3stemma prefix="vtf_" />
      </textflow>
    </panel>

    <panel class="panel-textflow panel-variant-textflow-2"
           static_caption="Coherence at Variant Passages (Chord)" default_closed="true">
      <toolbar name="variant-2" mode="variant" />
      <textflow global="true" var_only="true" cssclass="textflow-wrapper variant-textflow-wrapper">
        <d3chord prefix="vtf2_" />
      </textflow>
    </panel>

    <panel ref="ltpanel" class="panel-textflow panel-local-textflow"
           static_caption="Coherence in Attestations">
      <toolbar name="local" mode="local" />
      <textflow cssclass="textflow-wrapper local-textflow-wrapper">
        <d3stemma prefix="tf_" />
      </textflow>
    </panel>

    <panel class="panel-textflow panel-global-textflow" static_caption="General Textual Flow">
      <toolbar name="global" mode="global" />
      <textflow global="true" cssclass="textflow-wrapper global-textflow-wrapper">
        <d3stemma prefix="gtf_" />
      </textflow>
    </panel>

    <navigator />

  </div>
</template>

<script>
/**
 * This module is the main entry point and displays the main page.  This module
 * is only a container for the other modules that actually display the gadgets.
 *
 * @module coherence
 * @author Marcello Perathoner
 */

import $ from 'jquery';
import Vue from 'vue';

import d3common  from 'd3-common';

import 'bootstrap.css';
import 'jquery-ui-css/all.css';

import navigator        from 'navigator.vue';
import panel            from 'panel.vue';
import toolbar          from 'toolbar.vue';
import apparatus        from 'apparatus.vue';
import notes            from 'notes.vue';
import d3_stemma_layout from 'd3_stemma_layout.vue';
import d3_chord_layout  from 'd3_chord_layout.vue';
import local_stemma     from 'local_stemma.vue';
import textflow         from 'textflow.vue';
import relatives        from 'relatives.vue';
import relmetrics       from 'relatives_metrics.vue';

Vue.component ('navigator',   navigator);
Vue.component ('panel',       panel);
Vue.component ('toolbar',     toolbar);
Vue.component ('apparatus',   apparatus);
Vue.component ('notes',       notes);
Vue.component ('localstemma', local_stemma);
Vue.component ('d3stemma',    d3_stemma_layout);
Vue.component ('d3chord',     d3_chord_layout);
Vue.component ('textflow',    textflow);
Vue.component ('relatives',   relatives);
Vue.component ('relmetrics',  relmetrics);

export default {
    'props' : ['current_user'],
    'data'  : function () {
        return {
            'floating_panels' : [],
            'panel_id'        : 0,
        };
    },
    'computed' : {
        'caption' : function () {
            return `Attestation for ${this.$store.state.passage.hr}`;
        },
    },
    'watch' : {
        'caption' : function () {
            this.$store.commit ('caption', this.caption);
        },
    },
    'methods' : {
        /**
         * Create a new popup managed by the relatives module.
         *
         * We have to create these dynamically because there may be many open at once.
         *
         * @function create_relatives_popup
         *
         * @param {integer} ms_id - The manuscript id
         * @param {jQuery} target - An element. The popup will be positioned relative to this element.
         */
        create_relatives_popup (ms_id, target) {
            this.panel_id += 1;
            this.floating_panels.push ({
                'id'              : this.panel_id,
                'ms_id'           : ms_id,
                'position_target' : target,
            });
        },
        destroy_relatives_popup (panel_id) {
            this.floating_panels = this.floating_panels.filter (item => item.id !== panel_id);
        },
    },
    created () {
        /**
         * Initialize the component.
         *
         * @function created
         */
        $ (document).off ('.data-api');
        const vm = this;

        // insert css for color palettes
        d3common.insert_css_palette (d3common.generate_css_palette (
            d3common.labez_palette,
            d3common.cliques_palette
        ));

        // install event handlers

        // Click on a ms. in the apparatus or in a relatives popup.
        $ (document).on ('click', '.ms[data-ms-id]', function (event) {
            event.stopPropagation ();
            let ms_id = $ (event.target).attr ('data-ms-id');
            vm.create_relatives_popup (ms_id, event.target);
        });

        // Click on a comparison row in the apparatus or in a relatives popup.
        $ (document).on ('click', 'tr.comparison[data-ms2-id]', function (event) {
            event.stopPropagation ();
            let ms1_id = $ (event.currentTarget).attr ('data-ms1-id');
            let ms2_id = $ (event.currentTarget).attr ('data-ms2-id');
            let win = window.open ('comparison#ms1=id' + ms1_id + '&ms2=id' + ms2_id, '_blank');
            win.focus ();
        });

        // Click on a node in the textflow diagram.
        $ (document).on ('click', 'div.panel-textflow g.node', function (event) {
            let ms_id = $ (event.currentTarget).attr ('data-ms-id'); // the g.node, not the circle
            vm.create_relatives_popup (ms_id, event.currentTarget);
        });

        // Click on canvas to close context menus
        $ (document).on ('click', function (dummy_event) {
            let $menu = $ ('table.contextmenu');
            $menu.fadeOut (() => $menu.remove ());
        });
    },
    mounted () {
        const nav = this.$refs.nav;

        // React to hash changes.  All navigation is done by manipulating the
        // hash.
        $ (window).on ('hashchange', () => {
            nav.set_passage (window.location.hash.substring (1));
        });

        // On first page load simulate user navigation to hash.
        if (window.location.hash) {
            nav.set_passage (window.location.hash.substring (1));
        } else {
            nav.set_passage (1);
        }
    },
};
</script>

<style lang="less">
@import "@{BS}/variables.less";
@import "@{BS}/mixins.less";

#floating-panels {
    position: relative;
    height: 0;
}

.ms[data-ms-id]:hover {
    cursor: pointer;
    text-decoration: underline;
}

a.highlight,
span.highlight {
    background-color: #ff0;
}

a.selected,
span.selected {
    outline: 2px solid #f00;
}

@link-color: #ccc;
@link-opacity: 0.6;

/* links */

path,
line,
text {
    &.link {
        stroke: @link-color;
        stroke-width: 2px;
        stroke-opacity: @link-opacity;
        fill: none;

        &.dashed {
            stroke-dasharray: 4 4;
        }

        &.hover {
            stroke-opacity: 1;
        }

        &.hi-source {
            stroke: red;
        }

        &.hi-target {
            stroke: green;
        }
    }
}

path,
line {
    &.link {
        &.hover {
            stroke-width: 3px;
        }
    }
}

text {
    dominant-baseline: middle;
    text-anchor: middle;
    fill: #000;
    cursor: pointer;
    pointer-events: none;

    &.link {
        stroke: #fff;
        stroke-width: 2px;
        stroke-linejoin: round;
        paint-order: stroke;

        &.hover {
            stroke-width: 2px;
            fill: black;
        }
    }
}

marker.link {
    stroke: @link-color;
    stroke-opacity: @link-opacity;
    fill: #000;
    fill-opacity: 1;
    stroke-dasharray: none;
    visibility: hidden;
}

div.variant-textflow-wrapper {
    path.link {
        stroke-dasharray: none;
    }

    marker.link {
        visibility: visible;
    }
}

/* nodes */

circle,
ellipse {
    &.node {
        stroke-width: 3px;
        fill: #fff;
        transition: fill 2s linear;
    }
}

g.clickable ellipse.node {
    cursor: pointer;
}

g.draggable ellipse.node {
    cursor: move;
}

line.link.highlight,
g.highlight ellipse.node {
    transition: fill 0.5s linear;
    fill: #ff0;
}

g.selected ellipse.node {
    transition: fill 0.5s linear;
    fill: #f00;
}

/* subgraphs */

rect.subgraph {
    stroke: @panel-default-border;
    stroke-width: 1px;
    fill: @panel-default-heading-bg;

    &.rounded {
        rx: 5px;
        ry: 5px;
    }
}

/* wrapper */

div.svg-wrapper {
    width: 100%;

    svg {
        display: block;
        margin: 1em auto;
    }
}

</style>
