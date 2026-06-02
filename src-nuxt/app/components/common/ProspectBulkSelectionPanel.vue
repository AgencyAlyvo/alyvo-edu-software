<template>
  <aside
    v-if="selectedCount > 0"
    class="flex w-52 shrink-0 flex-col gap-3 rounded-lg border border-[#2f3d67] bg-[#0b1433]/90 p-4"
    aria-label="Actions sur la selection"
  >
    <div>
      <p class="text-xs font-semibold tracking-[0.15em] text-[#9a65d5] uppercase">Selection</p>
      <p class="mt-1 text-lg font-semibold text-white">{{ selectedCount }}</p>
      <p class="text-xs text-[#9ba3bd]">element(s) selectionne(s)</p>
    </div>

    <div class="flex flex-col gap-2">
      <UButton
        size="sm"
        icon="i-heroicons-star"
        label="Mettre en favoris"
        :loading="loading"
        :class="actionButtonClass"
        @click="emit('favorite')"
      />
      <UButton
        size="sm"
        icon="i-heroicons-star"
        label="Retirer des favoris"
        :loading="loading"
        variant="ghost"
        :class="ghostButtonClass"
        @click="emit('unfavorite')"
      />
      <UButton
        size="sm"
        icon="i-heroicons-trash"
        label="Supprimer"
        :loading="loading"
        variant="ghost"
        :class="dangerGhostButtonClass"
        @click="emit('delete')"
      />
    </div>

    <div class="mt-auto flex flex-col gap-1 border-t border-[#2f3d67] pt-3">
      <UButton
        size="xs"
        variant="ghost"
        label="Tout cocher (page)"
        :class="ghostButtonClass"
        @click="emit('selectPage')"
      />
      <UButton size="xs" variant="ghost" label="Tout deselectionner" :class="ghostButtonClass" @click="emit('clear')" />
    </div>
  </aside>
</template>

<script lang="ts" setup>
import { useAlyvoDarkUi } from '#src-nuxt/app/composables/useAlyvoDarkUi'

/**
 * Props du panneau d'actions groupées.
 */
type ProspectBulkSelectionPanelProps = {
  selectedCount: number
  loading?: boolean
}

/**
 * Evenements du panneau d'actions groupées.
 */
type ProspectBulkSelectionPanelEmits = {
  favorite: []
  unfavorite: []
  delete: []
  selectPage: []
  clear: []
}

/**
 * Signature de l'emetteur.
 */
type ProspectBulkSelectionPanelEmit = {
  (event: 'favorite'): void
  (event: 'unfavorite'): void
  (event: 'delete'): void
  (event: 'selectPage'): void
  (event: 'clear'): void
}

defineProps<ProspectBulkSelectionPanelProps>()
const emit: ProspectBulkSelectionPanelEmit = defineEmits<ProspectBulkSelectionPanelEmits>()

const { ghostButtonClass, dangerGhostButtonClass } = useAlyvoDarkUi()

const actionButtonClass: string =
  'justify-start rounded-md bg-[linear-gradient(135deg,#102766_0%,#7446a6_100%)] px-3 py-2 text-sm font-semibold text-white'
</script>
