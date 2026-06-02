<template>
  <form
    class="grid grid-cols-1 gap-3 rounded-lg border border-[#2f3d67] bg-[#0b1433]/70 p-4 md:grid-cols-4"
    @submit.prevent="submit"
  >
    <AlyvoListFilterField
      label="Recherche texte"
      hint="Nom du commerce, sous-categorie, adresse ou ville (contient le texte saisi)"
    >
      <UInput
        v-model="search"
        placeholder="Ex. Station U, Fuel, 35136, rue de Nantes"
        icon="i-heroicons-magnifying-glass"
        variant="none"
        class="w-full"
        :ui="inputUi"
      />
    </AlyvoListFilterField>

    <AlyvoListFilterField
      label="Ville seule"
      hint="Filtre additionnel sur la ville enregistree (independant de la recherche texte)"
    >
      <UInput v-model="city" placeholder="Ex. Saint-Jacques-de-la-Lande" variant="none" class="w-full" :ui="inputUi" />
    </AlyvoListFilterField>

    <AlyvoListFilterField label="Statut" hint="Etape commerciale du prospect">
      <USelect v-model="status" :items="statusItems" placeholder="Choisir un statut" variant="none" :ui="selectUi" />
    </AlyvoListFilterField>

    <AlyvoListFilterField label="Favoris" hint="Afficher uniquement les business marques en favori">
      <USelect v-model="favorite" :items="favoriteItems" placeholder="Tous ou favoris" variant="none" :ui="selectUi" />
    </AlyvoListFilterField>

    <AlyvoListFilterField label="Type de commerce" hint="Valeur OSM (restaurant, boulangerie, banque, etc.)">
      <USelect
        v-model="category"
        :items="categoryItems"
        placeholder="Choisir une categorie"
        variant="none"
        :ui="selectUi"
      />
    </AlyvoListFilterField>

    <AlyvoListFilterField label="Site web" hint="Presence d une URL de site renseignee">
      <USelect
        v-model="hasWebsite"
        :items="websiteItems"
        placeholder="Avec ou sans site"
        variant="none"
        :ui="selectUi"
      />
    </AlyvoListFilterField>

    <AlyvoListFilterField label="Score SEO max" hint="Affiche les fiches dont le score SEO est inferieur ou egal">
      <USelect
        v-model="seoScoreMax"
        :items="seoScoreItems"
        placeholder="Plafond de score"
        variant="none"
        :ui="selectUi"
      />
    </AlyvoListFilterField>

    <div class="flex gap-2 md:col-span-4 md:justify-end">
      <UButton type="button" variant="ghost" label="Reinitialiser" :class="ghostButtonClass" @click="reset" />
      <UButton type="submit" label="Filtrer" icon="i-heroicons-funnel" :class="primaryButtonClass" />
    </div>
  </form>
</template>

<script lang="ts" setup>
import type { Ref } from 'vue'
import { buildLocalBusinessFilterStatusSelectItems } from '#src-core/constants/localBusinessSelectableStatuses'
import type { LocalBusinessStatus } from '#src-core/types/enums/local-business.enums'
import {
  buildLocalBusinessOsmTypeFilterItems,
  type LocalBusinessOsmTypeSelectItem,
} from '#src-core/constants/localBusinessOsmTypeLabels'
import type { ListLocalBusinessProspectsQuery } from '#src-core/types/payload/local-business.types'
import { isFavoriteOnlyFilter } from '#src-core/utils/queryFilters'
import { useAlyvoDarkUi } from '#src-nuxt/app/composables/useAlyvoDarkUi'

/**
 * Evenements du formulaire de filtres business locaux.
 */
type LocalBusinessFiltersEmits = {
  submit: [ListLocalBusinessProspectsQuery]
}

/**
 * Signature de l'emetteur.
 */
type LocalBusinessFiltersEmit = (event: 'submit', query: ListLocalBusinessProspectsQuery) => void

/**
 * Item de liste deroulante.
 */
type SelectItem = {
  label: string
  value: string
}

const emit: LocalBusinessFiltersEmit = defineEmits<LocalBusinessFiltersEmits>()

const ALL: string = '__all__'
const { inputUi, selectUi, primaryButtonClass, ghostButtonClass } = useAlyvoDarkUi()

const search: Ref<string> = ref('')
const city: Ref<string> = ref('')
const status: Ref<string> = ref(ALL)
const favorite: Ref<string> = ref(ALL)
const category: Ref<string> = ref(ALL)
const hasWebsite: Ref<string> = ref(ALL)
const seoScoreMax: Ref<string> = ref(ALL)

const statusItems: SelectItem[] = [
  { label: 'Tous les statuts', value: ALL },
  ...buildLocalBusinessFilterStatusSelectItems().map(
    (item: { label: string; value: LocalBusinessStatus }): SelectItem => ({
      label: item.label,
      value: item.value,
    }),
  ),
]

const categoryItems: SelectItem[] = [
  { label: 'Tous les types', value: ALL },
  ...buildLocalBusinessOsmTypeFilterItems().map(
    (item: LocalBusinessOsmTypeSelectItem): SelectItem => ({
      label: item.label,
      value: item.value,
    }),
  ),
]

const favoriteItems: SelectItem[] = [
  { label: 'Tous les business', value: ALL },
  { label: 'Favoris uniquement', value: 'true' },
]

const websiteItems: SelectItem[] = [
  { label: 'Site web (tous)', value: ALL },
  { label: 'Avec site web', value: 'true' },
  { label: 'Sans site web', value: 'false' },
]

const seoScoreItems: SelectItem[] = [
  { label: 'Score SEO (tous)', value: ALL },
  { label: 'SEO ≤ 40 (a refaire)', value: '40' },
  { label: 'SEO ≤ 60 (moyen)', value: '60' },
  { label: 'SEO ≤ 80 (bon)', value: '80' },
]

/**
 * Construit le payload de filtres (cles retirees quand valeur "tous").
 * @returns {ListLocalBusinessProspectsQuery} Query pour l'API.
 */
const buildFilterQuery: () => ListLocalBusinessProspectsQuery = (): ListLocalBusinessProspectsQuery => ({
  page: 1,
  search: search.value.trim() || undefined,
  city: city.value.trim() || undefined,
  status: status.value && status.value !== ALL ? [status.value as LocalBusinessStatus] : undefined,
  isFavorite: isFavoriteOnlyFilter(favorite.value) ? true : undefined,
  category: category.value && category.value !== ALL ? category.value : undefined,
  hasWebsite: hasWebsite.value === 'true' ? true : hasWebsite.value === 'false' ? false : undefined,
  seoScoreMax: seoScoreMax.value && seoScoreMax.value !== ALL ? Number(seoScoreMax.value) : undefined,
})

/**
 * Construit le payload de filtres et emet submit.
 * @returns {void}
 */
const submit: () => void = (): void => {
  emit('submit', buildFilterQuery())
}

/**
 * Reinitialise les filtres et recharge sans filtre.
 * @returns {void}
 */
const reset: () => void = (): void => {
  search.value = ''
  city.value = ''
  status.value = ALL
  favorite.value = ALL
  category.value = ALL
  hasWebsite.value = ALL
  seoScoreMax.value = ALL
  emit('submit', buildFilterQuery())
}
</script>
