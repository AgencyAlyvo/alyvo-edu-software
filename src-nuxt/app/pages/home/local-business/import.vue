<template>
  <main class="grid gap-6">
    <header>
      <p class="text-xs font-semibold tracking-[0.2em] text-[#9a65d5] uppercase">BUSINESS LOCAUX</p>
      <h1 class="mt-2 text-2xl font-semibold text-white">Importer des business depuis OpenStreetMap</h1>
      <p class="mt-1 text-sm text-[#9ba3bd]">
        Recherche par commune dans tout le fichier OSM (sans limite de resultats), previsualise, puis importe ceux qui
        t'interessent. Les grosses villes peuvent prendre une minute ou plus.
      </p>
    </header>

    <div class="flex gap-3 rounded-lg border border-amber-500/40 bg-amber-500/10 px-4 py-3 text-sm" role="note">
      <UIcon name="i-heroicons-exclamation-triangle" class="mt-0.5 size-5 shrink-0 text-amber-400" />
      <div class="min-w-0 text-amber-100/90">
        <p class="font-medium text-amber-200">Nom de ville ou commune exact obligatoire</p>
        <p class="mt-1 leading-relaxed">
          La recherche filtre sur le nom enregistre dans OpenStreetMap (<span class="text-amber-100/70"
            >tag addr:city</span
          >). Utilise l'orthographe officielle complete : tirets, accents et apostrophes inclus. Exemple valide :
          <span class="font-semibold text-white">Saint-Jacques-de-la-Lande</span>
          — une variante comme « St Jacques de la Lande » ne renverra en general aucun resultat.
        </p>
      </div>
    </div>

    <form
      class="grid gap-3 rounded-lg border border-[#2f3d67] bg-[#0b1433]/70 p-4 md:grid-cols-4"
      @submit.prevent="search"
    >
      <UInput
        v-model="city"
        placeholder="Ex. Saint-Jacques-de-la-Lande"
        icon="i-heroicons-map-pin"
        variant="none"
        class="md:col-span-2"
        :ui="inputUi"
        required
      />
      <USelect
        v-model="category"
        :items="categoryItems"
        placeholder="Categorie (optionnel)"
        variant="none"
        :ui="selectUi"
      />
      <UButton
        type="submit"
        :label="store.isSearchingOsm ? 'Recherche...' : 'Rechercher dans OSM'"
        :loading="store.isSearchingOsm"
        icon="i-heroicons-magnifying-glass"
        :class="primaryButtonClass"
      />
    </form>

    <div
      v-if="searchAttempted && !store.isSearchingOsm && store.osmRawCount > 0"
      class="rounded-md border border-[#2f3d67] bg-[#0b1433]/40 px-4 py-3 text-xs text-[#9ba3bd]"
    >
      {{ store.osmRawCount }} business trouves dans OSM pour cette ville - {{ alreadyImportedCount }} deja dans ta base
      (filtres automatiquement) -
      <span class="font-semibold text-white">{{ store.osmPreview.length }} nouveaux a proposer</span>
    </div>

    <p v-if="searchAttempted && !store.isSearchingOsm && store.osmRawCount === 0" class="text-sm text-[#9ba3bd]">
      Aucun resultat trouve dans OSM pour cette recherche. Verifie que le nom de commune correspond exactement a celui
      d'OpenStreetMap (orthographe officielle, tirets, accents).
    </p>
    <p
      v-else-if="searchAttempted && !store.isSearchingOsm && store.osmPreview.length === 0"
      class="text-sm text-[#9ba3bd]"
    >
      Tous les business OSM de cette ville sont deja dans ta base.
    </p>

    <OsmImportPreview :results="store.osmPreview" :importing="isImporting" @import="importSelected" />

    <OsmImportProgressModal v-model="importProgressOpen" :progress="importProgress" :done="importProgressDone" />
  </main>
</template>

