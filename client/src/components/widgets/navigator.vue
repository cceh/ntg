<template>
  <form class="vm-navigator form-inline" autocomplete="off" @submit.prevent="on_submit">

    <div class="btn-group btn-group-sm mr-2">
      <button type="button" data="-1" class="btn btn-primary"
              aria-label="Previous Passage" title="Previous Passage" @click="on_submit">
        <span class="fas fa-chevron-left" />
      </button>
    </div>

    <div class="input-group input-group-sm">
      <div class="input-group-prepend">
        <span class="input-group-text">Nav:</span>
      </div>

      <autocomplete v-model="ac.siglum" name="siglum" :more_params="ac" aria-label="Book" title="Book"
                    @input="ac.chapter = ''; ac.verse = ''; ac.word = ''" />
      <autocomplete v-model="ac.chapter" name="chapter" :more_params="ac" aria-label="Chapter" title="Chapter"
                    @input="ac.verse = ''; ac.word = ''" />

      <div class="input-group-prepend input-group-append">
        <span class="input-group-text">:</span>
      </div>

      <autocomplete v-model="ac.verse" name="verse" :more_params="ac" aria-label="Verse" title="Verse"
                    @input="ac.word = ''" />

      <div class="input-group-prepend input-group-append">
        <span class="input-group-text">/</span>
      </div>

      <autocomplete v-model="ac.word" name="word" :more_params="ac" aria-label="Word" title="Word"
                    @input="on_submit" />

      <div class="input-group-btn input-group-append">
        <button type="submit" data="Go" class="btn btn-primary"
                aria-label="Go" title="Go">
          <span class="fas fa-check" />
        </button>
      </div>
    </div>

    <div class="btn-group btn-group-sm ml-2">
      <button type="button" data="1" class="btn btn-primary"
              aria-label="Next Passage" title="Next Passage" @click="on_submit">
        <span class="fas fa-chevron-right" />
      </button>
    </div>

    <input :value="value" name="pass_id" type="hidden" />
  </form>
</template>

<script>
/**
 * This module implements the tape-recorder-controls navigator.
 *
 * @component client/widgets/navigator
 * @author Marcello Perathoner
 */

import autocomplete from 'widgets/autocomplete.vue';

export default {
    'props' : {
        'value' : { // the pass_id, set by v-model
            'type'     : Number,
            'required' : true,
        },
    },
    'components' : {
        'autocomplete' : autocomplete,
    },
    'data' : function () {
        return {
            'ac' : {
                'siglum'  : '',
                'chapter' : '',
                'verse'   : '',
                'word'    : '',
            },
        };
    },
    'watch' : {
        value (new_pass_id) { this.load (new_pass_id); },
    },
    'methods' : {
        /**
         * Answer the user input on the navigator buttons.
         *
         * @param {Object} event - The event
         */
        on_submit (event) {
            const vm = this;
            const target = event.currentTarget;
            const params = {
                'button' : (target && target.getAttribute ('data')) || 'Go',
                ... vm.ac,
            };
            // transform user input into pass_id
            vm.get ('passage.json/' + vm.value, { 'params' : params }).then ((response) => {
                const passage = response.data.data;
                vm.$emit ('input', parseInt (passage.pass_id, 10));  // makes it work with v-model, sets value
            });
        },
        load (new_pass_id) {
            const vm = this;
            const ac = vm.ac;
            if (new_pass_id > 0) {
                vm.get ('passage.json/' + new_pass_id).then ((response) => {
                    const passage = response.data.data;
                    ac.siglum  = passage.siglum.toString ();
                    ac.chapter = passage.chapter.toString ();
                    ac.verse   = passage.verse.toString ();
                    ac.word    = passage.word.toString ();
                });
            } else {
                ac.siglum  = '';
                ac.chapter = '';
                ac.verse   = '';
                ac.word    = '';
            }
        },
    },
    mounted () {
        this.load (this.value);
    },
};
</script>

<style lang="scss">
/* navigator.vue */

.vm-navigator {
    @media print {
        display: none;
    }

    input.form-control {
        text-align: right;
        width: 3.5em;
        border-radius: 0;

        &[name=siglum] {
            text-align: left;
            border-right-width: 0;
            width: 4.5em;
        }

        &[name=word] {
            width: 6.5em;
        }
    }
}

</style>
