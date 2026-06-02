import type { ComputedRef, Ref } from 'vue'
import { useAlyvoDarkUi } from '#src-nuxt/app/composables/useAlyvoDarkUi'

/**
 * Entree de navigation pagination (numero ou ellipse).
 */
export type VisiblePage = number | 'ellipsis'

/**
 * Options du composable de pagination serveur.
 */
type UseServerPaginationOptions = {
  perPage?: number
  fetchPage: (page: number) => Promise<void>
  getTotalPages: () => number
  getCurrentPageFromMeta?: () => number | undefined
}

/**
 * Etat et controles de pagination alignes sur les listes paginees backend.
 * @param {UseServerPaginationOptions} options - Callbacks de chargement et meta.
 * @returns {object} Etat reactif et handlers de pagination.
 */
export const useServerPagination: (options: UseServerPaginationOptions) => {
  perPage: number
  currentPage: Ref<number>
  totalPages: ComputedRef<number>
  visiblePages: ComputedRef<VisiblePage[]>
  pageButtonClass: string
  activePageButtonClass: string
  onPageChange: (page: number) => Promise<void>
  resetToFirstPage: () => void
  syncCurrentPageFromMeta: () => void
} = (
  options: UseServerPaginationOptions,
): {
  perPage: number
  currentPage: Ref<number>
  totalPages: ComputedRef<number>
  visiblePages: ComputedRef<VisiblePage[]>
  pageButtonClass: string
  activePageButtonClass: string
  onPageChange: (page: number) => Promise<void>
  resetToFirstPage: () => void
  syncCurrentPageFromMeta: () => void
} => {
  const perPage: number = options.perPage ?? 50
  const currentPage: Ref<number> = ref(1)
  const { pageButtonClass, activePageButtonClass } = useAlyvoDarkUi()

  const totalPages: ComputedRef<number> = computed((): number => options.getTotalPages() || 1)

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
   * Synchronise la page courante avec les meta renvoyees par l'API.
   * @returns {void}
   */
  const syncCurrentPageFromMeta: () => void = (): void => {
    const fromMeta: number | undefined = options.getCurrentPageFromMeta?.()
    if (fromMeta) {
      currentPage.value = fromMeta
    }
  }

  /**
   * Reinitialise la pagination sur la premiere page.
   * @returns {void}
   */
  const resetToFirstPage: () => void = (): void => {
    currentPage.value = 1
  }

  /**
   * Charge une page serveur.
   * @param {number} page - Numero de page demande.
   * @returns {Promise<void>}
   */
  const onPageChange: (page: number) => Promise<void> = async (page: number): Promise<void> => {
    if (page < 1 || page > totalPages.value || page === currentPage.value) {
      return
    }

    currentPage.value = page
    await options.fetchPage(page)
    syncCurrentPageFromMeta()
  }

  return {
    perPage,
    currentPage,
    totalPages,
    visiblePages,
    pageButtonClass,
    activePageButtonClass,
    onPageChange,
    resetToFirstPage,
    syncCurrentPageFromMeta,
  }
}
