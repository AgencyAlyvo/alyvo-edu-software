<template>
  <div v-if="loading || safeProspects.length > 0" class="flex items-stretch gap-3">
    <ProspectBulkSelectionPanel
      :selected-count="selectedCount"
      :loading="bulkLoading"
      @favorite="runBulkFavorite"
      @unfavorite="runBulkUnfavorite"
      @delete="requestBulkDelete"
      @select-page="selectPage"
      @clear="clearSelection"
    />
    <div class="min-w-0 flex-1 overflow-hidden rounded-lg border border-[#2f3d67] bg-[#0b1433]/70">
      <div class="relative">
        <div
          v-if="loading"
          class="absolute inset-0 z-10 flex items-center justify-center bg-[#0b1433]/80 text-sm text-[#9ba3bd]"
          aria-live="polite"
        >
          Chargement...
        </div>
        <div :class="loading ? 'pointer-events-none opacity-45' : ''">
          <div class="overflow-x-auto">
            <div class="min-w-[1420px]">
              <div
                class="grid border-b border-[#2f3d67] px-4 py-3 text-xs text-[#9ba3bd] uppercase"
                :style="gridStyle"
                role="row"
              >
                <div role="columnheader" class="flex justify-center">
                  <input
                    ref="pageCheckboxRef"
                    type="checkbox"
                    :checked="allPageSelected"
                    :class="checkboxClass"
                    aria-label="Selectionner tous les business de la page"
                    @click.stop
                    @change="togglePage"
                  />
                </div>
                <div role="columnheader">Business</div>
                <div role="columnheader">Categorie</div>
                <div role="columnheader">Ville</div>
                <div role="columnheader">Site web</div>
                <div role="columnheader">Scores Lighthouse</div>
                <div role="columnheader">Email</div>
                <div role="columnheader">Telephone</div>
                <div role="columnheader">Statut</div>
                <div role="columnheader">Actions</div>
              </div>
              <div
                ref="viewportRef"
                class="relative max-h-[70vh] overflow-y-auto"
                :style="{ minHeight: `${Math.min(safeProspects.length, 12) * rowHeight}px` }"
                role="rowgroup"
              >
                <div :style="{ height: `${totalHeight}px`, position: 'relative' }">
                  <div
                    v-for="entry in visibleItems"
                    :key="entry.item.id"
                    class="absolute right-0 left-0 grid cursor-pointer items-center border-b border-[#1a2747] px-4 text-sm text-[#dfe6ff] hover:bg-[#111c35]"
                    :class="isSelected(entry.item.id) ? 'bg-[#111c35]' : ''"
                    :style="{
                      transform: `translateY(${entry.top}px)`,
                      height: `${rowHeight}px`,
                      gridTemplateColumns: gridStyle.gridTemplateColumns,
                    }"
                    role="row"
                    @click="openProspect(entry.item.id)"
                  >
                    <div role="cell" class="flex justify-center" @click.stop>
                      <input
                        type="checkbox"
                        :checked="isSelected(entry.item.id)"
                        :class="checkboxClass"
                        :aria-label="`Selectionner ${entry.item.name}`"
                        @change="toggle(entry.item.id)"
                      />
                    </div>
                    <div role="cell" class="min-w-0">
                      <span class="block truncate font-medium text-white">{{ entry.item.name }}</span>
                    </div>
                    <div role="cell" class="truncate text-[#c7d0ea]">
                      {{ formatOsmType(entry.item.subcategory, entry.item.category) }}
                    </div>
                    <div role="cell" class="min-w-0 text-[#c7d0ea]">
                      <span class="block truncate">{{ entry.item.city ?? '-' }}</span>
                      <p v-if="entry.item.postalCode" class="truncate text-xs text-[#69759b]">
                        {{ entry.item.postalCode }}
                      </p>
                    </div>
                    <div role="cell" class="flex justify-center" @click.stop>
                      <a
                        v-if="hasWebsiteUrl(entry.item)"
                        :href="entry.item.website!"
                        target="_blank"
                        rel="noopener noreferrer"
                        :title="`Ouvrir le site : ${entry.item.website}`"
                        class="inline-flex items-center justify-center rounded-full p-1 text-emerald-400 ring-1 ring-emerald-500/35 transition hover:bg-emerald-500/15 hover:text-emerald-300 hover:ring-emerald-400/55"
                        :aria-label="`Ouvrir le site web de ${entry.item.name}`"
                      >
                        <UIcon name="i-heroicons-check-circle-20-solid" class="h-5 w-5" />
                      </a>
                      <span
                        v-else
                        class="inline-flex items-center justify-center rounded-full p-1 text-red-400 ring-1 ring-red-500/35"
                        title="Pas de site web"
                        aria-label="Pas de site web"
                      >
                        <UIcon name="i-heroicons-x-circle-20-solid" class="h-5 w-5" />
                      </span>
                    </div>
                    <div role="cell">
                      <div v-if="hasAnyScore(entry.item)" class="flex flex-wrap gap-1">
                        <span
                          class="rounded px-1.5 py-0.5 text-[10px] font-bold"
                          :title="`SEO ${entry.item.seoScore ?? '-'}`"
                          :class="seoBadgeClasses(entry.item.seoScore)"
                          >SEO {{ entry.item.seoScore ?? '-' }}</span
                        >
                        <span
                          class="rounded px-1.5 py-0.5 text-[10px] font-bold"
                          :title="`Performance ${entry.item.performanceScore ?? '-'}`"
                          :class="seoBadgeClasses(entry.item.performanceScore)"
                          >PERF {{ entry.item.performanceScore ?? '-' }}</span
                        >
                        <span
                          class="rounded px-1.5 py-0.5 text-[10px] font-bold"
                          :title="`Accessibilite ${entry.item.accessibilityScore ?? '-'}`"
                          :class="seoBadgeClasses(entry.item.accessibilityScore)"
                          >A11Y {{ entry.item.accessibilityScore ?? '-' }}</span
                        >
                        <span
                          class="rounded px-1.5 py-0.5 text-[10px] font-bold"
                          :title="`Bonnes pratiques ${entry.item.bestPracticesScore ?? '-'}`"
                          :class="seoBadgeClasses(entry.item.bestPracticesScore)"
                          >BP {{ entry.item.bestPracticesScore ?? '-' }}</span
                        >
                      </div>
                      <span v-else class="text-[#69759b]">-</span>
                    </div>
                    <div role="cell" class="min-w-0 text-[#c7d0ea]">
                      <a
                        v-if="entry.item.email"
                        :href="`mailto:${entry.item.email}`"
                        :title="entry.item.email"
                        class="block truncate hover:underline"
                        @click.stop
                        >{{ entry.item.email }}</a
                      >
                      <span v-else class="text-[#69759b]">-</span>
                    </div>
                    <div role="cell" class="min-w-0 text-[#c7d0ea]">
                      <a
                        v-if="entry.item.phone"
                        :href="`tel:${entry.item.phone}`"
                        :title="entry.item.phone"
                        class="block truncate hover:underline"
                        @click.stop
                        >{{ entry.item.phone }}</a
                      >
                      <span v-else class="text-[#69759b]">-</span>
                    </div>
                    <div role="cell" @click.stop>
                      <LightStatusCell
                        :model-value="entry.item.status"
                        :items="statusItems"
                        @update:model-value="(status: LocalBusinessStatus) => updateStatus(entry.item, status)"
                      />
                    </div>
                    <div role="cell" class="flex items-center gap-1" @click.stop>
                      <LightIconButton
                        :icon="entry.item.isFavorite ? 'i-heroicons-star-solid' : 'i-heroicons-star'"
                        :title="entry.item.isFavorite ? 'Retirer des favoris' : 'Ajouter aux favoris'"
                        :tone="entry.item.isFavorite ? 'favorite-active' : 'neutral'"
                        :loading="isUpdating(entry.item.id)"
                        @click="toggleFavorite(entry.item)"
                      />
                      <LightIconButton
                        icon="i-heroicons-sparkles"
                        title="Enrichir (Lighthouse + emails)"
                        tone="info"
                        :loading="isUpdating(entry.item.id)"
                        @click="enrichProspect(entry.item)"
                      />
                      <LightIconButton
                        icon="i-heroicons-trash"
                        title="Supprimer"
                        tone="danger"
                        :loading="isUpdating(entry.item.id)"
                        @click="requestDelete(entry.item)"
                      />
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
  <ConfirmDialog
    v-model="bulkDeleteDialogOpen"
    title="Supprimer la selection"
    :message="bulkDeleteDialogMessage"
    confirm-label="Supprimer"
    :loading="bulkLoading"
    @confirm="confirmBulkDelete"
  />
  <ConfirmDialog
    v-model="deleteDialogOpen"
    title="Supprimer le business"
    :message="deleteDialogMessage"
    confirm-label="Supprimer"
    :loading="prospectPendingDeletion ? isUpdating(prospectPendingDeletion.id) : false"
    @confirm="confirmDelete"
  />
