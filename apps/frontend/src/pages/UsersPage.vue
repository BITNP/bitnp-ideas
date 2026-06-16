<template>
  <div class="page-shell">
    <div class="toolbar-row mb-4">
      <div>
        <h1 class="text-h5 mb-1">Users</h1>
        <p class="text-body-2 text-medium-emphasis mb-0">Global RBAC roles and account state synced from OIDC.</p>
      </div>
    </div>

    <v-card border flat>
      <v-table>
        <thead>
          <tr>
            <th>Name</th>
            <th>Email</th>
            <th>Role</th>
            <th>Active</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td>Alice Admin</td>
            <td>alice@bitnp.local</td>
            <td><v-chip size="small" color="primary" variant="tonal">superuser</v-chip></td>
            <td><v-switch :model-value="true" color="success" hide-details density="compact" /></td>
          </tr>
          <tr>
            <td>Devon Developer</td>
            <td>devon@bitnp.local</td>
            <td><v-chip size="small" color="secondary" variant="tonal">developer</v-chip></td>
            <td><v-switch :model-value="true" color="success" hide-details density="compact" /></td>
          </tr>
        </tbody>
      </v-table>
    </v-card>
  </div>
</template>
