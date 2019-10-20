<template>
  <div class="vm-leitzeile" v-html="leitzeile" />
</template>

<script>
/**
 * This component displays the leitzeile.
 *
 * @component leitzeile
 * @author Marcello Perathoner
 */

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
    'props' : ['pass_id'],
    'data'  : function () {
        return {
            'leitzeile' : '',
        };
    },
    'watch' : {
        pass_id (new_pass_id) {
            this.load_leitzeile (new_pass_id);
        },
    },
    'methods' : {
        load_leitzeile (new_pass_id) {
            const vm = this;
            const requests = [
                vm.get ('leitzeile.json/' + new_pass_id),
            ];
            Promise.all (requests).then ((responses) => {
                vm.leitzeile = compute_leitzeile_html (responses[0].data.data, new_pass_id);
            });
        },
    },
};
</script>

<style lang="scss">
/* leitzeile.vue */
@import "bootstrap-custom";

.vm-leitzeile {
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