</template>

<script lang="ts" setup>
import type { ComputedRef, Ref } from 'vue'
import {
  buildLocalBusinessStatusSelectItems,
  type LocalBusinessStatusSelectItem,
} from '#src-core/constants/localBusinessSelectableStatuses'
import type { LocalBusinessStatus } from '#src-core/types/enums/local-business.enums'
import { ProspectBulkAction } from '#src-core/types/enums/prospect-bulk-action.enums'
import { getLocalBusinessOsmTypeLabel } from '#src-core/constants/localBusinessOsmTypeLabels'
import { LocalBusinessStatusLabels } from '#src-core/types/enums/local-business.enums'
import type { LocalBusinessProspectSummary } from '#src-core/types/response/local-business.types'
import { useAlyvoDarkUi } from '#src-nuxt/app/composables/useAlyvoDarkUi'
import { useProspectIdSelection } from '#src-nuxt/app/composables/useProspectIdSelection'
import { useLocalBusinessProspectsStore } from '#src-nuxt/app/stores/localBusinessProspects.store'
import { useVirtualList } from '#src-nuxt/app/composables/useVirtualList'

/**
 * Props de la table business locaux.
 */
type LocalBusinessTableProps = {
  prospects?: readonly LocalBusinessProspectSummary[]
  loading?: boolean
}

