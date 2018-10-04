<template>
  <div class="leitzeile_vm" v-html="leitzeile" />
</template>

<script>
/**
 * This component displays the leitzeile.
 *
 * @component leitzeile
 * @author Marcello Perathoner
 */

import _ from 'lodash';

function compute_leitzeile_html (leitzeile_json, current_pass_id) {
    let accumulator = [[]];
    let last_pass_id = null;
    let i = 0;

    // group by pass_id
    for (const item of leitzeile_json) {
        if (item.pass_id !== last_pass_id) {
            i += 1;
            accumulator[i] = [];
            last_pass_id = item.pass_id;
        }
        accumulator[i].push (item);
    }

    const leitzeile = [];
    for (const items of accumulator) {
        if (items.length !== 0) {
            const pass_id = items[0].pass_id;
            const classes = [];
            let tmp = _.map (items, 'lemma').join (' ');
            if ((items[0].begadr % 2) === 1) {
                classes.push ('leitzeile-inserted');
                tmp = '';
            } else if (items[0].replaced) {
                classes.push ('leitzeile-replaced');
            } else {
                classes.push ('leitzeile-deleted');
            }
            classes.push ((items.length > 1) ? 'leitzeile-many' : 'leitzeile-one');
            if (items[0].spanned) {
                classes.push ('leitzeile-spanned');
            }
            if (pass_id === current_pass_id) {
                classes.push ('leitzeile-current');
            }
            const class_ = (classes.length) ? ` class="${classes.join (' ')}"` : '';

            if (pass_id) {
                leitzeile.push (`<a${class_} href="#pass_id=${pass_id}">${tmp}</a>`);
            } else {
                leitzeile.push (`<span>${tmp}</span>`);
            }
        }
    }
    return leitzeile.join (' ');
}

export default {
    'data' : function () {
        return {
        };
    },
    'computed' : {
        leitzeile () {
            return compute_leitzeile_html (this.$store.state.leitzeile, this.$store.state.passage.pass_id);
        },
    },
};
</script>

<style lang="scss">
/* leitzeile.vue */
@import "bootstrap-custom";

.leitzeile_vm {
    @media print {
        display: none;
    }

    margin-bottom: 20px;
    font-size: larger;

    .leitzeile-current {
        color: #d62728;
        pointer-events: none;
    }

    .leitzeile-spanned {
        display: none;
        border-bottom: 1px dotted grey;
    }

    .leitzeile-inserted {
        &::before {
            content: '⸆'; /* 2e06 */
        }
    }

    .xxx {
        .leitzeile-replaced.leitzeile-one {
            &::before {
                content: '⸀'; /* 2e00 */
            }
        }

        .leitzeile-replaced.leitzeile-many {
            &::before {
                content: '⸂';
            }

            &::after {
                content: '⸃';
            }
        }

        .leitzeile-deleted.leitzeile-one {
            &::before {
                content: '⸋'; /* 2e0b */
            }
        }

        .leitzeile-deleted.leitzeile-many {
            &::before {
                content: '⸍'; /* 2e0d */
            }

            &::after {
                content: '⸌'; /* 2e0c */
            }
        }
    }
}
</style>
