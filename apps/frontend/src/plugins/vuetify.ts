import 'vuetify/styles'
import 'roboto-fontface/css/roboto/roboto-fontface.css'

import {
  mdiAccountCircleOutline,
  mdiAccountGroupOutline,
  mdiApi,
  mdiCalendarClock,
  mdiChartTimelineVariant,
  mdiCheckCircleOutline,
  mdiClose,
  mdiCogOutline,
  mdiHomeAnalytics,
  mdiKeyVariant,
  mdiLightbulbOnOutline,
  mdiLinkVariant,
  mdiMagnify,
  mdiMoonWaningCrescent,
  mdiPlus,
  mdiSourceBranch,
  mdiTagMultipleOutline,
  mdiViewDashboardOutline,
  mdiWeatherSunny,
} from '@mdi/js'
import { createVuetify } from 'vuetify'
import { aliases, mdi } from 'vuetify/iconsets/mdi-svg'

export default createVuetify({
  theme: {
    defaultTheme: 'ideasLight',
    themes: {
      ideasLight: {
        dark: false,
        colors: {
          background: '#f6f7f9',
          surface: '#ffffff',
          primary: '#da751d',
          secondary: '#167c80',
          accent: '#c2410c',
          success: '#2e7d32',
          warning: '#b26a00',
          error: '#b3261e',
          info: '#4c6f91',
        },
      },
      ideasDark: {
        dark: true,
        colors: {
          background: '#14171a',
          surface: '#1f2429',
          primary: '#da751d',
          secondary: '#70c7c2',
          accent: '#ffb081',
        },
      },
    },
  },
  icons: {
    defaultSet: 'mdi',
    aliases: {
      ...aliases,
      account: mdiAccountCircleOutline,
      activity: mdiSourceBranch,
      api: mdiApi,
      calendar: mdiCalendarClock,
      check: mdiCheckCircleOutline,
      close: mdiClose,
      dashboard: mdiViewDashboardOutline,
      gantt: mdiChartTimelineVariant,
      home: mdiHomeAnalytics,
      idea: mdiLightbulbOnOutline,
      key: mdiKeyVariant,
      link: mdiLinkVariant,
      moon: mdiMoonWaningCrescent,
      plus: mdiPlus,
      search: mdiMagnify,
      settings: mdiCogOutline,
      sun: mdiWeatherSunny,
      tag: mdiTagMultipleOutline,
      users: mdiAccountGroupOutline,
    },
    sets: {
      mdi,
    },
  },
  defaults: {
    VBtn: {
      rounded: 'lg',
    },
    VCard: {
      rounded: 'lg',
    },
    VTextField: {
      density: 'compact',
      variant: 'outlined',
    },
    VSelect: {
      density: 'compact',
      variant: 'outlined',
    },
  },
})
