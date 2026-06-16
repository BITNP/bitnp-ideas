import { createPinia } from 'pinia'
import { createApp } from 'vue'
import 'jordium-gantt-vue3/dist/assets/jordium-gantt-vue3.css'
import './styles/main.css'

import App from './App.vue'
import router from './router'
import { appThemeColor } from './plugins/themePalette'
import vuetify from './plugins/vuetify'

const themeColorMeta = document.querySelector('meta[name="theme-color"]')

if (themeColorMeta) {
  themeColorMeta.setAttribute('content', appThemeColor)
}

const app = createApp(App)
app.use(createPinia())
app.use(router)
app.use(vuetify)

await router.isReady()
app.mount('#app')
