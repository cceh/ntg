<template>
  <div class="optimal-substemma-details-vm slider"> <!-- table cannot animate height -->
    <table ref="table" cellspacing="0" width="100%"
           class="table table-bordered table-condensed table-hover table-sortable table-optimal-substemma-details">
      <caption>
        <div class="d-flex justify-content-between">
          <div class="caption">Details of Combination {{ mss }}</div>
          <toolbar :toolbar="toolbar">
            <button-group slot="right" :options="options.csv" />
          </toolbar>
        </div>
      </caption>
      <thead>
        <tr @click="on_sort">
          <th class="type"    data-sort-by="type">Type</th>
          <th class="pass_hr" data-sort-by="pass_id">Passage</th>
          <th class="lesart"  data-sort-by="lesart">Lesart</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="r in rows" :class="(r.newer ? 'newer' : '') + (r.older ? 'older' : '')" :key="r.pass_id">
          <td class="type">{{ r.type }}</td>
          <td class="pass_hr"><a :href="'coherence#pass_id=' + r.pass_id">{{ r.pass_hr }}</a></td>
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
 * @component optimal_substemma_details
 * @author Marcello Perathoner
 */

import $ from 'jquery';
import _ from 'lodash';
import csv_parse from 'csv-parse/lib/sync';

import { options }  from 'widgets/options';

import sort_mixin   from 'table_sort_mixin.vue';

/**
 * Detail row conversion function.  Convert numeric values to numeric types
 * and add calculated fields.
 *
 * @function row_conversion
 *
 * @return The converted row
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
    'mixins' : [sort_mixin],
    'props'  : ['ms', 'mss'],
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
            vm.get (this.build_url ()).then ((response) => {
                const rows = csv_parse (response.data, { 'columns' : true });
                vm.rows = rows.map (row_conversion);
                this.sort ();
                const $el = $ (vm.$el);
                $el.slideDown ();
            });
        },
        build_url (page = 'optimal-substemma-detail.csv?') {
            return page + $.param ({
                'ms'        : 'id' + this.ms.ms_id,
                'selection' : this.mss.split ('.').join (' '),
            });
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
@import "bootstrap-custom";

div.optimal-substemma-details-vm {
    &.slider {
        display: none;
    }

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
