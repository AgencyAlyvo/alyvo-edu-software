import { defineStore } from 'pinia'
import type { Ref } from 'vue'
import { UserSettingsApiService } from '#src-core/services/UserSettingsApiService'
import type { UpdateUserSettingsPayload } from '#src-core/types/payload/settings.types'
import type { UserSettings, UserSettingsResponse } from '#src-core/types/response/settings.types'

/**
 * Store parametres expose.
 */
type UserSettingsStore = {
  settings: UserSettings | undefined
  isLoading: boolean
  fetch: () => Promise<void>
  update: (payload: UpdateUserSettingsPayload) => Promise<void>
}

/**
 * Store setup parametres.
 */
type UserSettingsStoreSetup = {
  settings: Ref<UserSettings | undefined>
  isLoading: Ref<boolean>
  fetch: () => Promise<void>
  update: (payload: UpdateUserSettingsPayload) => Promise<void>
}

/**
 * Type callable du store parametres.
 */
type UseUserSettingsStore = () => UserSettingsStore

export const useUserSettingsStore: UseUserSettingsStore = defineStore('userSettings', (): UserSettingsStoreSetup => {
  const settings: Ref<UserSettings | undefined> = ref(undefined)
  const isLoading: Ref<boolean> = ref(false)

  /**
   * Charge les parametres.
   * @returns {Promise<void>}
   */
  const fetch: () => Promise<void> = async (): Promise<void> => {
    isLoading.value = true
    try {
      const response: UserSettingsResponse = await UserSettingsApiService.get()
      settings.value = response.data
    } finally {
      isLoading.value = false
    }
  }

  /**
   * Met a jour les parametres.
   * @param {UpdateUserSettingsPayload} payload - Donnees partielles.
   * @returns {Promise<void>}
   */
  const update: (payload: UpdateUserSettingsPayload) => Promise<void> = async (
    payload: UpdateUserSettingsPayload,
  ): Promise<void> => {
    const response: UserSettingsResponse = await UserSettingsApiService.update(payload)
    settings.value = response.data
  }

  return { settings, isLoading, fetch, update }
})
