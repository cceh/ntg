<template>
  <div class="vm-optimal-substemma-table">
    <div class="card-header d-print-none">
      <toolbar :toolbar="toolbar">
        <button-group slot="right" :options="options.csv" />
      </toolbar>
    </div>

    <table class="table table-bordered table-sm table-hover table-with-details table-sortable table-optimal-substemma"
           cellspacing="0">
      <thead>
        <tr @click="on_sort">
          <th class="details-control" />

          <th class="mss" data-sort-by="mss"
              title="The combination of ancestors.">Ancestors</th>

          <th class="count" data-sort-by="count"
              title="Number of ancestors in this combination.">N</th>

          <th class="equal" data-sort-by="equal"
              title="Number of variants explained by agreement with one of the ancestors.">Equal</th>

          <th class="post" data-sort-by="post"
              title="Number of variants not explained by agreement but by posteriority.">Post</th>

          <th class="unknown" data-sort-by="unknown"
              title="Cases of unknown source variant.">Unknown</th>

          <th class="open" data-sort-by="open"
              title="Cases not explained by this combination of ancestors.">Open</th>

          <th class="hint" data-sort-by="hint"
              title="Indicates the combination explaining the most variants in the descendant compared with combinations which are equal in number of ancestors.">Hint</th>
        </tr>
      </thead>
      <tbody>
        <template v-for="r in rows">
          <tr :key="r.index" :class="rowclass (r)">
            <td class="details-control" @click="toggle_details_table (r, $event)" />

            <td class="mss" @click="on_click (r.mss)">{{ r.mss }}</td>

            <td class="n">{{ r.count }}</td>

            <td class="equal">{{ r.equal }}</td>
            <td class="post">{{ r.post }}</td>
            <td class="unknown">{{ r.unknown }}</td>
            <td class="open">{{ r.open }}</td>
            <td class="hint">{{ r.hintc }}</td>
          </tr>
          <tr v-if="r.child" :key="r.index + '_child'" :data-index="r.index" class="child">
            <td />
            <td colspan="99">
              <optimal-substemma-details-table :ms="ms" :selection="r.mss" />
            </td>
          </tr>
        </template>
      </tbody>
    </table>
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
import csv_parse from 'csv-parse/lib/sync';
import { options } from 'widgets/options';

import optimal_substemma_details from 'optimal_substemma_details.vue';
import sort_mixin                from 'table_sort_mixin.vue';
import toggle_mixin              from 'table_toggle_mixin.vue';
import toolbar                   from 'widgets/toolbar.vue';
import button_group              from 'widgets/button_group.vue';

/**
 * Row conversion function.  Convert numeric values to numeric types
 * and add calculated fields.
 *
 * @function row_conversion
 *
 * @return The converted row
 */

function row_conversion (d) {
    return {
        'index'   : d.index,
        'mss'     : d.mss,
        'count'   : +d.count,
        'equal'   : +d.equal,
        'post'    : +d.post,
        'unknown' : +d.unknown,
        'open'    : +d.open,
        'hint'    : d.hint === 'True',
        'hintc'   : d.hint === 'True' ? '<<' : '',
        'child'   : false,
    };
}


export default {
    'props' : {
        'ms'        : String,
        'selection' : String,
    },
    'mixins'     : [sort_mixin, toggle_mixin],
    'components' : {
        'toolbar'                         : toolbar,
        'button-group'                    : button_group,
        'optimal-substemma-details-table' : optimal_substemma_details,
    },
    data () {
        return {
            'rows'        : [],
            'sorted_by'   : 'hint equal',
            'sorted_desc' : true,
            'options'     : options,
            'toolbar'     : {
                'csv' : () => this.download (), // show a download csv button
            },
        };
    },
    'watch' : {
        'ms' : function () {
            this.load_data ();
            this.sort ();
        },
        'selection' : function () {
            this.load_data ();
            this.sort ();
        },
    },
    'methods' : {
        load_data () {
            const vm = this;
            if (vm.ms && vm.selection) {
                vm.get (vm.build_url ()).then ((response) => {
                    const rows = csv_parse (response.data, { 'columns' : true });
                    vm.rows = rows.map (row_conversion);
                    vm.sort ();
                });
            } else {
                vm.rows = [];
            }
        },
        download () {
            window.open (this.build_full_api_url (this.build_url (), '_blank'));
        },
        build_url () {
            return 'optimal-substemma.csv?' + tools.param (this, ['ms', 'selection']);
        },
        on_click () {
            const vm = this;
            vm.$router.push ({
                'name' : 'set_cover',
                'hash' : '#' + tools.param ({
                    'ms'         : vm.ms,
                    'pre_select' : vm.selection,
                }),
            });
        },
        rowclass (r) {
            return (r.hint ? 'hint' : '') + (r.child ? ' shown' : '');
        },
    },
};
</script>

<style lang="scss">
/* optimal_substemma_table.vue */
@import "bootstrap-custom";

div.vm-optimal-substemma-table {
    table.table-optimal-substemma {
        tr.hint {
            background-color: $card-cap-bg;
        }

        > thead > tr > th,
        > tbody > tr > td {
            text-align: right;

            &.mss,
            &.hint {
                text-align: left;

                &[data-sort-by] {
                    padding-left: 1.5em;
                }
            }
        }
    }
}
</style>
