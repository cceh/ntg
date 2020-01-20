<template>
  <div class="vm-find-relatives want_hashchange" @hashchange="on_hashchange">
    <div class="container bs-docs-container">

      <card>
        <card-caption :slidable="false" :closable="false">
          <span v-html="caption" />
        </card-caption>

        <div class="card-header d-print-none">
          <div class="btn-toolbar">
            <navigator ref="navigator" v-model="pass_id" />
            <labezator ref="labezator" v-model="labez" :pass_id="pass_id" class="ml-2"
                       v-bind="options.labez" reduce="">
              Variant:
            </labezator>
          </div>
        </div>

        <div class="card-header">
          <toolbar :toolbar="tb_relatives">
            <button-group v-model="tb_relatives.type" type="radio" :options="options.type" />
            <button-group v-model="tb_relatives.limit" type="radio" :options="options.limit" />
            <labezator v-model="tb_relatives.labez" :pass_id="pass_id"
                       v-bind="options.labez_all">
              Variant:
            </labezator>
            <range v-model="tb_relatives.rg_id" :pass_id="pass_id">
              Chapter:
            </range>
            <button-group v-model="tb_relatives.include" type="checkbox" :options="options.include" />
            <button-group v-model="tb_relatives.fragments" type="checkbox" :options="options.fragments" />
            <button-group v-model="tb_relatives.mode" type="radio" :options="options.mode" />
          </toolbar>
        </div>

        <div class="card-header">
          {{ msg }}
          <ul class="list-inline">
            <li v-for="ms in ms_list" :key="ms.ms_id" @click="scroll_to ('id' + ms.ms_id)">
              <a>{{ ms.hs }}.</a>&nbsp;
            </li>
          </ul>
        </div>
      </card>

      <div class="columns">
        <card v-for="ms in ms_list" :id="'id' + ms.ms_id" :key="ms.ms_id" class="card-find-relatives">
          <relatives-table :pass_id="pass_id" :ms_id="parseInt (ms.ms_id)" :external_toolbar="tb_relatives" />
        </card>
      </div>

    </div>
  </div>
</template>

<script>
/**
 * Show all manuscripts with a certain attestation at a certain passage.
 *
 * Internally uses a list of <relatives-table> and a <toolbar>.
 *
 * @component client/find_relatives
 * @author Marcello Perathoner
 */

import csv_parse from 'csv-parse/lib/sync';

import tools       from 'tools';
import { options } from 'widgets/options';

import card            from 'widgets/card.vue';
import card_caption    from 'widgets/card_caption.vue';
import navigator       from 'widgets/navigator.vue';
import labezator       from 'widgets/labezator.vue';
import toolbar         from 'widgets/toolbar.vue';
import relatives_table from 'relatives_table.vue';
import button_group    from 'widgets/button_group.vue';

export default {
    data () {
        return {
            'labez'        : '',
            'pass_id'      : 0,
            'passage'      : {},
            'ms_list'      : [],
            'options'      : options,
            'tb_relatives' : {
                'type'      : 'rel',
                'limit'     : '10',
                'labez'     : 'all+lac',
                'rg_id'     : this.$store.state.current_application.rg_id_all || 0,
                'include'   : [],
                'fragments' : [],
                'mode'      : 'sim',
            },
        };
    },
    'components' : {
        'card'            : card,
        'card-caption'    : card_caption,
        'navigator'       : navigator,
        'labezator'       : labezator,
        'toolbar'         : toolbar,
        'button-group'    : button_group,
        'relatives-table' : relatives_table,
    },
    'computed' : {
        'caption' : function () {
            return `Manuscripts attesting '${this.labez}' at ${this.passage ? this.passage.hr : ''}`;
        },
        'msg' : function () {
            return `${this.ms_list.length} manuscripts: `;
        },
    },
    'watch' : {
        pass_id () {
            this.set_hash ();
        },
        labez () {
            this.set_hash ();
        },
    },
    'methods' : {
        set_hash () {
            tools.set_hash (this, ['pass_id', 'labez']);
        },
        on_hashchange () {
            const vm = this;
            const params = tools.get_hash ();

            vm.labez   = params.labez || '';
            vm.pass_id = parseInt (params.pass_id, 10) || 0;

            if (vm.pass_id && vm.labez) {
                const requests = [
                    vm.get ('passage.json/'  + vm.pass_id),
                    vm.get ('attesting.csv/' + vm.pass_id + '/' + vm.labez),
                ];
                Promise.all (requests).then ((responses) => {
                    vm.passage = responses[0].data.data;
                    vm.ms_list = csv_parse (responses[1].data, { 'columns' : true });
                });
            } else {
                vm.ms_list = [];
            }
        },
        /**
         * Scroll to the manuscript.
         *
         * @method goto_manuscript
         */
        scroll_to (id) {
            const top = document.getElementById (id).offsetTop;
            document.querySelector ('html').velocity ({
                'scrollTop' : top,
            });
        },
    },
    mounted () {
        this.on_hashchange ();
    },
};
</script>

<style lang="scss">
/* find_relatives.vue */
@import "bootstrap-custom";

div.vm-find-relatives {
    div.columns {
        column-width: 38em;
    }

    div.card {
        margin-bottom: 1rem;
    }

    div.card-header {
        &:last-child {
            border-bottom: none;
        }
    }

    div.card-find-relatives {
        break-inside: avoid;
    }

    ul.list-inline {
        display: inline;

        li {
            display: inline;
        }
    }
}
</style>
