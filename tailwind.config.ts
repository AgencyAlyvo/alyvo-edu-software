import type { Config } from 'tailwindcss'

/** @type {import('tailwindcss').Config} */
export default <Partial<Config>>{
  content: ['./src-nuxt/**/*.vue'],
  theme: {
    extend: {},
  },
  plugins: [],
}
