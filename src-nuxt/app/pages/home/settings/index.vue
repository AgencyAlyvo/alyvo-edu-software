<template>
  <main class="grid gap-6">
    <header>
      <p class="text-xs font-semibold tracking-[0.2em] text-[#9a65d5] uppercase">LINKEDIN</p>
      <h1 class="mt-2 text-2xl font-semibold text-white">Paramètres LinkedIn</h1>
    </header>

    <SettingsLinkedinPanel />
  </main>
</template>

<script lang="ts" setup>
import { useUserSettingsStore } from '#src-nuxt/app/stores/userSettings.store'

definePageMeta({ layout: 'home' })

const store: ReturnType<typeof useUserSettingsStore> = useUserSettingsStore()

onMounted((): void => {
  void store.fetch()
})
</script>
