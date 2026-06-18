import vue from '@vitejs/plugin-vue'
import { fileURLToPath, URL } from 'node:url'
import { defineConfig } from 'vite'
import vuetify from 'vite-plugin-vuetify'

function normalizeGanttCssGlobalSelectors() {
  return {
    name: 'normalize-gantt-css-global-selectors',
    enforce: 'pre' as const,
    transform(code: string, id: string) {
      if (!id.includes('jordium-gantt-vue3') || !code.includes(':global(')) {
        return null
      }

      return {
        code: code.replace(/:global\(([^)]+)\)/g, '$1'),
        map: null,
      }
    },
  }
}

export default defineConfig({
  plugins: [normalizeGanttCssGlobalSelectors(), vue(), vuetify({ autoImport: true })],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },
  server: {
    port: 5173,
    proxy: {
      '/api/v1': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api\/v1/, ''),
      },
    },
  },
  build: {
    chunkSizeWarningLimit: 1200,
  },
})
