import { defineStore } from 'pinia'
import type { Ref } from 'vue'
import { LinkedinStatsApiService } from '#src-core/services/LinkedinStatsApiService'
import { LocalBusinessStatsApiService } from '#src-core/services/LocalBusinessStatsApiService'
import type { LinkedinStatsQuery, LocalBusinessStatsQuery } from '#src-core/types/payload/stats.types'
import type {
  LinkedinStats,
  LinkedinStatsResponse,
  LocalBusinessStats,
  LocalBusinessStatsResponse,
} from '#src-core/types/response/stats.types'

/**
 * Store statistiques expose.
 */
type StatsStore = {
  linkedinStats: LinkedinStats | undefined
  localBusinessStats: LocalBusinessStats | undefined
  isLoading: boolean
  isLocalBusinessLoading: boolean
  fetchLinkedin: (query?: LinkedinStatsQuery) => Promise<void>
  fetchLocalBusiness: (query?: LocalBusinessStatsQuery) => Promise<void>
}

/**
 * Store setup statistiques.
 */
type StatsStoreSetup = {
  linkedinStats: Ref<LinkedinStats | undefined>
  localBusinessStats: Ref<LocalBusinessStats | undefined>
  isLoading: Ref<boolean>
  isLocalBusinessLoading: Ref<boolean>
  fetchLinkedin: (query?: LinkedinStatsQuery) => Promise<void>
  fetchLocalBusiness: (query?: LocalBusinessStatsQuery) => Promise<void>
}

/**
 * Type callable du store statistiques.
 */
type UseStatsStore = () => StatsStore

export const useStatsStore: UseStatsStore = defineStore('stats', (): StatsStoreSetup => {
  const linkedinStats: Ref<LinkedinStats | undefined> = ref(undefined)
  const localBusinessStats: Ref<LocalBusinessStats | undefined> = ref(undefined)
  const isLoading: Ref<boolean> = ref(false)
  const isLocalBusinessLoading: Ref<boolean> = ref(false)

  /**
   * Charge les stats LinkedIn.
   * @param {LinkedinStatsQuery} [query] - Filtre de periode optionnel.
   * @returns {Promise<void>}
   */
  const fetchLinkedin: (query?: LinkedinStatsQuery) => Promise<void> = async (
    query?: LinkedinStatsQuery,
  ): Promise<void> => {
    isLoading.value = true
    try {
      const response: LinkedinStatsResponse = await LinkedinStatsApiService.linkedin(query)
      linkedinStats.value = response.data
    } finally {
      isLoading.value = false
    }
  }

  /**
   * Charge les stats business locaux.
   * @param {LocalBusinessStatsQuery} [query] - Filtre de periode optionnel.
   * @returns {Promise<void>}
   */
  const fetchLocalBusiness: (query?: LocalBusinessStatsQuery) => Promise<void> = async (
    query?: LocalBusinessStatsQuery,
  ): Promise<void> => {
    isLocalBusinessLoading.value = true
    try {
      const response: LocalBusinessStatsResponse = await LocalBusinessStatsApiService.localBusiness(query)
      localBusinessStats.value = response.data
    } finally {
      isLocalBusinessLoading.value = false
    }
  }

  return {
    linkedinStats,
    localBusinessStats,
    isLoading,
    isLocalBusinessLoading,
    fetchLinkedin,
    fetchLocalBusiness,
  }
})