<script lang="ts" setup>
import type { ComputedRef, Ref } from 'vue'
import {
  buildLocalBusinessOsmTypeFilterItems,
  type LocalBusinessOsmTypeSelectItem,
} from '#src-core/constants/localBusinessOsmTypeLabels'
import type { OsmBulkImportProgress, OsmSearchResult } from '#src-core/types/payload/local-business.types'
import { useAlyvoDarkUi } from '#src-nuxt/app/composables/useAlyvoDarkUi'
import { useLocalBusinessProspectsStore } from '#src-nuxt/app/stores/localBusinessProspects.store'

definePageMeta({ layout: 'home' })

/**
 * Item de liste deroulante.
 */
type SelectItem = {
  label: string
  value: string
}

/**
 * Statistiques de retour d'un import OSM.
 */
type ImportStats = {
  inserted: number
  skipped: number
  enriched: number
}

const ALL: string = '__all__'

const store: ReturnType<typeof useLocalBusinessProspectsStore> = useLocalBusinessProspectsStore()
const toast: ReturnType<typeof useToast> = useToast()
const { inputUi, selectUi, primaryButtonClass } = useAlyvoDarkUi()
const city: Ref<string> = ref('')
const category: Ref<string> = ref(ALL)
const searchAttempted: Ref<boolean> = ref(false)
const isImporting: Ref<boolean> = ref(false)
const importProgressOpen: Ref<boolean> = ref(false)
const importProgressDone: Ref<boolean> = ref(false)
const importProgress: Ref<OsmBulkImportProgress> = ref({
  total: 0,
  processed: 0,
  inserted: 0,
  skipped: 0,
  enriched: 0,
})

const alreadyImportedCount: ComputedRef<number> = computed((): number =>
  Math.max(0, store.osmRawCount - store.osmPreview.length),
)

const categoryItems: SelectItem[] = [
  { label: 'Tous les types', value: ALL },
  ...buildLocalBusinessOsmTypeFilterItems().map(
    (item: LocalBusinessOsmTypeSelectItem): SelectItem => ({
      label: item.label,
      value: item.value,
    }),
  ),
]

/**
 *
 */
const search: () => Promise<void> = async (): Promise<void> => {
  if (!city.value.trim()) return
  searchAttempted.value = true
  try {
    await store.searchOsm({
      city: city.value.trim(),
      ...(category.value && category.value !== ALL ? { category: category.value } : {}),
    })
  } catch (err) {
    toast.add({
      title: 'Recherche OSM impossible',
      description: (err as Error).message,
      color: 'error',
      duration: 5000,
    })
  }
}

/**
 * Met a jour la modale de progression pendant l'import OSM.
 * @param {OsmBulkImportProgress} progress - Etat courant.
 * @returns {void}
 */
const syncOsmImportProgressModal: (progress: OsmBulkImportProgress) => void = (
  progress: OsmBulkImportProgress,
): void => {
  importProgress.value = { ...progress }
}

/**
 * Importe en masse les resultats OSM selectionnes.
 * @param {OsmSearchResult[]} items - POI a importer.
 * @returns {Promise<void>}
 */
const importSelected: (items: OsmSearchResult[]) => Promise<void> = async (items: OsmSearchResult[]): Promise<void> => {
  isImporting.value = true
  importProgressDone.value = false
  importProgress.value = { total: items.length, processed: 0, inserted: 0, skipped: 0, enriched: 0 }
  importProgressOpen.value = true

  try {
    const stats: ImportStats = await store.bulkImport(
      { items },
      {
        onProgress: syncOsmImportProgressModal,
      },
    )
    importProgressDone.value = true
    const enrichmentSuffix: string =
      stats.enriched > 0 ? ` (${stats.enriched} enrichis via n8n)` : ' (enrichissement n8n indisponible, donnees OSM)'
    toast.add({
      title: 'Import termine',
      description: `${stats.inserted} business importes${enrichmentSuffix}, ${stats.skipped} ignores (doublons).`,
      color: 'success',
      duration: 5000,
    })
    store.osmPreview = []
  } catch (err) {
    importProgressOpen.value = false
    toast.add({
      title: 'Import impossible',
      description: (err as Error).message,
      color: 'error',
      duration: 5000,
    })
  } finally {
    isImporting.value = false
  }
}
</script>
