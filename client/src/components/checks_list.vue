<template>
  <div class="vm-checks-list want_hashchange" @hashchange="on_hashchange">

    <div v-if="$store.getters.can_read_private" class="container bs-docs-container">

      <card>
        <card-caption :slidable="false">
          {{ caption }}
        </card-caption>

        <div class="card-header d-print-none">
          <toolbar :toolbar="toolbar">
            <range v-model="toolbar.rg_id" :pass_id="0">
              Chapter:
            </range>
          </toolbar>
        </div>

        <table class="table">
          <thead>
            <tr>
              <th>Passage</th><th>Ancestor</th><th>Descendant</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="loading">
              <td colspan="3">
                <div class="spinner">
                  <b-spinner variant="info" label="Loading..."></b-spinner>
                </div>
              </td>
            </tr>
            <tr v-for="check in checks" :key="`${check.pass_id}-${check.ms1}-${check.ms2}`">
              <th>
                <router-link :to="{ 'name' : 'coherence', 'params' : { 'passage_or_id' : check.pass_id }}" target="_blank">{{ check.hr }}</router-link>
              </th>
              <td>{{ check.labez1 }}: {{ check.ms1 }}</td>
              <td>{{ check.labez2 }}: {{ check.ms2 }}</td>
            </tr>
          </tbody>
        </table>
      </card>
    </div>
  </div>
</template>

<script>
/**
 * Show a list of all checks.
 *
 * @component client/checks_list
 * @author Marcello Perathoner
 */

import { BSpinner } from 'bootstrap-vue/src/components/spinner/spinner';

import tools        from 'tools';

import card         from 'widgets/card.vue';
import card_caption from 'widgets/card_caption.vue';
import toolbar      from 'widgets/toolbar.vue';
import range        from 'widgets/range.vue';

export default {
    data () {
        return {
            'checks'  : [],
            'toolbar' : {
                'rg_id' : 0,
            },
            'loading' : false,
        };
    },
    'components' : {
        'card'         : card,
        'card-caption' : card_caption,
        'toolbar'      : toolbar,
        'range'        : range,
        'b-spinner'    : BSpinner,
    },
    'computed' : {
        'caption' : function () {
            const f = this.$store.state.ranges.filter (d => d.rg_id === this.toolbar.rg_id);
            const rg = f.length ? f[0].range : 'All';
            const msg = rg !== 'All' ? ` for Chapter ${rg}` : '';
            return `${this.$route.meta.caption}${msg}`;
        },
    },
    'watch' : {
        'toolbar.rg_id' : function () {
            tools.set_hash (this.toolbar);
        },
    },
    'methods' : {
        on_hashchange () {
            const vm = this;
            const params = tools.get_hash ();

            vm.toolbar.rg_id = parseInt (params.rg_id, 10) || 0;

            if (vm.toolbar.rg_id > 0) {
                const requests = [
                    vm.get ('checks/congruence_list.json/' + vm.toolbar.rg_id),
                ];
                vm.checks = [];
                vm.loading = true;
                Promise.all (requests).then ((responses) => {
                    vm.checks = responses[0].data.data;
                }).finally (() => {
                    vm.loading = false;
                });
            } else {
                vm.checks = [];
            }
        },
    },
    mounted () {
        // On first page load simulate user navigation to hash.
        this.on_hashchange ();
    },
};
</script>

<style lang="scss">
/* checks_list.vue */

div.vm-checks-list {
    .prewrap {
        white-space: pre-wrap;
    }

    table.table {
        margin: 1rem 0;
    }

    div.spinner {
        text-align: center;
    }
}
</style>