const props: LocalBusinessTableProps = withDefaults(defineProps<LocalBusinessTableProps>(), {
  /**
   * Retourne la liste vide par defaut.
   * @returns {readonly LocalBusinessProspectSummary[]} Liste vide.
   */
  prospects: (): readonly LocalBusinessProspectSummary[] => [],
  loading: false,
})

const store: ReturnType<typeof useLocalBusinessProspectsStore> = useLocalBusinessProspectsStore()
const router: ReturnType<typeof useRouter> = useRouter()
const toast: ReturnType<typeof useToast> = useToast()
const { checkboxClass } = useAlyvoDarkUi()
const updatingIds: Ref<Set<number>> = ref(new Set<number>())
const deleteDialogOpen: Ref<boolean> = ref(false)
const bulkDeleteDialogOpen: Ref<boolean> = ref(false)
const bulkLoading: Ref<boolean> = ref(false)
const pageCheckboxRef: Ref<HTMLInputElement | null> = ref(null)
const prospectPendingDeletion: Ref<LocalBusinessProspectSummary | undefined> = ref(undefined)

const statusItems: readonly LocalBusinessStatusSelectItem[] = buildLocalBusinessStatusSelectItems()

const safeProspects: ComputedRef<readonly LocalBusinessProspectSummary[]> = computed(
  (): readonly LocalBusinessProspectSummary[] => props.prospects ?? [],
)

const rowHeight: number = 64

const gridStyle: { gridTemplateColumns: string } = {
  gridTemplateColumns:
    '40px minmax(200px,1.4fr) minmax(140px,0.9fr) minmax(140px,1fr) 80px minmax(220px,1.4fr) minmax(180px,1.1fr) minmax(140px,0.9fr) minmax(220px,1.3fr) minmax(140px,0.9fr)',
}

const pageIds: ComputedRef<number[]> = computed((): number[] =>
  safeProspects.value.map((prospect: LocalBusinessProspectSummary): number => prospect.id),
)

const {
  selectedIds,
  selectedCount,
  isSelected,
  toggle,
  selectPage,
  clear: clearSelection,
  allPageSelected,
  somePageSelected,
  togglePage,
} = useProspectIdSelection({ pageIds })

watch([allPageSelected, somePageSelected], (): void => {
  const input: HTMLInputElement | null = pageCheckboxRef.value
  if (!input) return
  input.indeterminate = somePageSelected.value && !allPageSelected.value
})

const bulkDeleteDialogMessage: ComputedRef<string> = computed(
  (): string => `Supprimer definitivement ${selectedCount.value} business(s) ? Cette action est irreversible.`,
)

const viewportRef: Ref<HTMLDivElement | null> = ref(null)

const { visibleItems, totalHeight } = useVirtualList<LocalBusinessProspectSummary>({
  items: safeProspects,
  rowHeight,
  containerRef: viewportRef,
  overscan: 6,
})

