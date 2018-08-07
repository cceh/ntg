<template>
  <table class="comparison table table-bordered table-condensed table-hover" cellspacing="0">
    <caption>
      <span class="caption">{{ caption }}</span>
      <div ref="toolbar" class="btn-toolbar toolbar toolbar-comparison" role="toolbar" />
    </caption>
    <thead>
      <tr>
        <th class="details-control" />

        <th class="range exportable">Chapter</th>
        <th class="direction exportable"
            title="Genealogical direction, potential ancestors indicated by “>”">Dir</th>
        <th class="rank exportable"
            title="Ancestral rank according to the degree of agreement (Perc)">NR</th>

        <th class="perc exportable"
            title="Percentaged agreement of W1 and W2 at the variant passages attested by both (Pass)">Perc</th>
        <th class="eq exportable"
            title="Number of agreements of W1 and W2 at the variant passages attested by both (Pass)">Eq</th>
        <th class="common exportable"
            title="Total number of passages where W1 and W2 are both extant">Pass</th>

        <th class="older exportable"
            title="Number of variants in W2 that are prior to those in W1">W1&lt;W2</th>
        <th class="newer exportable"
            title="Number of variants in W1 that are prior to those in W2">W1&gt;W2</th>
        <th class="uncl exportable"
            title="Number of variants where no decision has been made about priority">Uncl</th>
        <th class="norel exportable"
            title="Number of passages where the respective variants are unrelated">NoRel</th>
      </tr>
    </thead>
    <tbody />
  </table>
</template>

<script>
/**
 * Comparison of 2 witnesses.  This module shows a table with a global
 * comparison of two witnesses: in how many passages do they differ, how many
 * are older / younger? There is also a drill-down table for each range with
 * more detail about the differing passages.
 *
 * @component comparison_table
 * @author Marcello Perathoner
 */

import $ from 'jquery';
import Vue from 'vue';
import csv_parse from 'csv-parse/lib/sync';

import 'datatables.net';
import 'datatables.net-bs';
import 'datatables.net-buttons';
import 'datatables.net-buttons-bs';
// import 'datatables.net-buttons-html5';
import 'datatables.net-buttons/js/buttons.print.js';

import 'bootstrap.css';
import 'datatables.net-bs.css';
import 'datatables.net-buttons-bs.css';

import comparison_details_table from 'comparison_details_table.vue';

Vue.component ('comparison-details-table', comparison_details_table);

export const default_table_options = {
    'autoWidth'    : true,
    'deferRender'  : true,
    'info'         : false,
    'lengthChange' : false,
    'ordering'     : true,
    'paging'       : false,
    'scrollX'      : false,
    'searching'    : false,
};

const default_buttons = [
/*
    {
        'extend'        : 'copy',
        'className'     : 'btn btn-primary btn-comparison-copy',
        'exportOptions' : { 'columns' : '.exportable' },
    },
    {
        'extend'        : 'csv',
        'className'     : 'btn btn-primary btn-comparison-csv',
        'exportOptions' : { 'columns' : '.exportable' },
    },
*/
    {
        'extend'        : 'print',
        'className'     : 'btn btn-primary btn-comparison-print',
        'exportOptions' : { 'columns' : '.exportable' },
        'autoPrint'     : false,
    },
];

/**
 * Return a direction marker, <, =, or >.
 *
 * @function dir
 *
 * @param {object} row - Data row
 *
 * @return Direction marker.
 */

function dir (r) {
    if (+r.older > +r.newer) {
        return '>';
    }
    if (+r.older < +r.newer) {
        return '<';
    }
    return '=';
}

/**
 * Row conversion function.  Convert numeric values to numeric types and add
 * calculated fields.
 *
 * @function main_row_conversion
 *
 * @return The converted row
 */

function row_conversion (d) {
    return {
        'rg_id'     : +d.rg_id,
        'range'     : d.range,
        'length1'   : +d.length1,
        'length2'   : +d.length2,
        'common'    : +d.common,
        'equal'     : +d.equal,
        'older'     : +d.older,
        'newer'     : +d.newer,
        'norel'     : +d.norel,
        'unclear'   : +d.unclear,
        'affinity'  : Math.round (d.affinity * 100000) / 1000,
        'rank'      : +d.rank,
        'direction' : dir (d),
    };
}

/**
 * Add buttons to a data_table.
 *
 * Must do this as separate function because otherwise dynamic creation of
 * details table components will not show buttons.
 *
 * @function buttons
 */

function buttons ($table, $toolbar) {
    let data_table = $table.DataTable (); // eslint-disable-line new-cap

    /* eslint-disable no-new */
    new $.fn.dataTable.Buttons (data_table, {
        'buttons' : default_buttons,
        'dom'     : {
            'container' : {
                'className' : 'btn-group btn-group-xs',
            },
        },
    });
    data_table.buttons ().container ().appendTo ($toolbar);
}

