import type { ComputedRef, Ref } from 'vue'

/**
 * Options du composable de selection par identifiants.
 */
type UseProspectIdSelectionOptions = {
  /**
   * Identifiants presents sur la page / liste courante (pour tout cocher).
   */
  pageIds: Ref<readonly number[]> | ComputedRef<readonly number[]>
}

/**
 * Gere une selection multiple de prospects par identifiant (persiste entre pages).
 * @param {UseProspectIdSelectionOptions} options - Identifiants de la page courante.
 * @returns {object} Etat et actions de selection.
 */
export const useProspectIdSelection: (options: UseProspectIdSelectionOptions) => {
  selectedIds: Ref<Set<number>>
  selectedCount: ComputedRef<number>
  isSelected: (id: number) => boolean
  toggle: (id: number) => void
  selectPage: () => void
  clear: () => void
  allPageSelected: ComputedRef<boolean>
  somePageSelected: ComputedRef<boolean>
  togglePage: () => void
} = (options: UseProspectIdSelectionOptions) => {
  const selectedIds: Ref<Set<number>> = ref(new Set<number>())

  const selectedCount: ComputedRef<number> = computed((): number => selectedIds.value.size)

  /**
   * Indique si un identifiant est selectionne.
   * @param {number} id - Identifiant prospect.
   * @returns {boolean} True si selectionne.
   */
  const isSelected: (id: number) => boolean = (id: number): boolean => selectedIds.value.has(id)

  /**
   * Bascule la selection d'un identifiant.
   * @param {number} id - Identifiant prospect.
   * @returns {void}
   */
  const toggle: (id: number) => void = (id: number): void => {
    const next: Set<number> = new Set(selectedIds.value)
    if (next.has(id)) next.delete(id)
    else next.add(id)
    selectedIds.value = next
  }

  /**
   * Selectionne tous les identifiants de la page courante.
   * @returns {void}
   */
  const selectPage: () => void = (): void => {
    const next: Set<number> = new Set(selectedIds.value)
    for (const id of options.pageIds.value) {
      next.add(id)
    }
    selectedIds.value = next
  }

  /**
   * Vide la selection.
   * @returns {void}
   */
  const clear: () => void = (): void => {
    selectedIds.value = new Set<number>()
  }

  const allPageSelected: ComputedRef<boolean> = computed((): boolean => {
    const ids: readonly number[] = options.pageIds.value
    if (ids.length === 0) return false
    return ids.every((id: number): boolean => selectedIds.value.has(id))
  })

  const somePageSelected: ComputedRef<boolean> = computed((): boolean =>
    options.pageIds.value.some((id: number): boolean => selectedIds.value.has(id)),
  )

  /**
   * Coche ou decoche tous les elements de la page.
   * @returns {void}
   */
  const togglePage: () => void = (): void => {
    if (allPageSelected.value) {
      const next: Set<number> = new Set(selectedIds.value)
      for (const id of options.pageIds.value) {
        next.delete(id)
      }
      selectedIds.value = next
      return
    }
    selectPage()
  }

  return {
    selectedIds,
    selectedCount,
    isSelected,
    toggle,
    selectPage,
    clear,
    allPageSelected,
    somePageSelected,
    togglePage,
  }
}