const deleteDialogMessage: ComputedRef<string> = computed((): string => {
  const prospect: LocalBusinessProspectSummary | undefined = prospectPendingDeletion.value
  if (!prospect) return 'Ce business sera supprime definitivement.'
  return `Supprimer definitivement ${prospect.name} ?`
})

/**
 * Libelle francais du type OSM (sous-categorie).
 * @param {string | null} subcategory - Valeur OSM (bakery, restaurant, ...).
 * @param {string | null} categoryTag - Ancienne cle de tag (shop, amenity).
 * @returns {string} Libelle affichable.
 */
const formatOsmType: (subcategory: string | null, categoryTag: string | null) => string = (
  subcategory: string | null,
  categoryTag: string | null,
): string => getLocalBusinessOsmTypeLabel(subcategory, categoryTag)

/**
 * Couleur du badge selon le score Lighthouse.
 * @param {number | null} score - Score 0-100.
 * @returns {string} Classes Tailwind.
 */
const seoBadgeClasses: (score: number | null) => string = (score: number | null): string => {
  if (score === null) return 'bg-slate-700 text-[#9ba3bd]'
  if (score >= 80) return 'bg-emerald-700 text-white'
  if (score >= 50) return 'bg-amber-600 text-white'
  return 'bg-red-700 text-white'
}

/**
 * Indique si au moins un score Lighthouse est renseigne.
 * @param {LocalBusinessProspectSummary} prospect - Business local.
 * @returns {boolean} True si au moins un score est non null.
 */
const hasAnyScore: (prospect: LocalBusinessProspectSummary) => boolean = (
  prospect: LocalBusinessProspectSummary,
): boolean =>
  prospect.seoScore !== null ||
  prospect.performanceScore !== null ||
  prospect.accessibilityScore !== null ||
  prospect.bestPracticesScore !== null

/**
 * Indique si le business a une URL de site web renseignee.
 * @param {LocalBusinessProspectSummary} prospect - Business local.
 * @returns {boolean} True si une URL non vide est presente.
 */
const hasWebsiteUrl: (prospect: LocalBusinessProspectSummary) => boolean = (
  prospect: LocalBusinessProspectSummary,
): boolean => Boolean(prospect.website?.trim())

/**
 * Navigue vers la fiche d'un business local.
 * @param {number} id - Identifiant du prospect.
 * @returns {Promise<void>}
 */
const openProspect: (id: number) => Promise<void> = async (id: number): Promise<void> => {
  await router.push(`/home/local-business/${id}`)
}

/**
 * Marque ou supprime un prospect comme en cours de mise a jour.
 * @param {number} id - Identifiant du prospect.
 * @param {boolean} value - Valeur.
 * @returns {void}
 */
const setUpdating: (id: number, value: boolean) => void = (id: number, value: boolean): void => {
  const next: Set<number> = new Set(updatingIds.value)
  if (value) next.add(id)
  else next.delete(id)
  updatingIds.value = next
}

/**
 * Indique si un prospect est en cours de mise a jour.
 * @param {number} id - Identifiant du prospect.
 * @returns {boolean} True si en cours.
 */
const isUpdating: (id: number) => boolean = (id: number): boolean => updatingIds.value.has(id)

/**
 * Bascule le marqueur favori d'un business.
 * @param {LocalBusinessProspectSummary} prospect - Business local.
 * @returns {Promise<void>}
 */
const toggleFavorite: (prospect: LocalBusinessProspectSummary) => Promise<void> = async (
  prospect: LocalBusinessProspectSummary,
): Promise<void> => {
  const nextFavorite: boolean = !prospect.isFavorite
  setUpdating(prospect.id, true)
  try {
    await store.update(prospect.id, { isFavorite: nextFavorite }, { refreshCurrent: false })
    if (store.filters.isFavorite === true) {
      await store.fetchList({ ...store.filters })
    }
  } finally {
    setUpdating(prospect.id, false)
  }
}

/**
 * Met a jour le statut d'un prospect.
 * @param {LocalBusinessProspectSummary} prospect - Prospect business local.
 * @param {LocalBusinessStatus} status - Statut du prospect.
 * @returns {Promise<void>}
 */
