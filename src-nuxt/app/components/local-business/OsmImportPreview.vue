<template>
  <section v-if="results.length > 0" class="overflow-hidden rounded-lg border border-[#2f3d67] bg-[#0b1433]/70">
    <div class="flex flex-col gap-3 border-b border-[#2f3d67] px-4 py-3 sm:flex-row sm:items-center sm:justify-between">
      <div>
        <p class="text-sm font-semibold text-white">{{ results.length }} resultats OSM disponibles</p>
        <p class="text-xs text-[#9ba3bd]">
          {{ selectedCount }} selectionne(s). Decoche ce que tu ne veux pas importer.
        </p>
      </div>
      <div class="flex flex-wrap gap-2">
        <UButton size="sm" variant="ghost" label="Tout" :class="ghostButtonClass" @click="selectAll" />
        <UButton size="sm" variant="ghost" label="Rien" :class="ghostButtonClass" @click="selectNone" />
        <UButton
          size="sm"
          :label="`Importer ${selectedCount}`"
          :loading="importing"
          :disabled="selectedCount === 0"
          :class="primaryButtonClass"
          @click="emitSelected"
        />
      </div>
    </div>

    <div class="overflow-x-auto">
      <table class="w-full text-left text-sm">
        <thead class="border-b border-[#2f3d67] text-xs text-[#9ba3bd] uppercase">
          <tr>
            <th class="w-10 px-4 py-3">
              <input
                type="checkbox"
                :checked="allSelectedInPage"
                :indeterminate="someSelectedInPage && !allSelectedInPage"
                :class="checkboxClass"
                @change="togglePage"
              />
            </th>
            <th class="px-4 py-3">Nom</th>
            <th class="px-4 py-3">Categorie</th>
            <th class="px-4 py-3">Adresse</th>
            <th class="px-4 py-3">Site</th>
            <th class="px-4 py-3">Email</th>
            <th class="px-4 py-3">Telephone</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="entry in pageItems"
            :key="`${entry.item.osmType}-${entry.item.osmId}`"
            class="border-b border-[#1a2747] text-[#dfe6ff] last:border-0"
            :class="selected[entry.index] ? 'bg-[#111c35]' : 'hover:bg-[#0f1830]'"
          >
            <td class="px-4 py-3">
              <input
                type="checkbox"
                :checked="selected[entry.index]"
                :class="checkboxClass"
                @change="toggle(entry.index)"
              />
            </td>
            <td class="px-4 py-3 font-medium text-white">{{ entry.item.name }}</td>
            <td class="px-4 py-3 text-[#c7d0ea]">
              {{ formatOsmType(entry.item.subcategory, entry.item.category) }}
            </td>
            <td class="px-4 py-3 text-[#c7d0ea]">
              {{ [entry.item.address, entry.item.city, entry.item.postalCode].filter(Boolean).join(', ') || '-' }}
            </td>
            <td class="px-4 py-3">
              <div class="flex justify-center">
                <span
                  v-if="entry.item.website?.trim()"
                  class="inline-flex items-center justify-center rounded-full p-1 text-emerald-400 ring-1 ring-emerald-500/35"
                  title="Site web renseigne"
                >
                  <UIcon name="i-heroicons-check-circle-20-solid" class="h-5 w-5" />
                </span>
                <span
                  v-else
                  class="inline-flex items-center justify-center rounded-full p-1 text-red-400 ring-1 ring-red-500/35"
                  title="Pas de site web"
                >
                  <UIcon name="i-heroicons-x-circle-20-solid" class="h-5 w-5" />
                </span>
              </div>
            </td>
            <td class="px-4 py-3 text-[#c7d0ea]">{{ entry.item.email ?? '-' }}</td>
            <td class="px-4 py-3 text-[#c7d0ea]">{{ entry.item.phone ?? '-' }}</td>
          </tr>
        </tbody>
      </table>
    </div>

    <div
      v-if="totalPages > 1"
      class="flex flex-col items-center gap-3 border-t border-[#2f3d67] px-4 py-3 sm:flex-row sm:justify-between"
    >
      <p class="text-xs text-[#9ba3bd]">Page {{ currentPage }} / {{ totalPages }}</p>
      <nav class="flex items-center gap-1" aria-label="Pagination resultats OSM">
        <button
          type="button"
          :disabled="currentPage === 1"
          :class="pageButtonClass"
          aria-label="Page precedente"
          @click="goToPage(currentPage - 1)"
        >
          <UIcon name="i-heroicons-chevron-left" class="h-4 w-4" />
        </button>
        <template v-for="(page, index) in visiblePages" :key="`${page}-${index}`">
          <span v-if="page === 'ellipsis'" class="px-2 text-sm font-semibold text-[#69759b]">...</span>
          <button
            v-else
            type="button"
            :class="page === currentPage ? activePageButtonClass : pageButtonClass"
            @click="goToPage(page)"
          >
            {{ page }}
          </button>
        </template>
        <button
          type="button"
          :disabled="currentPage === totalPages"
          :class="pageButtonClass"
          aria-label="Page suivante"
          @click="goToPage(currentPage + 1)"
        >
          <UIcon name="i-heroicons-chevron-right" class="h-4 w-4" />
        </button>
      </nav>
    </div>
  </section>
</template>

