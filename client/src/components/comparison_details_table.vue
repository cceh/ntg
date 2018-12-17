<template>
  <div class="comparison-details slider"> <!-- table cannot animate height -->
    <table ref="table" cellspacing="0" width="100%"
           class="table table-bordered table-condensed table-hover table-comparison-details">
      <caption>
        <div class="d-flex justify-content-between">
          <div class="caption">Comparison of {{ ms1.hs }} and {{ ms2.hs }} in Chapter {{ range }}</div>
          <toolbar :toolbar="toolbar">
            <button-group slot="right" :options="options.csv" />
          </toolbar>
        </div>
      </caption>
      <thead>
        <tr @click="on_sort">
          <th class="passage" data-sort-by="pass_id">Passage</th>
          <th class="lesart lesart1" data-sort-by="lesart1">Lesart</th>
          <th class="ms ms1" data-sort-by="labez_clique1">{{ ms1.hs }}</th>
          <th class="direction" data-sort-by="direction">Dir</th>
          <th class="ms ms2" data-sort-by="labez_clique2">{{ ms2.hs }}</th>
          <th class="lesart lesart2" data-sort-by="lesart2">Lesart</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="r in rows" :class="(r.newer ? 'newer' : '') + (r.older ? 'older' : '')" :key="r.pass_id">
          <td class="passage"><a :href="'coherence#pass_id=' + r.pass_id">{{ r.pass_hr }}</a></td>
          <td class="lesart lesart1">{{ r.lesart1 }}</td>
          <td class="ms ms1">{{ r.labez_clique1 }}</td>
          <td class="direction">{{ r.direction }}</td>
          <td class="ms ms2">{{ r.labez_clique2 }}</td>
          <td class="lesart lesart2">{{ r.lesart2 }}</td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script>
/**
 * Comparison of 2 witnesses.  This module shows a drill-down table for each range with
 * more detail about the differing passages.
 *
 * @component comparison_details_table
 * @author Marcello Perathoner
 */

import $ from 'jquery';
import _ from 'lodash';
import csv_parse from 'csv-parse/lib/sync';

import { options } from 'widgets/options';

/**
 * Return a direction marker: <, >, NoRel or Uncl.
 *
 * @function dir
 *
 * @param {object} r - The data row
 *
 * @return Direction marker.
 */

function dir (r) {
    if (r.older) {
        return '>';
    }
    if (r.newer) {
        return '<';
    }
    if (r.unclear) {
        return 'Uncl';
    }
    return 'NoRel';
}

/**
 * Detail row conversion function.  Convert numeric values to numeric types
 * and add calculated fields.
 *
 * @function row_conversion
 *
 * @return The converted row
 */

function row_conversion (d) {
    let r = {
        'pass_id'       : +d.pass_id,
        'pass_hr'       : d.pass_hr,
        'labez_clique1' : d.labez_clique1,
        'lesart1'       : d.lesart1,
        'labez_clique2' : d.labez_clique2,
        'lesart2'       : d.lesart2,
        'older'         : d.older   === 'True',
        'newer'         : d.newer   === 'True',
        'norel'         : d.norel   === 'True',
        'unclear'       : d.unclear === 'True',
    };
    r.direction = dir (r);
    return r;
}

export const sort_mixin = {
    data () {
        return {
            'sorted_by'   : '',
            'sorted_desc' : false,
            'options'     : options,
            'toolbar'     : {
                'csv' : () => this.download (), // show a download csv button
            },
        };
    },
    'watch' : {
        'sorted_by'   : function () { this.sort (); },
        'sorted_desc' : function () { this.sort (); },
    },
    'methods' : {
        on_sort (event) {
            const $th = $ (event.target);
            const sort_by = $th.attr ('data-sort-by');

            if (this.sorted_by === sort_by) {
                this.sorted_desc = !this.sorted_desc;
            } else {
                this.sorted_desc = false;
                this.sorted_by = sort_by;
            }
        },
        sort () {
            const vm = this;
            const rows = _.sortBy (vm.rows, [vm.sorted_by]);
            if (vm.sorted_desc) {
                _.reverse (rows);
            }
            vm.rows = rows;

            $ (vm.$el).find ('th[data-sort-by]').each (function (index, e) {
                const $th = $ (e);
                const sort_by = $th.attr ('data-sort-by');
                $th.toggleClass ('asc', false);
                $th.toggleClass ('desc', false);
                if (sort_by === vm.sorted_by) {
                    if (vm.sorted_desc) {
                        $th.toggleClass ('desc', true);
                    } else {
                        $th.toggleClass ('asc', true);
                    }
                }
            });
        },
    },
};


export default {
    'mixins' : [sort_mixin],
    'props'  : ['ms1', 'ms2', 'range'],
    data () {
        return {
            'rows'      : [],
            'sorted_by' : 'pass_id',
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
        build_url (page = 'comparison-detail.csv') {
            return page + '?' + $.param ({
                'ms1'   : 'id' + this.ms1.ms_id,
                'ms2'   : 'id' + this.ms2.ms_id,
                'range' : this.range,
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
/* comparison_table_details.vue */
@import "bootstrap-custom";

div.comparison-details {
    &.slider {
        display: none;
    }

    table.table-comparison-details {
        border-width: 0;

        th,
        td {
            text-align: left;

            &.passage {
                width: 15%;
            }

            &.direction {
                text-align: center;
                width: 5%;
            }

            &.lesart {
                width: 35%;
            }
        }

        th[data-sort-by]::after {
            left: auto;
            right: ($spacer * 0.25);
        }
    }
}
</style>
