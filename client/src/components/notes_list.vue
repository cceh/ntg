<template>
  <div class="vm-notes-list want_hashchange" @hashchange="on_hashchange">

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
              <th>Passage</th><th>Note</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="note in notes" :key="note.pass_id">
              <th>
                <router-link :to="{ 'name' : 'coherence', 'params' : { 'passage_or_id' : note.pass_id }}">{{ note.hr }}</router-link>
              </th>
              <td class="prewrap">{{ note.note }}</td>
            </tr>
          </tbody>
        </table>
      </card>
    </div>
  </div>
</template>

<script>
/**
 * Show a list of all notes.
 *
 * @component client/notes_list
 * @author Marcello Perathoner
 */

import tools        from 'tools';

import card         from 'widgets/card.vue';
import card_caption from 'widgets/card_caption.vue';
import toolbar      from 'widgets/toolbar.vue';
import range        from 'widgets/range.vue';

export default {
    data () {
        return {
            'notes'   : [],
            'toolbar' : {
                'rg_id' : 0,
            },
        };
    },
    'components' : {
        'card'         : card,
        'card-caption' : card_caption,
        'toolbar'      : toolbar,
        'range'        : range,
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
                    vm.get ('notes.json/' + vm.toolbar.rg_id),
                ];
                Promise.all (requests).then ((responses) => {
                    vm.notes = responses[0].data.data;
                });
            } else {
                vm.notes = [];
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
/* notes_list.vue */
@import "bootstrap-custom";

div.vm-notes-list {
    .prewrap {
        white-space: pre-wrap;
    }

    table.table {
        margin: 1rem 0;
    }
}
</style>
