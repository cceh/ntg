<template>
  <div class="vm-optimal-substemma-details slider"> <!-- table cannot animate height -->
    <table ref="table" cellspacing="0" width="100%"
           class="table table-bordered table-condensed table-hover table-sortable table-optimal-substemma-details">
      <caption>
        <div class="d-flex justify-content-between">
          <div class="caption">Details of Combination {{ selection }}</div>
          <toolbar :toolbar="toolbar" class="d-print-none">
            <button-group slot="right" :options="options.csv" />
          </toolbar>
        </div>
      </caption>
      <thead>
        <tr @click="on_sort">
          <th class="type" data-sort-by="type">Type</th>
          <th class="pass_hr" data-sort-by="pass_id">Passage</th>
          <th class="lesart" data-sort-by="lesart">Lesart</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="r in rows" :key="r.pass_id" :class="(r.newer ? 'newer' : '') + (r.older ? 'older' : '')">
          <td class="type">{{ r.type }}</td>
          <td class="pass_hr">
            <router-link :to="{ 'name' : 'coherence', 'params' : { 'passage_or_id' : r.pass_id }}">{{ r.pass_hr }}</router-link>
          </td>
          <td class="lesart">{{ r.lesart }}</td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script>
/**
 * Exhaustive Search Details.  This module shows a drill-down table for any
 * combination with more detail about the explained variants.
 *
 * @component client/optimal_substemma_details
 * @author Marcello Perathoner
 */

import csv_parse from 'csv-parse/lib/sync';

import tools        from 'tools';
import sort_mixin   from 'table_sort_mixin.vue';
import button_group from 'widgets/button_group.vue';
import toolbar      from 'widgets/toolbar.vue';
import { options }  from 'widgets/options';

/**
 * Detail row conversion function.  Convert numeric values to numeric types
 * and add calculated fields.
 *
 * @param  {object} d - The original row
 * @return {object}   - The converted row
 */

function row_conversion (d) {
    return {
        'type'    : d.type,
        'pass_id' : +d.pass_id,
        'pass_hr' : d.pass_hr,
        'lesart'  : d.lesart,
    };
}

export default {
    'props' : {
        'ms'        : String,
        'selection' : String,
    },
    'mixins'     : [sort_mixin],
    'components' : {
        'button-group' : button_group,
        'toolbar'      : toolbar,
    },
    data () {
        return {
            'rows'      : [],
            'sorted_by' : 'pass_id',
            'options'   : options,
            'toolbar'   : {
                'csv' : () => this.download (), // show a download csv button
            },
        };
    },
    'methods' : {
        load_data () {
            const vm = this;
            vm.get (vm.build_url ()).then ((response) => {
                const rows = csv_parse (response.data, { 'columns' : true });
                vm.rows = rows.map (row_conversion);
                vm.sort ();
                vm.$nextTick (() => {
                    tools.slide_fade_in (vm.$el);
                });
            });
        },
        build_url () {
            return 'optimal-substemma-detail.csv?' + tools.param (this, ['ms', 'selection']);
        },
        download () {
            window.open (this.build_full_api_url (this.build_url (), '_blank'));
        },
    },
    mounted () {
        this.load_data ();
    },
};
</script>

<style lang="scss">
/* optimal_substemma_details.vue */
@import "bootstrap-custom.scss";

div.vm-optimal-substemma-details {
    height: 0;
    overflow: hidden;
    opacity: 0;

    table.table-optimal-substemma-details {
        margin-top: 0 !important;
        margin-bottom: 0 !important;
        background-color: $card-bg;
        border-width: 0;

        caption {
            caption-side: top;
            padding: $card-spacer-y $card-spacer-x;
            border-bottom: $table-border-width solid $table-border-color;
            font-weight: bold;
            color: inherit;
            background-color: $card-cap-bg;
        }

        thead {
            background-color: $card-cap-bg;
        }

        > thead > tr > th,
        > tbody > tr > td {
            text-align: left;

            &[data-sort-by] {
                padding-left: 1.5em;
            }

            &.type {
                width: 15%;
            }

            &.pass_hr {
                width: 15%;
            }
        }
    }
}
</style>
