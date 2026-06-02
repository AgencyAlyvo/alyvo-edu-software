import { defineStore } from 'pinia'
import type { Ref } from 'vue'
import { WeeklyObjectiveApiService } from '#src-core/services/WeeklyObjectiveApiService'
import type { WeeklyObjective, WeeklyObjectiveResponse } from '#src-core/types/response/weekly.types'

/**
 * Store objectif hebdomadaire expose.
 */
type WeeklyObjectiveStore = {
  current: WeeklyObjective | undefined
  isLoading: boolean
  fetchCurrent: () => Promise<void>
}

/**
 * Store setup objectif hebdomadaire.
 */
type WeeklyObjectiveStoreSetup = {
  current: Ref<WeeklyObjective | undefined>
  isLoading: Ref<boolean>
  fetchCurrent: () => Promise<void>
}

/**
 * Type callable du store objectif.
 */
type UseWeeklyObjectiveStore = () => WeeklyObjectiveStore

export const useWeeklyObjectiveStore: UseWeeklyObjectiveStore = defineStore(
  'weeklyObjective',
  (): WeeklyObjectiveStoreSetup => {
    const current: Ref<WeeklyObjective | undefined> = ref(undefined)
    const isLoading: Ref<boolean> = ref(false)

    /**
     * Charge l'objectif courant.
     * @returns {Promise<void>}
     */
    const fetchCurrent: () => Promise<void> = async (): Promise<void> => {
      isLoading.value = true
      try {
        const response: WeeklyObjectiveResponse = await WeeklyObjectiveApiService.getCurrent()
        current.value = response.data
      } finally {
        isLoading.value = false
      }
    }

    return { current, isLoading, fetchCurrent }
  },
)
