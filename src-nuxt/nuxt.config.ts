import { fileURLToPath } from 'url'
import tailwindcss from '@tailwindcss/vite'

// https://nuxt.com/docs/api/configuration/nuxt-config
export default defineNuxtConfig({
  app: {
    head: {
      meta: [{ name: 'viewport', content: 'width=device-width, initial-scale=1' }, { charset: 'utf-8' }],
      script: [],
      link: [],
      style: [],
      noscript: [],
    },
  },
  srcDir: 'app',
  serverDir: 'server',
  dir: {
    public: 'public',
    modules: 'modules',
    shared: 'shared',
  },
  modulesDir: ['../node_modules'],
  ssr: false, // Obligatoire pour Tauri.
  alias: {
    '#src-nuxt': fileURLToPath(new URL('.', import.meta.url)),
    '#src-core': fileURLToPath(new URL('../src-core', import.meta.url)),
  },
  css: ['~/assets/css/tailwind.css', '~/assets/css/main.scss'],
  devtools: { enabled: true },
  telemetry: false,
  components: {
    dirs: [{ path: '~/components', pathPrefix: false }],
  },
  runtimeConfig: {
    apiSecret: '', // can be overridden by NUXT_API_SECRET environment variable
    public: {
      appEnv: process.env.NUXT_PUBLIC_NODE_ENV,
      apiBaseUrl: process.env.NUXT_PUBLIC_BASE_URL_API,
      appIdentifier: process.env.NUXT_PUBLIC_APP_IDENTIFIER,
    },
  },
  typescript: {
    strict: true,
    typeCheck: true,
    tsConfig: {
      compilerOptions: {
        skipLibCheck: true,
        noEmit: true,
      },
    },
  },
  vite: {
    plugins: [tailwindcss()],
  },
  modules: ['@pinia/nuxt', '@nuxtjs/google-fonts', '@nuxt/ui'],
  pinia: {
    storesDirs: ['~/stores/**'],
  },
  googleFonts: {
    families: {
      Manrope: [400, 500, 600, 700, 800],
    },
  },
})