<script lang="ts" setup>
import type { ComputedRef, Ref } from 'vue'
import { getLocalBusinessOsmTypeLabel } from '#src-core/constants/localBusinessOsmTypeLabels'
import type { OsmSearchResult } from '#src-core/types/payload/local-business.types'
import { useAlyvoDarkUi } from '#src-nuxt/app/composables/useAlyvoDarkUi'

/**
 *
 */
type VisiblePage = number | 'ellipsis'

/**
 * Props de la preview d'import OSM.
 */
type OsmImportPreviewProps = {
  results: OsmSearchResult[]
  importing?: boolean
}

/**
 * Evenements emis par la preview d'import.
 */
type OsmImportPreviewEmits = {
  import: [OsmSearchResult[]]
}

const props: OsmImportPreviewProps = defineProps<OsmImportPreviewProps>()

const emit: (event: 'import', items: OsmSearchResult[]) => void = defineEmits<OsmImportPreviewEmits>()

const { primaryButtonClass, ghostButtonClass, checkboxClass, pageButtonClass, activePageButtonClass } = useAlyvoDarkUi()
const perPage: number = 25
const currentPage: Ref<number> = ref(1)
const selected: Ref<boolean[]> = ref([])

watch(
  () => props.results,
  (next: OsmSearchResult[]): void => {
    selected.value = next.map(() => true)
    currentPage.value = 1
  },
  { immediate: true },
)

const totalPages: ComputedRef<number> = computed((): number => Math.max(1, Math.ceil(props.results.length / perPage)))

const visiblePages: ComputedRef<VisiblePage[]> = computed((): VisiblePage[] => {
  const total: number = totalPages.value
  const current: number = currentPage.value

  if (total <= 7) {
    return Array.from({ length: total }, (_: unknown, index: number): number => index + 1)
  }

  const candidates: number[] = [1, total, current - 1, current, current + 1]
  if (current <= 3) candidates.push(2, 3, 4)
  if (current >= total - 2) candidates.push(total - 3, total - 2, total - 1)

  const sorted: number[] = [...new Set(candidates)]
    .filter((page: number): boolean => page >= 1 && page <= total)
    .sort((a: number, b: number): number => a - b)

  const pages: VisiblePage[] = []
  let previous: number | null = null
  for (const page of sorted) {
    if (previous !== null && page - previous > 1) {
      pages.push('ellipsis')
    }
    pages.push(page)
    previous = page
  }

  return pages
})

/**
 * Change la page courante de la preview OSM.
 * @param {number} page - Numero de page (1-based).
 * @returns {void}
 */
const goToPage: (page: number) => void = (page: number): void => {
  currentPage.value = Math.min(totalPages.value, Math.max(1, page))
}

/**
 * Items affiches sur la page courante avec leur index original (pour conserver la selection).
 */
const pageItems: ComputedRef<{ item: OsmSearchResult; index: number }[]> = computed(
  (): { item: OsmSearchResult; index: number }[] => {
    const start: number = (currentPage.value - 1) * perPage
    const end: number = start + perPage
    return props.results.slice(start, end).map((item: OsmSearchResult, i: number) => ({ item, index: start + i }))
  },
)

const selectedCount: ComputedRef<number> = computed(
  (): number => selected.value.filter((s: boolean): boolean => s).length,
)

/**
 * Emet les POI coches (calcul unique au clic pour eviter de parcourir 2000+ lignes a chaque rendu).
 * @returns {void}
 */
const emitSelected: () => void = (): void => {
  const items: OsmSearchResult[] = []
  for (let idx: number = 0; idx < props.results.length; idx += 1) {
    if (selected.value[idx]) {
      items.push(props.results[idx]!)
    }
  }
  emit('import', items)
}

const allSelectedInPage: ComputedRef<boolean> = computed((): boolean => {
  const items: { item: OsmSearchResult; index: number }[] = pageItems.value
  return (
    items.length > 0 &&
    items.every((e: { item: OsmSearchResult; index: number }): boolean => Boolean(selected.value[e.index]))
  )
})

const someSelectedInPage: ComputedRef<boolean> = computed((): boolean =>
  pageItems.value.some((e: { item: OsmSearchResult; index: number }): boolean => Boolean(selected.value[e.index])),
)

/**
 * Bascule la selection d'une ligne OSM.
 * @param {number} idx - Index global dans la liste complete.
 * @returns {void}
 */
const toggle: (idx: number) => void = (idx: number): void => {
  selected.value[idx] = !selected.value[idx]
}

/**
 * Selectionne ou deselectionne toutes les lignes de la page courante.
 * @returns {void}
 */
const togglePage: () => void = (): void => {
  const next: boolean = !allSelectedInPage.value
  for (const entry of pageItems.value) {
    selected.value[entry.index] = next
  }
}

/**
 * Selectionne tous les resultats OSM.
 * @returns {void}
 */
const selectAll: () => void = (): void => {
  selected.value = selected.value.map((): boolean => true)
}

/**
 * Deselectionne tous les resultats OSM.
 * @returns {void}
 */
const selectNone: () => void = (): void => {
  selected.value = selected.value.map((): boolean => false)
}

/**
 * Libelle francais du type OSM.
 * @param {string | null} subcategory - Valeur OSM.
 * @param {string | null} categoryTag - Cle de tag legacy.
 * @returns {string} Libelle affichable.
 */
const formatOsmType: (subcategory: string | null, categoryTag: string | null) => string = (
  subcategory: string | null,
  categoryTag: string | null,
): string => getLocalBusinessOsmTypeLabel(subcategory, categoryTag)
</script>
