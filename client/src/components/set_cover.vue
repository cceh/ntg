<template>
  <div class="vm-set-cover want_hashchange" @hashchange="on_hashchange">

    <div class="container bs-docs-container">

      <div class="navigator">
        <form class="form-inline d-flex justify-content-between" @submit.prevent="submit">

          <div class="input-group">
            <div class="input-group-prepend">
              <span class="input-group-text">Witness:</span>
            </div>
            <input id="ms" v-model="ms" type="text" class="form-control"
                   title="Enter the Gregory-Aland-No. of the descendant witness."
                   aria-label="Descendant Witness" />
          </div>

          <div class="input-group input-group-selection">
            <div class="input-group-prepend">
              <span class="input-group-text">Pre-Select:</span>
            </div>
            <input id="pre" v-model="pre_select" type="text" class="form-control"
                   title="Enter a space-separated list of witnesses to pre-select into the set cover."
                   aria-label="Pre-Select" />
          </div>

          <button type="submit" data="Go" class="btn btn-primary"
                  title="Find the set cover.">Go</button>

        </form>
      </div>

      <card class="card-set-cover">
        <card-caption :slidable="false">
          {{ caption }}
        </card-caption>

        <div class="card-header">
          <toolbar :toolbar="toolbar">
            <button-group v-model="toolbar.include" type="checkbox" :options="options.include" />
          </toolbar>
        </div>

        <table class="table table-bordered table-sm table-hover table-set-cover" cellspacing="0">
          <thead>
            <tr>
              <th class="n"
                  title="Index No.">No.</th>

              <th class="hs"
                  title="The ancestor">Ancestor</th>

              <th class="equals"
                  title="Number of variants explained by agreement with the ancestor.">Equal</th>

              <th class="post"
                  title="Number of variants not explained by agreement but by posteriority.">Post</th>

              <th class="unknown"
                  title="Cases of unknown source variant.">Unknown</th>

              <th class="open"
                  title="Number of variants not explained by any ancestor.">Total Open</th>

              <th class="explained"
                  title="Number of variants explained by one of the ancestors.">Total Explained</th>

              <th class="d-print-none"
                  title="Open Optimal Substemma view"></th>
            </tr>
          </thead>
          <tbody>
            <template v-for="r in cover">
              <tr :key="r.ms_id" :data-ms-id="r.ms_id">
                <td class="n">{{ r.n }}</td>
                <td class="hs">{{ r.hs }}</td>
                <td class="equal">{{ r.equal }}</td>
                <td class="post">{{ r.post }}</td>
                <td class="unknown">{{ r.unknown }}</td>
                <td class="open">{{ r.open }}</td>
                <td class="explained">{{ r.explained }}</td>

                <td class="opt-stemma d-print-none"
                    :title="`Find Optimal Substemma for ${ms} using ${r.cumsum_hs}`"
                    @click="on_opt_stemma (r.cumsum_hs)">
                  <span class="fas fa-sitemap"></span>
                </td>

              </tr>
            </template>
          </tbody>
        </table>
      </card>

    </div>
  </div>
</template>

<script>
/**
 * Find the minimum set cover of ancestors for any descendant.
 *
 * See: Presentation 485ff
 *
 * @component client/set_cover
 * @author Marcello Perathoner
 */

import tools       from 'tools';
import { options } from 'widgets/options';

import card         from 'widgets/card.vue';
import card_caption from 'widgets/card_caption.vue';
import toolbar      from 'widgets/toolbar.vue';
import button_group from 'widgets/button_group.vue';

export default {
    data () {
        return {
            'ms'         : '',  // v-model
            'pre_select' : '',  // v-model
            'ms_object'  : {},
            'cover'      : [],
            'options'    : options,
            'toolbar'    : {
                'include' : [],
            },
        };
    },
    'components' : {
        'card'         : card,
        'card-caption' : card_caption,
        'toolbar'      : toolbar,
        'button-group' : button_group,
    },
    'computed' : {
        caption () {
            if (this.ms_object.hs) {
                const w = `${this.ms_object.hs} (${this.ms_object.open})`;
                this.$store.commit ('caption', `${w} - Minimum Set Cover`);
                return `Minimum Set Cover for Witness ${w}`;
            }
            return this.$route.meta.caption;
        },
    },
    'watch' : {
        'toolbar.include' : function () {
            this.on_hashchange ();
        },
    },
    'methods' : {
        submit () {
            tools.set_hash (this, ['ms', 'pre_select']);
        },
        on_hashchange () {
            const vm = this;

            const params   = tools.get_hash ();
            params.include = vm.toolbar.include;

            if (params.ms) {
                const requests = [
                    vm.get (`set-cover.json/${params.ms}?` + tools.param (params, ['pre_select', 'include'])),
                ];
                Promise.all (requests).then ((responses) => {
                    const data = responses[0].data.data;
                    vm.ms_object  = data.ms;
                    vm.ms         = data.ms.hs;
                    vm.pre_select = data.mss.map (d => d.hs).join (' ');

                    let cumsum = [];
                    vm.cover = data.cover.map (function (item) {
                        cumsum.push (item.hs);
                        item.cumsum_hs = cumsum.join (' ');
                        return item;
                    });
                });
            } else {
                // reset data
                vm.ms         = '';
                vm.pre_select = '';
                vm.ms_object  = {};
                vm.cover      = [];
            }
        },
        /* open the optimal substemma view with this combination preloaded */
        on_opt_stemma (cumsum) {
            const vm = this;
            window.open (
                vm.$router.resolve ({
                    'name' : 'opt_stemma',
                    'hash' : '#' + tools.param ({
                        'ms'        : vm.ms,
                        'selection' : cumsum,
                    }),
                }).href, '_blank'
            ).focus ();
        },
    },
    mounted () {
        this.on_hashchange ();
    },
};
</script>

<style lang="scss">
/* set_cover.vue */
@import "bootstrap-custom";

div.vm-set-cover {
    div.navigator {
        margin-bottom: $spacer;

        form.form-inline {
            /* make button same height as inputs */
            align-items: stretch;
        }

        .input-group {
            margin-right: ($spacer * 0.5);
        }

        input[type=text] {
            width: 6em;
        }

        #pre {
            width: 12em;
        }

        @media print {
            display: none;
        }

        .input-group-selection {
            flex-grow: 1;
        }
    }

    td.opt-stemma {
        width: 1%;

        span.fas {
            color: var(--green);
        }
    }
}
</style>
