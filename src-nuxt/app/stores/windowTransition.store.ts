import { defineStore } from 'pinia'
import type { Ref } from 'vue'

/**
 * Etat et actions exposes par le store de transition fenetre.
 */
type WindowTransitionStore = {
  isLoading: boolean
  setLoading: (value: boolean) => void
}

/**
 * Etat et actions retournes par le setup store avant unwrap Pinia.
 */
type WindowTransitionStoreSetup = {
  isLoading: Ref<boolean>
  setLoading: (value: boolean) => void
}

/**
 * Definition callable du store de transition fenetre.
 */
type UseWindowTransitionStore = () => WindowTransitionStore

/**
 * Store gerant le loader global pendant les transitions de fenetre.
 */
export const useWindowTransitionStore: UseWindowTransitionStore = defineStore(
  'windowTransition',
  (): WindowTransitionStoreSetup => {
    const isLoading: Ref<boolean> = ref(false)

    /**
     * Active ou desactive le loader global.
     * @param {boolean} value - Etat du loader.
     * @returns {void}
     */
    const setLoading: (value: boolean) => void = (value: boolean): void => {
      isLoading.value = value
    }

    return {
      isLoading,
      setLoading,
    }
  },
)
