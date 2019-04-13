<script>
import $ from 'jquery';

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
            const rows = _.sortBy (vm.rows, vm.sorted_by.split (' '));
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
            }

            &.desc[data-sort-by]::after {
                content: "\f0dd";
                color: var(--red);
            }
        }
    }
}

</style>
