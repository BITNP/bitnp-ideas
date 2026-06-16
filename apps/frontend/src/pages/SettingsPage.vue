<template>
  <div class="page-shell">
    <div class="toolbar-row mb-4">
      <div>
        <h1 class="text-h5 mb-1">Settings</h1>
        <p class="text-body-2 text-medium-emphasis mb-0">Runtime boundaries for SSO, audit, and idea-only automation.</p>
      </div>
    </div>

    <v-row>
      <v-col cols="12" md="6">
        <v-card border flat>
          <v-card-title>OIDC</v-card-title>
          <v-card-text>
            <v-text-field label="Issuer URL" model-value="https://accounts.example.com/realms/bitnp" />
            <v-text-field label="Client ID" model-value="bitnp-ideas" />
          </v-card-text>
        </v-card>
      </v-col>
      <v-col cols="12" md="6">
        <v-card border flat>
          <v-card-title>API Key Boundary</v-card-title>
          <v-card-text>
            <v-checkbox :model-value="true" label="Allow ideas:read" hide-details />
            <v-checkbox :model-value="true" label="Allow ideas:write" hide-details />
            <v-checkbox :model-value="false" disabled label="Allow projects/tasks" hide-details />
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>
  </div>
</template>
