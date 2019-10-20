<template>
  <div class="vm-index">
    <div class="container bs-docs-container">
      <div v-if="$store.getters.can_read">
        <router-link class="biglink" :to="{ 'name' : 'coherence' }">Coherence and Textual Flow</router-link>
        <router-link class="biglink" :to="{ 'name' : 'comparison' }">Comparison of Witnesses</router-link>
        <router-link class="biglink" :to="{ 'name' : 'find_relatives' }">Find Relatives</router-link>
        <div v-if="$store.getters.can_write">
          <router-link class="biglink" :to="{ 'name' : 'notes_list' }">List of Notes</router-link>
          <router-link class="biglink" :to="{ 'name' : 'opt_stemma' }">Optimal Substemma</router-link>
          <router-link class="biglink" :to="{ 'name' : 'set_cover' }">Minimum Set Cover</router-link>
        </div>
      </div>

      <a class="biglink" href="/pdfs/GenQ4_Guide.pdf" target="_blank">Short Guide (PDF)</a>

      <p>
        This new interface of the Genealogical Queries suite of tools is the
        result of a collaboration of the AWK project “Novum Testamentum Graecum -
        Editio Critica Maior” and the Cologne Center for eHumanities. –
        Programming: Marcello Perathoner.
      </p>

      <div class="logos">
        <a href="http://egora.uni-muenster.de/intf/index_en.shtml"><img :src="intf_logo" /></a>
        <a href="http://www.awk.nrw.de"><img :src="awk_logo" /></a>
        <a href="http://cceh.uni-koeln.de"><img :src="cceh_logo" /></a>
      </div>

      <div class="gdpr">
        <a href="https://www.portal.uni-koeln.de/datenschutz1.html">Data Privacy Statement</a>
      </div>
    </div>

  </div>
</template>

<script>

/* import these images for the side-effect only: make webpack pack these files. */
import intf_logo from '../images/intf-logo.png';
import awk_logo from  '../images/awk-logo-00.png';
import cceh_logo from '../images/cceh-logo.png';

export default {
    'data' : function () {
        return {
            'intf_logo' : intf_logo,
            'awk_logo'  : awk_logo,
            'cceh_logo' : cceh_logo,
        };
    },
};
</script>

<style lang="scss">
/* index.vue */

div.vm-index {
    a.biglink {
        display: block;
        font-size: 150%;
        margin: 1em 0;
    }

    div.gdpr {
        margin-top: 1em;
    }

    div.logos {
        margin-top: 2em;

        img {
            height: 100px;
            padding-right: 1em;
        }
    }
}
</style>
