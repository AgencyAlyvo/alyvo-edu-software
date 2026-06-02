<template>
  <div class="flex flex-col items-center gap-3 sm:flex-row sm:items-center sm:justify-between">
    <p class="text-xs text-[#9ba3bd]">
      Page {{ currentPage }} / {{ displayTotalPages }} - {{ total }} {{ totalLabel }}
    </p>
    <nav class="flex shrink-0 items-center gap-1 sm:ml-auto" :aria-label="navAriaLabel">
      <button
        type="button"
        :disabled="currentPage <= 1"
        :class="pageButtonClass"
        aria-label="Page precedente"
        @click="emit('change', currentPage - 1)"
      >
        <UIcon name="i-heroicons-chevron-left" class="h-4 w-4" />
      </button>
      <template v-for="(page, index) in navVisiblePages" :key="`${page}-${index}`">
        <span v-if="page === 'ellipsis'" class="px-2 text-sm font-semibold text-[#69759b]">...</span>
        <button
          v-else
          type="button"
          :class="page === currentPage ? activePageButtonClass : pageButtonClass"
          @click="emit('change', page)"
        >
          {{ page }}
        </button>
      </template>
      <button
        type="button"
        :disabled="currentPage >= displayTotalPages"
        :class="pageButtonClass"
        aria-label="Page suivante"
        @click="emit('change', currentPage + 1)"
      >
        <UIcon name="i-heroicons-chevron-right" class="h-4 w-4" />
      </button>
    </nav>
  </div>
</template>

<script lang="ts" setup>
import type { VisiblePage } from '#src-nuxt/app/composables/useServerPagination'

/**
 * Props de la barre de pagination serveur.
 */
type ServerPaginationNavProps = {
  currentPage: number
  totalPages: number
  total: number
  totalLabel: string
  visiblePages: VisiblePage[]
  pageButtonClass: string
  activePageButtonClass: string
  navAriaLabel: string
}

/**
 * Evenements de pagination.
 */
type ServerPaginationNavEmits = {
  change: [page: number]
}

const props: ServerPaginationNavProps = defineProps<ServerPaginationNavProps>()
const emit: (event: 'change', page: number) => void = defineEmits<ServerPaginationNavEmits>()

/** Nombre de pages affiche (minimum 1 pour « Page 1 / 1 »). */
const displayTotalPages: ComputedRef<number> = computed((): number => Math.max(props.totalPages, 1))

/** Boutons de page affiches (au moins la page 1). */
const navVisiblePages: ComputedRef<VisiblePage[]> = computed((): VisiblePage[] => {
  if (props.visiblePages.length > 0) {
    return props.visiblePages
  }

  return [1]
})
</script>
