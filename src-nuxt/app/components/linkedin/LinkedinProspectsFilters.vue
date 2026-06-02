<template>
  <form
    class="grid gap-3 rounded-lg border border-[#2f3d67] bg-[#0b1433]/70 p-4 md:grid-cols-[1fr_auto_auto_auto] md:items-end"
    @submit.prevent="applyFilters"
  >
    <AlyvoListFilterField
      label="Recherche texte"
      hint="Prenom, nom, entreprise ou poste LinkedIn (contient le texte saisi)"
    >
      <UInput
        v-model="localSearch"
        icon="i-heroicons-magnifying-glass"
        placeholder="Ex. Dupont, Alyvo, Directeur commercial"
        variant="none"
        class="w-full"
        :ui="inputUi"
      />
    </AlyvoListFilterField>

    <AlyvoListFilterField label="Statut" hint="Etape commerciale du prospect">
      <USelect
        v-model="localStatus"
        :items="statusItems"
        placeholder="Choisir un statut"
        variant="none"
        :ui="selectUi"
        class="min-w-[220px]"
      />
    </AlyvoListFilterField>

    <AlyvoListFilterField label="Favoris" hint="Afficher uniquement les prospects marques en favori">
      <USelect
        v-model="localFavorite"
        :items="favoriteItems"
        placeholder="Tous ou favoris"
        variant="none"
        :ui="selectUi"
        class="min-w-[200px]"
      />
    </AlyvoListFilterField>

    <UButton
      type="submit"
      icon="i-heroicons-funnel"
      label="Filtrer"
      class="h-11 rounded-md bg-[linear-gradient(135deg,#102766_0%,#7446a6_100%)] px-4 py-2 font-semibold text-white shadow-[0_14px_30px_rgba(5,9,23,0.35)] transition hover:bg-[linear-gradient(135deg,#17337c_0%,#9a65d5_100%)]"
    />
  </form>
</template>

<script lang="ts" setup>
import type { Ref } from 'vue'
import { buildLinkedinStatusSelectItems } from '#src-core/constants/linkedinSelectableStatuses'
import type { LinkedinProspectStatus } from '#src-core/types/enums/linkedin.enums'
import type { ListLinkedinProspectsQuery } from '#src-core/types/payload/linkedin.types'
import { isFavoriteOnlyFilter } from '#src-core/utils/queryFilters'

/**
 * Evenements du filtre de prospects.
 */
type LinkedinProspectsFiltersEmits = {
  submit: [query: ListLinkedinProspectsQuery]
}

/**
 * Signature de l'emetteur.
 */
type LinkedinProspectsFiltersEmit = (event: 'submit', query: ListLinkedinProspectsQuery) => void

/**
 * Item de select.
 */
type SelectItem = {
  label: string
  value: string
}

const allStatusesValue: string = 'all'
const allFavoritesValue: string = 'all'
const emit: LinkedinProspectsFiltersEmit = defineEmits<LinkedinProspectsFiltersEmits>()
const localSearch: Ref<string> = ref('')
const localStatus: Ref<string | undefined> = ref(undefined)
const localFavorite: Ref<string> = ref(allFavoritesValue)
/** Configuration UI de l'input de recherche. */
type InputUiConfig = { base: string; leadingIcon: string }
const inputUi: InputUiConfig = {
  base: 'h-11 w-full rounded-md border border-[#2f3d67] bg-[rgba(5,9,23,0.86)] px-3 text-[#f7f8ff] placeholder:text-[#626d90] shadow-[0_10px_24px_rgba(0,0,0,0.18)] outline-none transition hover:border-[#485780] focus:border-[#9a65d5] focus:shadow-[0_0_0_1px_rgba(154,101,213,0.28),0_10px_24px_rgba(0,0,0,0.18)]',
  leadingIcon: 'text-[#9ba3bd]',
} as const
/** Configuration UI du select de statut. */
type SelectUiConfig = {
  base: string
  placeholder: string
  trailingIcon: string
  content: string
  viewport: string
  item: string
  itemWrapper: string
  itemLabel: string
  itemTrailingIcon: string
}
const selectUi: SelectUiConfig = {
  base: 'h-11 w-full cursor-pointer rounded-md border border-[#2f3d67] bg-[rgba(5,9,23,0.86)] px-3 text-[#f7f8ff] shadow-[0_10px_24px_rgba(0,0,0,0.18)] outline-none transition hover:border-[#485780] focus:border-[#9a65d5] focus:shadow-[0_0_0_1px_rgba(154,101,213,0.28),0_10px_24px_rgba(0,0,0,0.18)]',
  placeholder: 'truncate text-[#626d90]',
  trailingIcon: 'text-[#9ba3bd]',
  content:
    'max-h-60 w-(--reka-select-trigger-width) rounded-md border border-[#2f3d67] bg-[#071022] shadow-[0_18px_48px_rgba(0,0,0,0.35)] ring-0 origin-(--reka-select-content-transform-origin)',
  viewport: 'relative divide-y divide-[#152247] scroll-py-1 overflow-y-auto flex-1',
  item: 'group relative flex w-full items-start gap-1.5 rounded-md p-1.5 text-sm !text-[#c7d0ea] outline-none transition-colors hover:bg-[#111c3f] hover:!text-white data-[highlighted]:bg-[#111c3f] data-[highlighted]:!text-white data-[state=checked]:bg-[#16234f] data-[state=checked]:!text-white',
  itemWrapper: 'min-w-0 flex-1 !text-current',
  itemLabel: 'truncate !text-current group-data-[highlighted]:!text-white group-data-[state=checked]:!text-white',
  itemTrailingIcon: 'text-[#9a65d5] group-data-[highlighted]:text-[#c7a8f2] group-data-[state=checked]:text-[#c7a8f2]',
} as const
const statusItems: SelectItem[] = [
  { label: 'Tous les statuts', value: allStatusesValue },
  ...buildLinkedinStatusSelectItems().map(
    (item: { label: string; value: LinkedinProspectStatus }): SelectItem => ({
      label: item.label,
      value: item.value,
    }),
  ),
]

const favoriteItems: SelectItem[] = [
  { label: 'Tous les prospects', value: allFavoritesValue },
  { label: 'Favoris uniquement', value: 'true' },
]

/**
 * Emet les filtres actifs.
 * @returns {void}
 */
const applyFilters: () => void = (): void => {
  emit('submit', {
    search: localSearch.value || undefined,
    status:
      localStatus.value && localStatus.value !== allStatusesValue
        ? [localStatus.value as LinkedinProspectStatus]
        : undefined,
    isFavorite: isFavoriteOnlyFilter(localFavorite.value) ? true : undefined,
    page: 1,
  })
}
</script>
