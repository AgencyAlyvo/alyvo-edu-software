<template>
  <main class="grid gap-6">
    <header>
      <p class="text-xs font-semibold tracking-[0.2em] text-[#9a65d5] uppercase">LINKEDIN</p>
      <h1 class="mt-2 text-2xl font-semibold text-white">Objectif LinkedIn de la semaine</h1>
      <p class="mt-1 text-sm text-[#9ba3bd]">{{ weekLabel }}</p>
    </header>

    <WeeklyObjectiveBanner :objective="objectiveStore.current" />

    <section class="grid gap-4">
      <div class="flex flex-col gap-1 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <h2 class="text-base font-semibold text-white">Prospects ajoutes cette semaine</h2>
          <p class="mt-1 text-xs text-[#9ba3bd]">
            {{ weeklyProspectsCountLabel }}
          </p>
        </div>
      </div>

      <LinkedinProspectsTable
        v-if="prospectsStore.isLoading || prospectsStore.prospects.length > 0"
        :prospects="prospectsStore.prospects"
        :loading="prospectsStore.isLoading"
      />

      <div v-else class="rounded-lg border border-[#2f3d67] bg-[#0b1433]/70 py-16 text-center">
        <UIcon name="i-heroicons-user-group" class="mx-auto mb-3 h-10 w-10 text-[#2f3d67]" />
        <p class="text-sm font-medium text-[#8f9abc]">Aucun prospect ajoute cette semaine</p>
        <p class="mt-1 text-xs text-[#9ba3bd]">Les nouveaux prospects apparaitront ici des leur creation.</p>
      </div>

      <ServerPaginationNav
        :current-page="currentPage"
        :total-pages="totalPages"
        :total="prospectsStore.pagination?.total ?? 0"
        total-label="prospects sur la semaine"
        :visible-pages="visiblePages"
        :page-button-class="pageButtonClass"
        :active-page-button-class="activePageButtonClass"
        nav-aria-label="Pagination prospects LinkedIn de la semaine"
        @change="onPageChange"
      />
    </section>
  </main>
</template>

<script lang="ts" setup>
import type { ComputedRef } from 'vue'
import { useServerPagination } from '#src-nuxt/app/composables/useServerPagination'
import { useLinkedinProspectsStore } from '#src-nuxt/app/stores/linkedinProspects.store'
import { useWeeklyObjectiveStore } from '#src-nuxt/app/stores/weeklyObjective.store'
import { formatIsoWeekDisplayLabel } from '#src-nuxt/app/utils/isoWeekLabel'

definePageMeta({ layout: 'home' })

const objectiveStore: ReturnType<typeof useWeeklyObjectiveStore> = useWeeklyObjectiveStore()
const prospectsStore: ReturnType<typeof useLinkedinProspectsStore> = useLinkedinProspectsStore()

const weekLabel: ComputedRef<string> = computed((): string => formatIsoWeekDisplayLabel(objectiveStore.current?.week))

const weekIso: ComputedRef<string | undefined> = computed((): string | undefined => objectiveStore.current?.week)

const perPage: number = 50

/**
 * Charge une page des prospects de la semaine.
 * @param {number} page - Numero de page.
 * @returns {Promise<void>}
 */
const fetchWeeklyPage: (page: number) => Promise<void> = async (page: number): Promise<void> => {
  if (!weekIso.value) return
  await prospectsStore.fetchList({
    week: weekIso.value,
    page,
    perPage,
    sortBy: 'createdAt',
    sortDir: 'desc',
  })
}

/**
 * Retourne le nombre total de pages hebdomadaires.
 * @returns {number} Derniere page.
 */
const getWeeklyTotalPages: () => number = (): number => prospectsStore.pagination?.lastPage ?? 1

/**
 * Lit la page courante renvoyee par l'API.
 * @returns {number | undefined} Page courante.
 */
const getWeeklyCurrentPageFromMeta: () => number | undefined = (): number | undefined =>
  prospectsStore.pagination?.currentPage

const {
  currentPage,
  totalPages,
  visiblePages,
  pageButtonClass,
  activePageButtonClass,
  onPageChange,
  syncCurrentPageFromMeta,
} = useServerPagination({
  perPage,
  fetchPage: fetchWeeklyPage,
  getTotalPages: getWeeklyTotalPages,
  getCurrentPageFromMeta: getWeeklyCurrentPageFromMeta,
})

const weeklyProspectsCountLabel: ComputedRef<string> = computed((): string => {
  const count: number = prospectsStore.pagination?.total ?? 0
  if (count === 0) {
    return 'Aucun prospect pour le moment'
  }

  if (count === 1) {
    return '1 prospect identifie sur la semaine'
  }

  return `${count} prospects identifies sur la semaine`
})

/**
 * Charge la page semaine (objectif + liste paginee).
 * @returns {Promise<void>}
 */
const loadPage: () => Promise<void> = async (): Promise<void> => {
  await objectiveStore.fetchCurrent()
  if (!weekIso.value) return
  await prospectsStore.fetchList({
    week: weekIso.value,
    page: 1,
    perPage,
    sortBy: 'createdAt',
    sortDir: 'desc',
  })
  syncCurrentPageFromMeta()
}

onMounted((): void => {
  void loadPage()
})
</script>
