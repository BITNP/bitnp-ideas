<template>
  <div class="page-shell">
    <div class="toolbar-row mb-4">
      <div>
        <h1 class="text-h5 mb-1">API Keys</h1>
        <p class="text-body-2 text-medium-emphasis mb-0">External automation is limited to idea intake scopes.</p>
      </div>
      <v-btn color="primary" prepend-icon="$key">Create key</v-btn>
    </div>

    <v-card border flat>
      <v-table>
        <thead>
          <tr>
            <th>Name</th>
            <th>Key ID</th>
            <th>Scopes</th>
            <th>Entities</th>
            <th>Status</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td>AI intake workflow</td>
            <td><code>ideas_demo_01</code></td>
            <td>ideas:read, ideas:write</td>
            <td><v-chip size="small" color="primary" variant="tonal">idea</v-chip></td>
            <td><v-chip size="small" color="success" variant="tonal">active</v-chip></td>
          </tr>
        </tbody>
      </v-table>
    </v-card>
  </div>
</template>

