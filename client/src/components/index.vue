<template>
  <div>
    <router-link class="biglink" to="coherence">Coherence and Textual Flow</router-link>
    <router-link class="biglink" to="comparison">Comparison of Witnesses</router-link>

    <a class="biglink" href="/pdf/GenQ4_Guide.pdf" target="_blank">Short Guide (PDF)</a>

    <p>
      This new interface of the Genealogical Queries suite of tools is the
      result of a collaboration of the AWK project “Novum Testamentum Graecum -
      Editio Critica Maior” and the Cologne Center for eHumanities. –
      Programming: Marcello Perathoner.
    </p>

    <div class="logos">
      <a href="http://egora.uni-muenster.de/intf/index_en.shtml"><img src="/images/intf-logo.png" /></a>
      <a href="http://www.awk.nrw.de"><img src="/images/awk-logo-00.png" /></a>
      <a href="http://cceh.uni-koeln.de"><img src="/images/cceh-logo.png" /></a>
    </div>

    <div class="gdpr">
      <a href="https://www.portal.uni-koeln.de/datenschutz1.html">Data Privacy Statement</a>
    </div>
  </div>
</template>

<script>

/* import these images for the side-effect only: make webpack pack these files. */
import '../images/intf-logo.png';
import '../images/awk-logo-00.png';
import '../images/cceh-logo.png';

export default {
    'data' : function () {
        return {
            'caption' : 'Genealogical Queries',
        };
    },
    mounted () {
        this.$store.commit ('caption', this.caption);
    },
};
</script>

<style lang="less" scoped>
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
</style>
