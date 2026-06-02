import { computed, onBeforeUnmount, ref, watch } from 'vue'
import type { ComputedRef, Ref } from 'vue'

/**
 * Options de virtualisation.
 */
export type UseVirtualListOptions<T> = {
  items: Ref<readonly T[]> | ComputedRef<readonly T[]>
  rowHeight: number
  containerRef: Ref<HTMLElement | null | undefined>
  overscan?: number
}

/**
 * Resultat d'une virtualisation : fenetre rendue + dimensions totales.
 */
export type UseVirtualListResult<T> = {
  visibleItems: ComputedRef<readonly { item: T; index: number; top: number }[]>
  totalHeight: ComputedRef<number>
  spacerTop: ComputedRef<number>
  spacerBottom: ComputedRef<number>
  scrollToIndex: (index: number, behavior?: ScrollBehavior) => void
}

/**
 * Virtualise une liste a hauteur de ligne fixe : seules les rangees visibles
 * (+ overscan) sont rendues dans le DOM, peu importe la taille du tableau.
 *
 * Pourquoi : Vue/Nuxt UI ecroulent le main thread des qu'on monte plusieurs
 * milliers de composants (USelect, UTooltip, UButton) en meme temps. Avec
 * virtualisation, le nombre de composants montes est plafonne au nombre de
 * lignes visibles + overscan (~30 max sur un ecran standard).
 * @param {UseVirtualListOptions<T>} options - Options de virtualisation.
 * @template T
 * @returns {UseVirtualListResult<T>} API de la liste virtualisee.
 */
export function useVirtualList<T>(options: UseVirtualListOptions<T>): UseVirtualListResult<T> {
  const overscan: number = options.overscan ?? 6
  const scrollTop: Ref<number> = ref(0)
  const viewportHeight: Ref<number> = ref(0)

  /**
   * Met a jour la fenetre visible a partir du scroll.
   * @returns {void}
   */
  const handleScroll: () => void = (): void => {
    const el: HTMLElement | null | undefined = options.containerRef.value
    if (!el) return
    scrollTop.value = el.scrollTop
  }

  /**
   * Met a jour la hauteur visible du conteneur.
   * @returns {void}
   */
  const handleResize: () => void = (): void => {
    const el: HTMLElement | null | undefined = options.containerRef.value
    if (!el) return
    viewportHeight.value = el.clientHeight
  }

  let resizeObserver: ResizeObserver | undefined
  let attached: HTMLElement | undefined

  /**
   * Detache les listeners du conteneur courant.
   * @returns {void}
   */
  const detach: () => void = (): void => {
    if (attached) {
      attached.removeEventListener('scroll', handleScroll)
      attached = undefined
    }
    resizeObserver?.disconnect()
    resizeObserver = undefined
  }

  /**
   * Attache les listeners au conteneur passe en parametre.
   * @param {HTMLElement} el - Conteneur scrollable.
   * @returns {void}
   */
  const attach: (el: HTMLElement) => void = (el: HTMLElement): void => {
    detach()
    attached = el
    el.addEventListener('scroll', handleScroll, { passive: true })
    scrollTop.value = el.scrollTop
    viewportHeight.value = el.clientHeight
    if (typeof ResizeObserver !== 'undefined') {
      resizeObserver = new ResizeObserver(handleResize)
      resizeObserver.observe(el)
    } else if (typeof window !== 'undefined') {
      window.addEventListener('resize', handleResize)
    }
  }

  watch(
    options.containerRef,
    (el: HTMLElement | null | undefined): void => {
      if (el) {
        attach(el)
      } else {
        detach()
      }
    },
    { immediate: true, flush: 'post' },
  )

  watch(options.items, (): void => {
    handleResize()
  })

  onBeforeUnmount((): void => {
    detach()
    if (typeof window !== 'undefined' && typeof ResizeObserver === 'undefined') {
      window.removeEventListener('resize', handleResize)
    }
  })

  const totalHeight: ComputedRef<number> = computed((): number => options.items.value.length * options.rowHeight)

  const visibleRange: ComputedRef<{ start: number; end: number }> = computed((): { start: number; end: number } => {
    const itemCount: number = options.items.value.length
    if (itemCount === 0) {
      return { start: 0, end: 0 }
    }
    const vh: number = viewportHeight.value || 600
    const firstVisible: number = Math.floor(scrollTop.value / options.rowHeight)
    const lastVisible: number = Math.ceil((scrollTop.value + vh) / options.rowHeight)
    const start: number = Math.max(0, firstVisible - overscan)
    const end: number = Math.min(itemCount, lastVisible + overscan)
    return { start, end }
  })

  const visibleItems: ComputedRef<readonly { item: T; index: number; top: number }[]> = computed(
    (): readonly { item: T; index: number; top: number }[] => {
      const range: { start: number; end: number } = visibleRange.value
      const items: readonly T[] = options.items.value
      const result: { item: T; index: number; top: number }[] = []
      for (let i: number = range.start; i < range.end; i++) {
        const item: T | undefined = items[i]
        if (item === undefined) continue
        result.push({ item, index: i, top: i * options.rowHeight })
      }
      return result
    },
  )

  const spacerTop: ComputedRef<number> = computed((): number => visibleRange.value.start * options.rowHeight)
  const spacerBottom: ComputedRef<number> = computed((): number => {
    const total: number = options.items.value.length
    return Math.max(0, (total - visibleRange.value.end) * options.rowHeight)
  })

  /**
   * Scrolle jusqu'a un index donne.
   * @param {number} index - Index a afficher.
   * @param {ScrollBehavior | undefined} behavior - Mode de scroll.
   * @returns {void}
   */
  const scrollToIndex: (index: number, behavior?: ScrollBehavior) => void = (
    index: number,
    behavior: ScrollBehavior = 'auto',
  ): void => {
    const el: HTMLElement | null | undefined = options.containerRef.value
    if (!el) return
    const safeIndex: number = Math.max(0, Math.min(options.items.value.length - 1, index))
    el.scrollTo({ top: safeIndex * options.rowHeight, behavior })
  }

  return { visibleItems, totalHeight, spacerTop, spacerBottom, scrollToIndex }
}