export default {
    'props' : ['ms1', 'ms2'],
    data () {
        return {
        };
    },
    'computed' : {
        'caption' : function () {
            return this.ms1 ? `Comparison of ${this.ms1.hs} and ${this.ms2.hs}` : 'Comparison';
        },
        'ms1ms2' : function () {
            return this.ms1 ? this.ms1.ms_id + '-' + this.ms2.ms_id : '';
        },
    },
    'watch' : {
        'ms1ms2' : function () {
            this.load_data ();
        },
    },
    mounted () {
        /**
         * Initialize the table structure.  This has to be done only once.  On
         * navigation we only replace the table data.
         */

        const $table = $ (this.$el);

        $table.DataTable ( // eslint-disable-line new-cap
            $.extend ({}, default_table_options, {
                'columns' : [
                    {
                        'class'          : 'details-control',
                        'orderable'      : false,
                        'data'           : null,
                        'defaultContent' : '',
                    },

                    {
                        'data' : function (r, type /* , val, meta */) {
                            if (type === 'sort') {
                                return r.rg_id;
                            }
                            return r.range;
                        },
                        'class' : 'range',
                        'type'  : 'num',
                    },
                    {
                        'data'  : 'direction',
                        'class' : 'direction',
                    },
                    {
                        'data'  : 'rank',
                        'class' : 'equal',
                    },

                    {
                        'data'  : 'affinity',
                        'class' : 'equal',
                    },
                    {
                        'data'  : 'equal',
                        'class' : 'equal',
                    },
                    {
                        'data'  : 'common',
                        'class' : 'common',
                    },

                    {
                        'data'  : 'newer',
                        'class' : 'newer',
                    },
                    {
                        'data'  : 'older',
                        'class' : 'older',
                    },
                    {
                        'data'  : 'unclear',
                        'class' : 'unclear',
                    },
                    {
                        'data'  : 'norel',
                        'class' : 'norel',
                    },
                ],
                'order'      : [[1, 'asc']],
                'createdRow' : function (row, data, dummy_index) {
                    let $row = $ (row);
                    $row.attr ('data-range', data.range);
                    $row.toggleClass ('older', data.older > data.newer);
                    $row.toggleClass ('newer', data.older < data.newer);
                },
            })
        );

        buttons ($table, this.$refs.toolbar);

        $table.find ('tbody').on ('click', 'td.details-control', this.toggle_details_table);
    },
    'methods' : {
        load_data () {
            // reload table
            let url = 'comparison-summary.csv?' + $.param ({
                'ms1' : 'id' + this.ms1.ms_id,
                'ms2' : 'id' + this.ms2.ms_id,
            });
            let vm = this;
            vm.get (url).then ((response) => {
                const rows = csv_parse (response.data, { 'columns' : true });
                const data_table = $ (vm.$el).DataTable (); // eslint-disable-line new-cap
                data_table.clear ().rows.add (rows.map (row_conversion)).draw ();
            });
        },

        /**
         * Opens a table containing a detailed view of one range.
         *
         * @function toggle_details_table
         */

        toggle_details_table (event) {
            let $tr    = $ (event.currentTarget).closest ('tr');
            let $table = $ (this.$el);
            let row    = $table.DataTable ().row ($tr); // eslint-disable-line new-cap

            if (row.child.isShown ()) {
                $ ('div.slider', row.child ()).slideUp (function () {
                    row.child.hide ();
                    $tr.removeClass ('shown');
                });
            } else {
                if ($tr.hasClass ('csv-loaded')) {
                    $tr.addClass ('shown');
                    row.child.show ();
                    $ ('div.slider', row.child ()).slideDown ();
                    return;
                }

                // Dynamically create the details table component and mount it
                // as off-DOM element.  Then attach it using row.child ().
                let Comp = this.$options.components['comparison-details-table'];
                let comp = new Comp ({
                    'propsData' : { 'ms1' : this.ms1, 'ms2' : this.ms2, 'range' : $tr.attr ('data-range') },
                    'parent'    : this,
                }).$mount ();

                row.child (comp.$el);
                row.child.show ();
                $tr.addClass ('shown');

                buttons ($ (comp.$refs.table), comp.$refs.toolbar);
            }
        },
    },
};
</script>

<style lang="less">
@import "@{BS}/variables.less";
@import "@{BS}/mixins.less";

table.dataTable {
    margin-top: 0 !important;
    margin-bottom: 0 !important;

    caption {
        font-weight: bold;
        padding: @table-condensed-cell-padding;
        border-bottom: 1px solid @table-border-color;
        color: inherit;

        div.toolbar {
            float: right;
        }
    }

    thead {
        background-color: @panel-default-heading-bg;

        tr th {
            &.sorting::after,
            &.sorting_asc::after,
            &.sorting_desc::after {
                position: absolute;
                bottom: 8px;
                right: 8px;
                display: block;
                padding-left: 8px;
                /* stylelint-disable-next-line font-family-no-missing-generic-family-keyword */
                font-family: 'Glyphicons Halflings';
                opacity: 1;
                cursor: pointer;
            }

            &.sorting::after {
                content: "\e114";
                color: green;
            }

            &.sorting_asc::after {
                content: "\e114";
                color: red;
            }

            &.sorting_desc::after {
                content: "\e113";
                color: red;
            }
        }
    }

    tbody {
        background-color: @panel-bg;

        td.sorting_1 {
            background: @panel-default-heading-bg;
        }
    }
}

table.comparison {
    margin-bottom: 0;
    border-width: 0;
    text-align: right;

    caption {
        padding: @panel-heading-padding;
    }

    /* stylelint-disable-next-line no-descending-specificity */
    th,
    td {
        &.ms {
            text-align: left;
        }

        &.direction {
            text-align: center;
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

    div.slider {
        background-color: @panel-default-heading-bg;
        display: none;
    }

    td.no-padding {
        padding: 0;
    }

    tr .details-control {
        text-align: center;
    }

    tr td.details-control::after {
        /* stylelint-disable-next-line font-family-no-missing-generic-family-keyword */
        font-family: 'Glyphicons Halflings';
        content: "\e081";
        color: green;
        cursor: pointer;
    }

    tr.shown td.details-control::after {
        content: "\e082";
        color: red;
    }

    tr[data-range="0"] td.details-control::after {
        content: "";
    }
}

body.dt-print-view table {
    font-size: 12px;
}
</style>
