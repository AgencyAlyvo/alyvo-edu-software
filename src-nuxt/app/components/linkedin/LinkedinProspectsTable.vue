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
            <div class="min-w-[1380px]">
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
                    aria-label="Selectionner tous les prospects de la page"
                    @click.stop
                    @change="togglePage"
                  />
                </div>
                <div role="columnheader">Prospect</div>
                <div role="columnheader">Poste</div>
                <div role="columnheader">Entreprise</div>
                <div role="columnheader">Ville</div>
                <div role="columnheader">Region</div>
                <div role="columnheader">Secteur</div>
                <div role="columnheader">Statut</div>
                <div role="columnheader">Prochaine action</div>
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
                        :aria-label="`Selectionner ${entry.item.firstName} ${entry.item.lastName}`"
                        @change="toggle(entry.item.id)"
                      />
                    </div>
                    <div role="cell">
                      <span class="block truncate font-medium text-white">
                        {{ entry.item.firstName }} {{ entry.item.lastName }}
                      </span>
                    </div>
                    <div role="cell" class="truncate text-[#c7d0ea]">{{ entry.item.position ?? '-' }}</div>
                    <div role="cell" class="truncate">{{ entry.item.company ?? '-' }}</div>
                    <div role="cell" class="truncate text-[#c7d0ea]">{{ entry.item.city ?? '-' }}</div>
                    <div role="cell" class="truncate text-[#c7d0ea]">{{ entry.item.region ?? '-' }}</div>
                    <div role="cell" class="truncate text-[#c7d0ea]">{{ entry.item.industry ?? '-' }}</div>
                    <div role="cell" @click.stop>
                      <LightStatusCell
                        :model-value="normalizeStatusForSelect(entry.item.status)"
                        :items="statusItems"
                        @update:model-value="(status: LinkedinProspectStatus) => updateStatus(entry.item, status)"
                      />
                    </div>
                    <div role="cell" class="truncate text-[#9ba3bd]">{{ getNextActionLabel(entry.item) }}</div>
                    <div role="cell" class="flex items-center gap-1" @click.stop>
                      <LightIconButton
                        :icon="entry.item.isFavorite ? 'i-heroicons-star-solid' : 'i-heroicons-star'"
                        :title="entry.item.isFavorite ? 'Retirer des favoris' : 'Ajouter aux favoris'"
                        :tone="entry.item.isFavorite ? 'favorite-active' : 'neutral'"
                        :loading="isUpdating(entry.item.id)"
                        @click="toggleFavorite(entry.item)"
                      />
                      <LightIconButton
                        icon="i-heroicons-arrow-top-right-on-square"
                        title="Ouvrir LinkedIn"
                        :disabled="!entry.item.linkedinUrl"
                        @click="onLinkedinClick($event, entry.item)"
                      />
                      <LightIconButton
                        icon="i-heroicons-arrow-path"
                        title="Mettre a jour depuis LinkedIn"
                        tone="info"
                        :disabled="!entry.item.linkedinUrl"
                        :loading="isUpdating(entry.item.id)"
                        @click="refreshProspect(entry.item)"
                      />
                      <LightIconButton
                        icon="i-heroicons-trash"
                        title="Supprimer le prospect"
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
    title="Supprimer le prospect"
    :message="deleteDialogMessage"
    confirm-label="Supprimer"
    :loading="prospectPendingDeletion ? isUpdating(prospectPendingDeletion.id) : false"
    @confirm="confirmDelete"
  />
</template>

<script lang="ts" setup>
import type { ComputedRef, Ref } from 'vue'
import {
  buildLinkedinStatusSelectItems,
  linkedinSelectableStatusLabels,
  linkedinRelanceOnlyStatuses,
  linkedinTerminalNextActionLabels,
} from '#src-core/constants/linkedinSelectableStatuses'
import { ProspectBulkAction } from '#src-core/types/enums/prospect-bulk-action.enums'
import { LinkedinProspectStatus } from '#src-core/types/enums/linkedin.enums'
import type { LinkedinProspectSummary } from '#src-core/types/response/linkedin.types'
import { useAlyvoDarkUi } from '#src-nuxt/app/composables/useAlyvoDarkUi'
import { useProspectIdSelection } from '#src-nuxt/app/composables/useProspectIdSelection'
import { useLinkedinProspectsStore } from '#src-nuxt/app/stores/linkedinProspects.store'
import { useVirtualList } from '#src-nuxt/app/composables/useVirtualList'
import { normalizeExternalUrl, openExternalUrl } from '#src-nuxt/app/utils/externalUrl'