const updateStatus: (prospect: LocalBusinessProspectSummary, status: LocalBusinessStatus) => Promise<void> = async (
  prospect: LocalBusinessProspectSummary,
  status: LocalBusinessStatus,
): Promise<void> => {
  if (status === prospect.status) return
  setUpdating(prospect.id, true)
  try {
    await store.update(prospect.id, { status })
    toast.add({
      title: 'Statut mis a jour',
      description: LocalBusinessStatusLabels[status],
      color: 'success',
      duration: 3000,
    })
  } finally {
    setUpdating(prospect.id, false)
  }
}

/**
 * Lance l'enrichissement n8n d'un business local.
 * @param {LocalBusinessProspectSummary} prospect - Prospect business local.
 * @returns {Promise<void>}
 */
const enrichProspect: (prospect: LocalBusinessProspectSummary) => Promise<void> = async (
  prospect: LocalBusinessProspectSummary,
): Promise<void> => {
  setUpdating(prospect.id, true)
  try {
    await store.enrich(prospect.id)
    toast.add({
      title: 'Business enrichi',
      description: `${prospect.name} a ete enrichi (Lighthouse + emails).`,
      color: 'success',
      duration: 3000,
    })
  } catch (err) {
    toast.add({
      title: "Echec de l'enrichissement",
      description: (err as Error).message,
      color: 'error',
      duration: 4000,
    })
  } finally {
    setUpdating(prospect.id, false)
  }
}

/**
 * Ouvre la confirmation de suppression.
 * @param {LocalBusinessProspectSummary} prospect - Prospect a supprimer.
 * @returns {void}
 */
const requestDelete: (prospect: LocalBusinessProspectSummary) => void = (
  prospect: LocalBusinessProspectSummary,
): void => {
  prospectPendingDeletion.value = prospect
  deleteDialogOpen.value = true
}

/**
 * Supprime le prospect selectionne apres confirmation.
 * @returns {Promise<void>}
 */
const confirmDelete: () => Promise<void> = async (): Promise<void> => {
  const prospect: LocalBusinessProspectSummary | undefined = prospectPendingDeletion.value
  if (!prospect) {
    deleteDialogOpen.value = false
    return
  }
  setUpdating(prospect.id, true)
  try {
    await store.destroy(prospect.id)
    toast.add({
      title: 'Business supprime',
      description: `${prospect.name} a ete retire de la liste.`,
      color: 'success',
      duration: 3000,
    })
    deleteDialogOpen.value = false
    prospectPendingDeletion.value = undefined
  } finally {
    setUpdating(prospect.id, false)
  }
}

/**
 * Execute une action groupée puis rafraichit la liste si necessaire.
 * @param {ProspectBulkAction} action - Action a appliquer.
 * @param {string} successTitle - Titre du toast de succes.
 * @returns {Promise<void>}
 */
const runBulk: (action: ProspectBulkAction, successTitle: string) => Promise<void> = async (
  action: ProspectBulkAction,
  successTitle: string,
): Promise<void> => {
  const ids: number[] = [...selectedIds.value]
  if (ids.length === 0) return
  bulkLoading.value = true
  try {
    const affected: number = await store.bulkAction(ids, action)
    clearSelection()
    if (action === ProspectBulkAction.DELETE || store.filters.isFavorite === true) {
      await store.fetchList({ ...store.filters })
    }
    toast.add({
      title: successTitle,
      description: `${affected} element(s) mis a jour.`,
      color: 'success',
      duration: 3000,
    })
  } finally {
    bulkLoading.value = false
  }
}

/**
 * Met en favoris la selection courante.
 * @returns {Promise<void>}
 */
const runBulkFavorite: () => Promise<void> = (): Promise<void> =>
  runBulk(ProspectBulkAction.FAVORITE, 'Favoris mis a jour')

/**
 * Retire des favoris la selection courante.
 * @returns {Promise<void>}
 */
const runBulkUnfavorite: () => Promise<void> = (): Promise<void> =>
  runBulk(ProspectBulkAction.UNFAVORITE, 'Favoris mis a jour')

/**
 * Ouvre la confirmation de suppression groupée.
 * @returns {void}
 */
const requestBulkDelete: () => void = (): void => {
  bulkDeleteDialogOpen.value = true
}

/**
 * Supprime la selection apres confirmation.
 * @returns {Promise<void>}
 */
const confirmBulkDelete: () => Promise<void> = async (): Promise<void> => {
  bulkDeleteDialogOpen.value = false
  await runBulk(ProspectBulkAction.DELETE, 'Business supprimes')
}
</script>
