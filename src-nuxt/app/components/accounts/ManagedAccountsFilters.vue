<template>
  <form
    class="grid gap-3 rounded-lg border border-[#2f3d67] bg-[#0b1433]/70 p-4 md:grid-cols-[1fr_auto] md:items-end"
    @submit.prevent="applyFilters"
  >
    <AlyvoListFilterField label="Filtre d'affichage" hint="Affine la liste des comptes gérés">
      <USelect
        v-model="localFilter"
        :items="filterItems"
        placeholder="Choisir un filtre"
        variant="none"
        :ui="selectUi"
        class="min-w-[240px]"
      />
    </AlyvoListFilterField>

    <UButton type="submit" icon="i-heroicons-funnel" label="Filtrer" :class="primaryButtonClass" class="h-11" />
  </form>
</template>

<script lang="ts" setup>
import type { Ref } from 'vue'

import type { ManagedAccountFilter } from '#src-core/types/payload/managed-accounts.types'

import AlyvoListFilterField from '#src-nuxt/app/components/ui/AlyvoListFilterField.vue'
import { useAlyvoDarkUi } from '#src-nuxt/app/composables/useAlyvoDarkUi'

/**
 *
 */
type SelectItem = {
  label: string
  value: ManagedAccountFilter
}

/**
 *
 */
type ManagedAccountsFiltersEmits = {
  submit: [filter: ManagedAccountFilter]
}

/**
 *
 */
type ManagedAccountsFiltersEmit = (event: 'submit', filter: ManagedAccountFilter) => void

const emit: ManagedAccountsFiltersEmit = defineEmits<ManagedAccountsFiltersEmits>()

const { selectUi, primaryButtonClass } = useAlyvoDarkUi()

const filterItems: SelectItem[] = [
  { label: 'Tous les comptes', value: 'all' },
  { label: 'École activée', value: 'school_active' },
  { label: 'École inactive', value: 'school_inactive' },
  { label: 'Cursor activé', value: 'cursor_active' },
  { label: 'Cursor inactif', value: 'cursor_inactive' },
]

const localFilter: Ref<ManagedAccountFilter> = ref('all')

/**
 * Emet le filtre selectionne.
 */
const applyFilters: () => void = (): void => {
  emit('submit', localFilter.value)
}
</script>
