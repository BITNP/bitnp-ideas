import baseConfig from '@bitnp-ideas/eslint-config'
import globals from 'globals'

export default [
  ...baseConfig,
  {
    files: ['src/**/*.vue'],
    languageOptions: {
      globals: {
        ...globals.browser,
      },
    },
    rules: {
      'vue/max-attributes-per-line': 'off',
      'vue/multi-word-component-names': 'off',
      'vue/singleline-html-element-content-newline': 'off',
    },
  },
]
