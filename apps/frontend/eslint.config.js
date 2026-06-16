import baseConfig from '@bitnp-ideas/eslint-config'

export default [
  ...baseConfig,
  {
    files: ['src/**/*.vue'],
    rules: {
      'vue/max-attributes-per-line': 'off',
      'vue/multi-word-component-names': 'off',
      'vue/singleline-html-element-content-newline': 'off',
    },
  },
]
