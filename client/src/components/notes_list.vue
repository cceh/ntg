<template>
  <div class="notes_list_vm">

    <div class="container bs-docs-container" v-if="$store.getters.can_write">

      <card>
        <table class="table">
          <tr>
            <th>Passage</th><th>Note</th>
          </tr>
          <tr v-for="note in notes" :key="note.pass_id">
            <th><a :href="'coherence#pass_id=' + note.pass_id">{{ note.hr }}</a></th>
            <td class="prewrap">{{ note.note }}</td>
          </tr>
        </table>
      </card>

    </div>
  </div>
</template>

<script>
/**
 * Show a list of all notes.
 *
 * Internally uses a list of <notes>.
 *
 * @component notes_list
 * @author Marcello Perathoner
 */

import $   from 'jquery';
import Vue from 'vue';

import toolbar from 'widgets/toolbar.vue';
import notes   from 'notes.vue';

Vue.component ('toolbar', toolbar);
Vue.component ('notes',   notes);

export default {
    data () {
        return {
            'notes'    : [],
        };
    },
    'computed' : {
        'caption' : function () {
            return `Notes`;
        },
    },
    'mounted' : function () {
        const vm = this;
        const xhr1 = vm.get ('notes.json');
        Promise.all ([xhr1]).then ((responses) => {
            vm.notes = responses[0].data.data;
        });
    },
};
</script>

<style lang="scss">
/* notes_list.vue */
@import "bootstrap-custom";

div.notes_list_vm {
    .prewrap {
        white-space: pre-wrap;
    }
}
</style>
