import { defineConfig } from 'vitest/config'
import { fileURLToPath } from 'node:url'

export default defineConfig({
  resolve: {
    alias: {
      '#src-core': fileURLToPath(new URL('./src-core', import.meta.url)),
      '#src-nuxt': fileURLToPath(new URL('./src-nuxt', import.meta.url)),
    },
  },
  test: {
    environment: 'node',
    globals: false,
    include: ['tests/unit/**/*.{test,spec}.ts'],
    coverage: {
      enabled: true,
      provider: 'v8',
      reporter: ['text', 'html'],
      reportsDirectory: './tests/unit/test-reports',
    },
  },
})
