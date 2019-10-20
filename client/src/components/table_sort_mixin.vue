<script>
/**
 * Mixin to make a table sortable
 *
 * To use:
 *
 * put a class 'table-sortable' on the table
 * put an attribute 'data-sort-by' on the <th>s of the columns you want made sortable
 */

import { reverse, sortBy } from 'lodash';

export default {
    data () {
        return {
            'sorted_by'   : '',
            'sorted_desc' : false,
        };
    },
    'watch' : {
        'sorted_by'   : function () { this.sort (); },
        'sorted_desc' : function () { this.sort (); },
    },
    'methods' : {
        on_sort (event) {
            const th = event.target;
            const sort_by = th.getAttribute ('data-sort-by');

            if (this.sorted_by === sort_by) {
                this.sorted_desc = !this.sorted_desc;
            } else {
                this.sorted_desc = false;
                this.sorted_by = sort_by;
            }
        },
        sort () {
            const vm = this;
            const rows = sortBy (vm.rows, vm.sorted_by.split (' '));
            if (vm.sorted_desc) {
                reverse (rows);
            }
            vm.rows = rows;
            vm.$el.querySelectorAll ('th[data-sort-by]').forEach (function (th) {
                const sort_by = th.getAttribute ('data-sort-by');
                const cl = th.classList;
                cl.remove ('asc');
                cl.remove ('desc');
                if (sort_by === vm.sorted_by) {
                    cl.add (vm.sorted_desc ? 'desc' : 'asc');
                }
            });
        },
    },
};

</script>

<style lang="scss">
/* comparison_table.vue */
@import "bootstrap-custom";

table.table-sortable {
    thead {
        tr th {
            position: relative;

            &[data-sort-by] {
                cursor: pointer;
            }

            &[data-sort-by]::after {
                position: absolute;
                top: ($spacer * 0.25);
                left: ($spacer * 0.25);
                display: block;
                /* stylelint-disable-next-line font-family-no-missing-generic-family-keyword */
                font-family: 'Font Awesome 5 Free';
                font-weight: 900;
                content: "\f0dc";
                color: var(--green);
                opacity: 1;

                @media print {
                    display: none;
                }
            }

            &.asc[data-sort-by]::after {
                content: "\f0de";
                color: var(--red);

                @media print {
                    display: unset;
                    color: var(--black);
                }
            }

            &.desc[data-sort-by]::after {
                content: "\f0dd";
                color: var(--red);

                @media print {
                    display: unset;
                    color: var(--black);
                }
            }
        }
    }
}

</style>
