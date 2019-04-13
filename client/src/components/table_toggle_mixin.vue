<script>
import $ from 'jquery';

export default {
    data () {
        return {
        };
    },
    'methods' : {
        /**
         * Opens a table containing a detailed view of one range.
         *
         * @function toggle_details_table
         */
        toggle_details_table (row, event) {
            if (row.child) {
                const $child_row = $ (event.target).closest ('tr').next ();
                $child_row.find ('div.slider').slideUp (() => { row.child = false; });
            } else {
                row.child = true;
            }
        },
    },
};

</script>

<style lang="scss">
/* comparison_table.vue */
@import "bootstrap-custom";

table.table-with-details {
    tr.child {
        padding: 0;

        &:hover {
            background-color: $card-bg;
        }

        > td {
            padding: 0;
        }
    }

    tr .details-control {
        text-align: center;
        width: $spacer;

        @media print {
            display: none;
        }
    }

    tr td.details-control::after {
        /* stylelint-disable-next-line font-family-no-missing-generic-family-keyword */
        font-family: 'Font Awesome 5 Free';
        font-weight: 900;
        content: "\f055";
        color: var(--green);
        cursor: pointer;
    }

    tr.shown td.details-control::after {
        content: "\f056";
        color: var(--red);
    }
}

</style>
