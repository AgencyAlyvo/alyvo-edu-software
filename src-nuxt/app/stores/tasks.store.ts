import { defineStore } from 'pinia'
import type { Ref } from 'vue'
import { LinkedinProspectApiService } from '#src-core/services/LinkedinProspectApiService'
import type { DueRelance, DueRelancesListResponse } from '#src-core/types/response/relances.types'

/**
 * Store des relances LinkedIn dues expose.
 */
type TasksStore = {
  dueRelances: DueRelance[]
  isLoading: boolean
  fetchDue: () => Promise<void>
}

/**
 * Store setup des relances LinkedIn dues.
 */
type TasksStoreSetup = {
  dueRelances: Ref<DueRelance[]>
  isLoading: Ref<boolean>
  fetchDue: () => Promise<void>
}

/**
 * Type callable du store de relances LinkedIn.
 */
type UseTasksStore = () => TasksStore

export const useTasksStore: UseTasksStore = defineStore('tasks', (): TasksStoreSetup => {
  const dueRelances: Ref<DueRelance[]> = ref([])
  const isLoading: Ref<boolean> = ref(false)

  /**
   * Charge les relances LinkedIn dues.
   * @returns {Promise<void>}
   */
  const fetchDue: () => Promise<void> = async (): Promise<void> => {
    isLoading.value = true
    try {
      const response: DueRelancesListResponse | DueRelance[] = await LinkedinProspectApiService.dueRelances()
      if (Array.isArray(response)) {
        dueRelances.value = response
      } else if (Array.isArray(response.data)) {
        dueRelances.value = response.data
      } else {
        dueRelances.value = []
      }
    } finally {
      isLoading.value = false
    }
  }

  return { dueRelances, isLoading, fetchDue }
})