/**
 * Props de la table prospects.
 */
type LinkedinProspectsTableProps = {
  prospects?: readonly LinkedinProspectSummary[]
  loading?: boolean
}

/**
 * Item de selection des statuts.
 */
type StatusItem = {
  label: string
  value: LinkedinProspectStatus
}

const props: LinkedinProspectsTableProps = withDefaults(defineProps<LinkedinProspectsTableProps>(), {
  /**
   * Retourne la liste vide par defaut.
   * @returns {readonly LinkedinProspectSummary[]} Liste vide.
   */
  prospects: (): readonly LinkedinProspectSummary[] => [],
  loading: false,
})

const store: ReturnType<typeof useLinkedinProspectsStore> = useLinkedinProspectsStore()
const router: ReturnType<typeof useRouter> = useRouter()
const toast: ReturnType<typeof useToast> = useToast()
const { checkboxClass } = useAlyvoDarkUi()
const updatingIds: Ref<Set<number>> = ref(new Set<number>())
const deleteDialogOpen: Ref<boolean> = ref(false)
const bulkDeleteDialogOpen: Ref<boolean> = ref(false)
const bulkLoading: Ref<boolean> = ref(false)
const pageCheckboxRef: Ref<HTMLInputElement | null> = ref(null)
const prospectPendingDeletion: Ref<LinkedinProspectSummary | undefined> = ref(undefined)

const statusItems: readonly StatusItem[] = buildLinkedinStatusSelectItems()
const statusLabels: Record<LinkedinProspectStatus, string> = linkedinSelectableStatusLabels
const relanceLegacyStatuses: LinkedinProspectStatus[] = linkedinRelanceOnlyStatuses

const safeProspects: ComputedRef<readonly LinkedinProspectSummary[]> = computed(
  (): readonly LinkedinProspectSummary[] => props.prospects ?? [],
)

const rowHeight: number = 56

const gridStyle: { gridTemplateColumns: string } = {
  gridTemplateColumns:
    '40px minmax(180px,1.2fr) minmax(140px,1fr) minmax(140px,1fr) minmax(110px,0.8fr) minmax(110px,0.8fr) minmax(110px,0.8fr) minmax(220px,1.4fr) minmax(160px,1fr) minmax(180px,1.1fr)',
}

const pageIds: ComputedRef<number[]> = computed((): number[] =>
  safeProspects.value.map((prospect: LinkedinProspectSummary): number => prospect.id),
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
  (): string => `Supprimer definitivement ${selectedCount.value} prospect(s) ? Cette action est irreversible.`,
)

const viewportRef: Ref<HTMLDivElement | null> = ref(null)

const { visibleItems, totalHeight } = useVirtualList<LinkedinProspectSummary>({
  items: safeProspects,
  rowHeight,
  containerRef: viewportRef,
  overscan: 6,
})

/**
 * Normalise un statut legacy de relance vers message 1 envoye pour le select.
 * @param {LinkedinProspectStatus} status - Statut courant.
 * @returns {LinkedinProspectStatus} Statut affiche.
 */
const normalizeStatusForSelect: (status: LinkedinProspectStatus) => LinkedinProspectStatus = (
  status: LinkedinProspectStatus,
): LinkedinProspectStatus => {
  if (relanceLegacyStatuses.includes(status)) {
    return LinkedinProspectStatus.MESSAGE_1_ENVOYE
  }
  return status
}

const deleteDialogMessage: ComputedRef<string> = computed((): string => {
  const prospect: LinkedinProspectSummary | undefined = prospectPendingDeletion.value
  if (!prospect) {
    return 'Ce prospect sera supprime definitivement.'
  }
  return `Supprimer definitivement ${prospect.firstName} ${prospect.lastName} ?`
})

/**
 * Navigue vers la fiche d'un prospect.
 * @param {number} id - Identifiant du prospect.
 * @returns {Promise<void>}
 */
