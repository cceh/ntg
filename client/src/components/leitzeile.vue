<template>
  <div class="vm-leitzeile">
    <div class="wrapper">
      <table class="item" v-for="item of leitzeile">
        <tr>
          <td>
            <router-link v-if="item.pass_id" :class="item.classes"
                         :to="{ 'name' : 'coherence', 'params' : { 'passage_or_id' : item.pass_id } }">
              {{ item.lemma }}
            </router-link>
            <span v-else="" :class="item.classes">{{ item.lemma }}</span>
          </td>
        </tr>
        <tr><td class="word">{{ item.word }}</td></tr>
      </table>
    </div>
  </div>
</template>

<script>
/**
 * This component displays the leitzeile.
 *
 * @component client/leitzeile
 * @author Marcello Perathoner
 */

import tools from 'tools';

export default {
    'props' : ['pass_id'],
    'data'  : function () {
        return {
            'leitzeile' : [],
        };
    },
    'watch' : {
        pass_id (new_pass_id) {
            this.load_leitzeile (new_pass_id);
        },
    },
    'methods' : {
        fix_leitzeile (item) {
            const vm = this;
            const classes = [];

            item.pass_id = item.pass_ids[0];

            if ((item.begadr % 2) === 1) {
                classes.push ('leitzeile-inserted');
            }

            classes.push ((item.pass_ids.length > 1) ? 'leitzeile-many' : 'leitzeile-one');

            if (item.pass_ids.includes (this.pass_id)) {
                classes.push ('leitzeile-current');
            }

            item.classes = classes.join (' ');
            item.word = item.begadr % 1000;
            return item;
        },
        load_leitzeile (new_pass_id) {
            const vm = this;
            const wrapper = vm.$el.querySelector ('.wrapper');
            wrapper.style.height = wrapper.scrollHeight + 'px';

            const requests = [
                vm.get ('leitzeile.json/' + new_pass_id),
                tools.fade_out (wrapper).promise,
            ];
            Promise.all (requests).then ((responses) => {
                vm.leitzeile = responses[0].data.data.map (vm.fix_leitzeile);
                vm.$nextTick (() => {
                    tools.slide_fade_in (wrapper, true);
                });
            });
        },
    },
};
</script>

<style lang="scss">
/* leitzeile.vue */
@import "bootstrap-custom.scss";

.vm-leitzeile {
    @media print {
        display: none;
    }

    div.wrapper {
        overflow: hidden;
    }

    margin-bottom: 20px;
    font-size: larger;

    table.item {
        display: inline-table;

        td.word {
            font-size: smaller;
            color: var(--gray);
        }
    }

    .leitzeile-current {
        color: #d62728;
        pointer-events: none;
    }

    .leitzeile-inserted {
        &::before {
            content: '⸆'; /* 2e06 */
        }
    }
}
</style>
