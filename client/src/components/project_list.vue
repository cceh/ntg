<template>
  <div class="vm-project-list">
    <div class="container bs-docs-container">
      <table class="table table-bordered table-hover">
        <tbody>
          <tr>
            <th>Project</th><th>Editable</th><th>Description</th>
          </tr>
          <router-link v-for="i of $store.state.instances" :key="i.application_root"
                       tag="tr" :to="'/' + i.application_root">
            <td class="app_name">
              <a>{{ i.application_name }}</a>
            </td>
            <td class="can_edit">
              <span v-if="i.user_can_write" class="fas fa-pen-square" />
            </td>
            <td class="app_desc">
              {{ i.application_description }}
            </td>
          </router-link>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script>
/**
 * Project list component.  List the available projects.
 *
 * A project is one book of the NT and one phase.
 *
 * @component client/project_list
 * @author Marcello Perathoner
 */

export default {
    'data' : function () {
        return {
        };
    },
};

</script>

<style lang="scss">
/* project_list.vue */

div.vm-project-list {
    td.app_name {
        width: 20%;
    }

    td.can_edit {
        width: 1%;
    }

    span.fas {
        font-size: 150%;
        color: red;
    }

    table {
        margin-top: 2em;
    }
}

</style>
