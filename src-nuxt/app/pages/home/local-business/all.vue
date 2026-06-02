<template>
  <main class="grid gap-6">
    <header class="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
      <div>
        <p class="text-xs font-semibold tracking-[0.2em] text-[#9a65d5] uppercase">BUSINESS LOCAUX</p>
        <h1 class="mt-2 text-2xl font-semibold text-white">Tous les business locaux</h1>
        <p class="mt-1 text-sm text-[#9ba3bd]">
          {{ store.pagination?.total ?? 0 }} business dans ta base (sources OpenStreetMap + ajouts manuels).
        </p>
      </div>
      <NuxtLink
        to="/home/local-business/import"
        class="inline-flex h-10 items-center gap-2 rounded-md bg-[linear-gradient(135deg,#102766_0%,#7446a6_100%)] px-4 font-semibold text-white shadow-[0_14px_30px_rgba(5,9,23,0.35)] transition hover:bg-[linear-gradient(135deg,#17337c_0%,#9a65d5_100%)]"
      >
        <UIcon name="i-heroicons-map-pin" class="h-4 w-4" />
        Importer depuis OSM
      </NuxtLink>
    </header>

    <LocalBusinessFilters @submit="fetchWithFilters" />
    <LocalBusinessTable :prospects="store.prospects" :loading="store.isLoading" />

    <ServerPaginationNav
      :current-page="currentPage"
      :total-pages="totalPages"
      :total="store.pagination?.total ?? 0"
      total-label="business au total"
      :visible-pages="visiblePages"
      :page-button-class="pageButtonClass"
      :active-page-button-class="activePageButtonClass"
      nav-aria-label="Pagination business locaux"
      @change="onPageChange"
    />
  </main>
</template>

<script lang="ts" setup>
import type { ListLocalBusinessProspectsQuery } from '#src-core/types/payload/local-business.types'
import { useServerPagination } from '#src-nuxt/app/composables/useServerPagination'
import { useLocalBusinessProspectsStore } from '#src-nuxt/app/stores/localBusinessProspects.store'

definePageMeta({ layout: 'home' })

const store: ReturnType<typeof useLocalBusinessProspectsStore> = useLocalBusinessProspectsStore()

const perPage: number = 50

/**
 * Charge une page de la liste business locaux.
 * @param {number} page - Numero de page.
 * @returns {Promise<void>}
 */
const fetchBusinessPage: (page: number) => Promise<void> = async (page: number): Promise<void> => {
  await store.fetchList({ ...store.filters, page, perPage })
}

/**
 * Retourne le nombre total de pages.
 * @returns {number} Derniere page.
 */
const getBusinessTotalPages: () => number = (): number => store.pagination?.lastPage ?? 1

/**
 * Lit la page courante renvoyee par l'API.
 * @returns {number | undefined} Page courante.
 */
const getBusinessCurrentPageFromMeta: () => number | undefined = (): number | undefined => store.pagination?.currentPage

const {
  currentPage,
  totalPages,
  visiblePages,
  pageButtonClass,
  activePageButtonClass,
  onPageChange,
  resetToFirstPage,
  syncCurrentPageFromMeta,
} = useServerPagination({
  perPage,
  fetchPage: fetchBusinessPage,
  getTotalPages: getBusinessTotalPages,
  getCurrentPageFromMeta: getBusinessCurrentPageFromMeta,
})

/**
 * Charge la liste avec les filtres + perPage et reset la page courante.
 * @param {ListLocalBusinessProspectsQuery} query - Filtres a appliquer.
 * @returns {Promise<void>}
 */
const fetchWithFilters: (query: ListLocalBusinessProspectsQuery) => Promise<void> = async (
  query: ListLocalBusinessProspectsQuery,
): Promise<void> => {
  resetToFirstPage()
  await store.fetchList({ ...query, page: 1, perPage })
  syncCurrentPageFromMeta()
}

onMounted(async (): Promise<void> => {
  await store.fetchList({ page: 1, perPage })
  syncCurrentPageFromMeta()
})
</script>
