<template>
  <main class="grid gap-6">
    <header class="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
      <div>
        <p class="text-xs font-semibold tracking-[0.2em] text-[#9a65d5] uppercase">BUSINESS LOCAUX</p>
        <h1 class="mt-2 text-2xl font-semibold text-white">Tableau de bord business locaux</h1>
      </div>

      <DashboardDateRangePicker v-model="dateRange" :loading="statsStore.isLocalBusinessLoading" />
    </header>

    <DashboardLocalBusinessStatsPanel
      :stats="statsStore.localBusinessStats"
      :period-label="dateRange.label"
      :loading="statsStore.isLocalBusinessLoading"
    />
  </main>
</template>

<script lang="ts" setup>
import type { Ref } from 'vue'
import { useStatsStore } from '#src-nuxt/app/stores/stats.store'
import type { DashboardDateRange } from '#src-core/types/payload/stats.types'
import { createDefaultDashboardDateRange, dashboardDateRangeToQuery } from '#src-nuxt/app/utils/dashboardDateRange'

definePageMeta({ layout: 'home' })

const statsStore: ReturnType<typeof useStatsStore> = useStatsStore()
const dateRange: Ref<DashboardDateRange> = ref(createDefaultDashboardDateRange())

/**
 * Charge les donnees de la page pour la periode selectionnee.
 * @returns {Promise<void>}
 */
const loadPage: () => Promise<void> = async (): Promise<void> => {
  await statsStore.fetchLocalBusiness(dashboardDateRangeToQuery(dateRange.value))
}

watch(dateRange, (): void => {
  void loadPage()
})

onMounted((): void => {
  void loadPage()
})
</script>
