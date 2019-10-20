<template>
  <div class="vm-optimal-substemma want_hashchange" @hashchange="on_hashchange">

    <div class="container bs-docs-container">

      <div class="navigator d-print-none">
        <form class="form-inline d-flex justify-content-between" @submit.prevent="submit">

          <div class="input-group">
            <div class="input-group-prepend">
              <span class="input-group-text">Witness:</span>
            </div>
            <input id="ms" v-model="input_ms" type="text" class="form-control"
                   title="Enter the Gregory-Aland-No. of the descendant witness."
                   aria-label="Descendant witness" />
          </div>

          <div class="input-group input-group-selection">
            <div class="input-group-prepend">
              <span class="input-group-text">Ancestors:</span>
            </div>
            <input id="selection" v-model="input_selection" type="text" class="form-control"
                   title="Enter a space-separated list of ancestor witnesses."
                   aria-label="List of Ancestors" />
          </div>

          <button type="submit" data="Go" class="btn btn-primary"
                  title="Do an exhaustive search of all combinations of the ancestors.">Go</button>

        </form>
      </div>

      <card class="card-optimal-substemma">
        <card-caption :slidable="false">
          {{ caption }}
        </card-caption>

        <optimal-substemma-table :ms="ms" :selection="selection" />
      </card>

    </div>
  </div>
</template>

<script>
/**
 * Find the optimal substemma of a witness by exhaustive search.
 *
 * See: Presentation 485ff
 *
 * @component optimal_substemma
 * @author Marcello Perathoner
 *
 * 1891 03 5 429 181 2298 04 0120 01
 */

import tools from 'tools';

import card                    from 'widgets/card.vue';
import card_caption            from 'widgets/card_caption.vue';
import optimal_substemma_table from 'optimal_substemma_table.vue';

export default {
    data () {
        return {
            'input_ms'        : '',
            'input_selection' : '',
            'ms'              : '',
            'selection'       : '',
            'open'            : 0,
        };
    },
    'components' : {
        'card'                    : card,
        'card-caption'            : card_caption,
        'optimal-substemma-table' : optimal_substemma_table,
    },
    'computed' : {
        caption () {
            if (this.ms) {
                const w = `${this.ms} (${this.open})`;
                this.$store.commit ('caption', `${w} - Optimal Substemma`);
                return `Optimal Substemma for Witness ${w} using ${this.selection}`;
            }
            return this.$route.meta.caption;
        },
    },
    'methods' : {
        submit () {
            tools.set_hash ({
                'ms'        : this.input_ms,
                'selection' : this.input_selection,
            });
        },
        on_hashchange () {
            const vm = this;
            const params = tools.get_hash ();

            if (params.ms && params.selection) {
                const requests = [
                    vm.get ('optimal-substemma.json', { 'params' : params }),
                ];

                Promise.all (requests).then ((responses) => {
                    const data = responses[0].data.data;
                    // reload table
                    vm.ms        = data.ms.hs;
                    vm.selection = data.mss.map (d => d.hs).join (' ');
                    // normalize user input
                    vm.input_ms        = vm.ms;
                    vm.input_selection = vm.selection;
                    vm.open            = data.ms.open;
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
/* optimal_substemma.vue */
@import "bootstrap-custom";

div.vm-optimal-substemma {
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

        .input-group-selection {
            flex-grow: 1;
        }
    }
}
</style>
