import 'vuetify/styles'
import 'roboto-fontface/css/roboto/roboto-fontface.css'

import {
  mdiAccountCircleOutline,
  mdiAccountGroupOutline,
  mdiApi,
  mdiBlockHelper,
  mdiCalendarClock,
  mdiChartTimelineVariant,
  mdiCheckCircleOutline,
  mdiClose,
  mdiCogOutline,
  mdiContentCopy,
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
import { darkThemeColors, lightThemeColors } from './themePalette'

export default createVuetify({
  theme: {
    defaultTheme: 'ideasLight',
    themes: {
      ideasLight: {
        dark: false,
        colors: lightThemeColors,
      },
      ideasDark: {
        dark: true,
        colors: darkThemeColors,
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
      block: mdiBlockHelper,
      calendar: mdiCalendarClock,
      check: mdiCheckCircleOutline,
      close: mdiClose,
      copy: mdiContentCopy,
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
    VBtn: {},
    VCard: {},
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