const openProspect: (id: number) => Promise<void> = async (id: number): Promise<void> => {
  await router.push(`/home/linkedin/${id}`)
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
 * @returns {boolean} True si en cours de mise a jour.
 */
const isUpdating: (id: number) => boolean = (id: number): boolean => updatingIds.value.has(id)

/**
 * Bascule le marqueur favori d'un prospect.
 * @param {LinkedinProspectSummary} prospect - Prospect LinkedIn.
 * @returns {Promise<void>}
 */
const toggleFavorite: (prospect: LinkedinProspectSummary) => Promise<void> = async (
  prospect: LinkedinProspectSummary,
): Promise<void> => {
  const nextFavorite: boolean = !prospect.isFavorite
  setUpdating(prospect.id, true)
  try {
    await store.update(prospect.id, { isFavorite: nextFavorite })
    if (store.filters.isFavorite === true) {
      await store.fetchList({ ...store.filters })
    }
  } finally {
    setUpdating(prospect.id, false)
  }
}

/**
 * Met a jour le statut d'un prospect.
 * @param {LinkedinProspectSummary} prospect - Prospect LinkedIn.
 * @param {LinkedinProspectStatus} status - Statut du prospect.
 * @returns {Promise<void>}
 */
const updateStatus: (prospect: LinkedinProspectSummary, status: LinkedinProspectStatus) => Promise<void> = async (
  prospect: LinkedinProspectSummary,
  status: LinkedinProspectStatus,
): Promise<void> => {
  if (status === prospect.status) {
    return
  }
  setUpdating(prospect.id, true)
  try {
    await store.update(prospect.id, { status })
    toast.add({
      title: 'Statut mis à jour',
      description: statusLabels[status],
      color: 'success',
      duration: 3000,
    })
  } finally {
    setUpdating(prospect.id, false)
  }
}

/**
 * Relance l'enrichissement n8n et met a jour la fiche du prospect.
 * @param {LinkedinProspectSummary} prospect - Prospect LinkedIn.
 * @returns {Promise<void>}
 */
const refreshProspect: (prospect: LinkedinProspectSummary) => Promise<void> = async (
  prospect: LinkedinProspectSummary,
): Promise<void> => {
  if (!prospect.linkedinUrl) {
    toast.add({
      title: 'URL LinkedIn manquante',
      description: 'Ajoute une URL LinkedIn avant de rafraichir ce prospect.',
      color: 'warning',
      duration: 3000,
    })
    return
  }
  setUpdating(prospect.id, true)
  try {
    await store.refresh(prospect.id)
    toast.add({
      title: 'Prospect mis a jour',
      description: `${prospect.firstName} ${prospect.lastName} a ete rafraichi depuis LinkedIn.`,
      color: 'success',
      duration: 3000,
    })
  } finally {
    setUpdating(prospect.id, false)
  }
}

/**
 * Ouvre le profil LinkedIn dans le navigateur externe.
 * @param {MouseEvent} event - Evenement de clic.
 * @param {LinkedinProspectSummary} prospect - Prospect.
 * @returns {Promise<void>}
 */
const onLinkedinClick: (event: MouseEvent, prospect: LinkedinProspectSummary) => Promise<void> = async (
  event: MouseEvent,
  prospect: LinkedinProspectSummary,
): Promise<void> => {
  event.preventDefault()
  event.stopPropagation()
  const url: string | undefined = normalizeExternalUrl(prospect.linkedinUrl)
  if (!url) return
  await openExternalUrl(url)
}

/**
 * Ouvre la confirmation de suppression.
 * @param {LinkedinProspectSummary} prospect - Prospect a supprimer.
 * @returns {void}
 */
const requestDelete: (prospect: LinkedinProspectSummary) => void = (prospect: LinkedinProspectSummary): void => {
  prospectPendingDeletion.value = prospect
  deleteDialogOpen.value = true
}

/**
 * Supprime le prospect selectionne apres confirmation.
 * @returns {Promise<void>}
 */
const confirmDelete: () => Promise<void> = async (): Promise<void> => {
  const prospect: LinkedinProspectSummary | undefined = prospectPendingDeletion.value
  if (!prospect) {
    deleteDialogOpen.value = false
    return
  }
  setUpdating(prospect.id, true)
  try {
    await store.destroy(prospect.id)
    toast.add({
      title: 'Prospect supprime',
      description: `${prospect.firstName} ${prospect.lastName} a ete retire de la liste.`,
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
 * Retourne le libelle de la prochaine action d'un prospect.
 * @param {LinkedinProspectSummary} prospect - Prospect LinkedIn.
 * @returns {string} Libelle affiche.
 */
const getNextActionLabel: (prospect: LinkedinProspectSummary) => string = (prospect: LinkedinProspectSummary): string =>
  prospect.nextAction ?? linkedinTerminalNextActionLabels[prospect.status] ?? 'A definir'

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
  await runBulk(ProspectBulkAction.DELETE, 'Prospects supprimes')
}
</script>
