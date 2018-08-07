<template>
  <div>
    <div class="navigator">
      <form class="manuscripts-selector form-inline" @submit.prevent="submit">
        <div class="form-group">
          <label>Witness 1:</label>
          <input v-model="input1" type="text" class="form-control" name="ms1"
                 title="Enter the Gregory-Aland no. of the first witness ('A' for the initial text)." />
          <label>Witness 2:</label>
          <input v-model="input2" type="text" class="form-control" name="ms2"
                 title="Enter the Gregory-Aland no. of the second witness ('A' for the initial text)." />
        </div>
        <button type="submit" data="Go" class="btn btn-primary"
                title="Start the comparison.">Go</button>
      </form>
    </div>

    <div class="panel panel-default panel-comparison">
      <comparison-table :ms1="ms1" :ms2="ms2" />
    </div>
  </div>
</template>

<script>
/**
 * Comparison of 2 witnesses.  This module shows a table with a global
 * comparison of two witnesses: in how many passages do they differ, how many
 * are older / younger? There is also a drill-down table for each range with
 * more detail about the differing passages.
 *
 * @component comparison
 * @author Marcello Perathoner
 */

import $ from 'jquery';
import Vue from 'vue';

import tools from 'tools';

import 'bootstrap.css';

import comparison_table from 'comparison_table.vue';

Vue.component ('comparison-table', comparison_table);

export default {
    data () {
        return {
            'ms1'    : { 'hs' : '-' },
            'ms2'    : { 'hs' : '-' },
            'input1' : '',
            'input2' : '',
        };
    },
    'computed' : {
        'caption' : function () {
            return `Comparison of ${this.ms1.hs} and ${this.ms2.hs}`;
        },
    },
    'watch' : {
        'caption' : function () {
            this.$store.commit ('caption', this.caption);
        },
    },
    'methods' : {
        submit (dummy_event) {
            window.location.hash = '#' + $.param ({
                'ms1' : this.input1,
                'ms2' : this.input2,
            });
        },
        on_hashchange () {
            const hash = window.location.hash.substring (1);
            if (hash) {
                const vm = this;
                const params = tools.deparam (hash);
                const p1 = vm.get ('manuscript.json/' + params.ms1);
                const p2 = vm.get ('manuscript.json/' + params.ms2);

                Promise.all ([p1, p2]).then ((p) => {
                    vm.ms1 = p[0].data.data;
                    vm.ms2 = p[1].data.data;
                    vm.input1 = vm.ms1.hs;
                    vm.input2 = vm.ms2.hs;
                });
            } else {
                // reset data
                Object.assign (this.$data, this.$options.data.call (this));
            }
        },
    },
    created () {
        const vm = this;
        $ (window).on ('hashchange', function () {
            vm.on_hashchange ();
        });
    },
    mounted () {
        // On first page load simulate user navigation to hash.
        if (window.location.hash) {
            this.on_hashchange ();
        } else {
            this.$store.commit ('caption', this.caption);
        }
    },
};
</script>

<style lang="less">
@import "@{BS}/variables.less";
@import "@{BS}/mixins.less";

div.navigator {
    margin-bottom: 1em;

    input[type=text] {
        width: 6em;
    }
}

div.panel-comparison {
    background-color: @panel-default-heading-bg;
}
</style>
