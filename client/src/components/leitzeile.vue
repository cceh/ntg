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

    const leitzeile = [];
    for (const item of leitzeile_json) {
        const classes = [];
        const pass_id = item.pass_ids[0];

        if ((item.begadr % 2) === 1) {
            classes.push ('leitzeile-inserted');
        }

        classes.push ((item.pass_ids.length > 1) ? 'leitzeile-many' : 'leitzeile-one');

        if (item.pass_ids.includes (current_pass_id)) {
            classes.push ('leitzeile-current');
        }

        const class_ = (classes.length) ? ` class="${classes.join (' ')}"` : '';

        leitzeile.push ('<table class="item"><tr><td>');
        if (pass_id) {
            leitzeile.push (`<a${class_} href="#pass_id=${pass_id}">${item.lemma}</a>`);
        } else {
            leitzeile.push (`<span${class_}>${item.lemma}</span>`);
        }
        leitzeile.push (`</td></tr><tr><td class="word">${item.begadr % 1000}</td></tr></table>`);
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

    table.item {
        display: inline-table;
        td.word {
            font-size: smaller;
            color: var(--gray);
        }
    }

    .leitzeile-current {
        color: #d62728;
        pointer-events: none;
    }

    .leitzeile-inserted {
        &::before {
            content: '⸆'; /* 2e06 */
        }
    }
}
</style>
