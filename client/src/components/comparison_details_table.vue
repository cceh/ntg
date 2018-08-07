<template>
  <tr class="no-padding">
    <td class="no-padding" />
    <td class="no-padding" colspan="99">
      <div class="slider">
        <table ref="table" cellspacing="0" width="100%"
               class="comparison-detail table table-bordered table-condensed table-hover">
          <caption>
            <span class="caption">Comparison of {{ ms1.hs }} and {{ ms2.hs }} in Chapter {{ range }}</span>
            <div ref="toolbar" class="btn-toolbar toolbar toolbar-comparison-detail" role="toolbar" />
          </caption>
          <thead>
            <tr>
              <th class="passage exportable">Passage</th>
              <th class="lesart lesart1 exportable">Lesart</th>
              <th class="ms ms1 exportable">{{ ms1.hs }}</th>
              <th class="direction exportable">Dir</th>
              <th class="ms ms2 exportable">{{ ms2.hs }}</th>
              <th class="lesart lesart2 exportable">Lesart</th>
            </tr>
          </thead>
          <tbody />
        </table>
      </div>
    </td>
  </tr>
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
import csv_parse from 'csv-parse/lib/sync';

import 'datatables.net';
import 'datatables.net-bs';

import 'bootstrap.css';
import 'datatables.net-bs.css';

import { default_table_options } from 'comparison_table.vue';

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


export default {
    'props' : ['ms1', 'ms2', 'range'],
    data () {
        return {
        };
    },
    'methods' : {
        load_data () {
            let url = 'comparison-detail.csv?' + $.param ({
                'ms1'   : 'id' + this.ms1.ms_id,
                'ms2'   : 'id' + this.ms2.ms_id,
                'range' : this.range,
            });

            const vm = this;
            vm.get (url).then ((response) => {
                const rows = csv_parse (response.data, { 'columns' : true });
                const $el = $ (vm.$el);
                $el.addClass ('csv-loaded');
                const $table = $ (vm.$refs.table);
                const data_table = $table.DataTable (); // eslint-disable-line new-cap
                data_table.clear ().rows.add (rows.map (row_conversion)).draw ();
                $ ('div.slider', $el).slideDown ();
            });
        },
    },
    mounted () {
        /**
         * Initialize the details table structure.  This has to be done only once.
         * On navigation we'll throw the details table away.
         */

        const $table = $ (this.$refs.table);

        $table.DataTable ( // eslint-disable-line new-cap
            $.extend ({}, default_table_options, {
                'columns' : [
                    {
                        'data' : function (r, type /* , val, meta */) {
                            if (type === 'sort') {
                                return r.pass_id;
                            }
                            return '<a href="coherence#' + r.pass_id + '">' + r.pass_hr + '</a>';
                        },
                        'class' : 'passage',
                        'type'  : 'num',
                    },
                    {
                        'data'  : 'lesart1',
                        'class' : 'lesart lesart1',
                    },
                    {
                        'data'  : 'labez_clique1',
                        'class' : 'ms ms1',
                    },
                    {
                        'data'  : 'direction',
                        'class' : 'direction',
                    },
                    {
                        'data'  : 'labez_clique2',
                        'class' : 'ms ms2',
                    },
                    {
                        'data'  : 'lesart2',
                        'class' : 'lesart lesart2',
                    },
                ],
                'order'      : [[0, 'asc']],
                'createdRow' : function (r, d /* , index */) {
                    let $row = $ (r);
                    $row.toggleClass ('newer', d.newer);
                    $row.toggleClass ('older', d.older);
                },
            })
        );

        this.load_data ();
    },
};
</script>

<style lang="less">
@import "@{BS}/variables.less";
@import "@{BS}/mixins.less";

table.comparison-detail {
    text-align: left;
    border-width: 0;

    th,
    td {
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

    tbody {
        tr.older td.direction {
            background-color: #cfc;
        }

        tr.newer td.direction {
            background-color: #fcc;
        }
    }
}
</style>
