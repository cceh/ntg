<template>
  <div class="comparison_vm want_hashchange" @hashchange="on_hashchange">

    <div class="container bs-docs-container">

      <div class="navigator">
        <form class="form-inline" @submit.prevent="submit">

          <div class="input-group">
            <div class="input-group-prepend">
              <span class="input-group-text">Witness 1:</span>
            </div>
            <input v-model="ms1" type="text" class="form-control"
                   title="Enter the Gregory-Aland no. of the first witness ('A' for the initial text)."
                   aria-label="Witness 1" />
          </div>

          <div class="input-group">
            <div class="input-group-prepend">
              <span class="input-group-text">Witness 2:</span>
            </div>
            <input v-model="ms2" type="text" class="form-control"
                   title="Enter the Gregory-Aland no. of the second witness ('A' for the initial text)."
                   aria-label="Witness 2" />
          </div>

          <button type="submit" data="Go" class="btn btn-primary"
                  title="Start the comparison.">Go</button>

        </form>
      </div>

      <card>
        <card-caption :slidable="false">
          {{ caption }}
        </card-caption>

        <comparison-table :ms1="mso1" :ms2="mso2" />
      </card>

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
 * @component client/comparison
 * @author Marcello Perathoner
 */

import tools from 'tools';

import card             from 'widgets/card.vue';
import card_caption     from 'widgets/card_caption.vue';
import comparison_table from 'comparison_table.vue';

export default {
    data () {
        return {
            'ms1'  : '',  // v-model
            'ms2'  : '',  // v-model
            'mso1' : {},
            'mso2' : {},
        };
    },
    'components' : {
        'card'             : card,
        'card-caption'     : card_caption,
        'comparison-table' : comparison_table,
    },
    'computed' : {
        'caption' : function () {
            if (this.mso1.hs && this.mso2.hs) {
                return `Comparison of Witnesses ${this.mso1.hs} and ${this.mso2.hs}`;
            }
            return this.$route.meta.caption;
        },
    },
    /** @lends module:client/comparison */
    'methods' : {
        /**
         * React to click of the submit button.  Change the hash.  Makes the
         * browser back button work.
         */
        submit () {
            tools.set_hash (this, ['ms1', 'ms2']);
        },
        /** React to hash changes.  Start a new comparison. */
        on_hashchange () {
            const vm = this;

            const params = tools.get_hash ();
            if (params.ms1 && params.ms2) {
                const requests = [
                    vm.get ('manuscript.json/' + params.ms1),
                    vm.get ('manuscript.json/' + params.ms2),
                ];

                Promise.all (requests).then ((responses) => {
                    vm.mso1 = responses[0].data.data;
                    vm.mso2 = responses[1].data.data;
                    vm.ms1 = vm.mso1.hs;
                    vm.ms2 = vm.mso2.hs;
                });
            } else {
                // reset data
                Object.assign (this.$data, this.$options.data ());
            }
        },
    },
    mounted () {
        this.on_hashchange ();
    },
};
</script>

<style lang="scss">
/* comparison.vue */
@import "bootstrap-custom";

div.comparison_vm {
    div.navigator {
        margin-bottom: $spacer;

        form.form-inline {
            /* make button same height as inputs */
            align-items: stretch;
        }

        .input-group {
            margin-right: ($spacer * 0.5);
        }

        input[type=text] {
            width: 6em;
        }

        @media print {
            display: none;
        }
    }
}
</style>
