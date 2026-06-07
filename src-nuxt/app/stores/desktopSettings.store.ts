import { defineStore } from 'pinia'
import type { Ref } from 'vue'

import {
  DEFAULT_CAPSOLVER_API_KEY,
  DEFAULT_WINDSCRIBE_CLI_PATH,
  DEFAULT_WINDSCRIBE_LOCATION,
  DESKTOP_SETTINGS_STORAGE_KEYS,
} from '#src-core/constants/desktop-settings.constants'

/**
 * Etat expose par le store des parametres desktop.
 */
type DesktopSettingsStore = {
  windscribeCliPath: string
  windscribeLocation: string
  capsolverApiKey: string
  savedMessage: string | null
  load: () => void
  save: () => void
  resetToDefaults: () => void
  isVpnRotationConfigured: boolean
  isCapSolverConfigured: boolean
}

/**
 * Setup Pinia du store parametres desktop.
 */
type DesktopSettingsStoreSetup = {
  windscribeCliPath: Ref<string>
  windscribeLocation: Ref<string>
  capsolverApiKey: Ref<string>
  savedMessage: Ref<string | null>
  load: () => void
  save: () => void
  resetToDefaults: () => void
  isVpnRotationConfigured: Ref<boolean>
  isCapSolverConfigured: Ref<boolean>
}

/**
 * Hook Pinia parametres desktop.
 */
type UseDesktopSettingsStore = () => DesktopSettingsStore

export const useDesktopSettingsStore: UseDesktopSettingsStore = defineStore(
  'desktopSettings',
  (): DesktopSettingsStoreSetup => {
    const windscribeCliPath: Ref<string> = ref(DEFAULT_WINDSCRIBE_CLI_PATH)
    const windscribeLocation: Ref<string> = ref(DEFAULT_WINDSCRIBE_LOCATION)
    const capsolverApiKey: Ref<string> = ref(DEFAULT_CAPSOLVER_API_KEY)
    const savedMessage: Ref<string | null> = ref(null)

    const isVpnRotationConfigured: Ref<boolean> = computed((): boolean => {
      return windscribeCliPath.value.trim().length > 0
    })

    const isCapSolverConfigured: Ref<boolean> = computed((): boolean => {
      return capsolverApiKey.value.trim().length > 0
    })

    /**
     * Charge les parametres depuis localStorage.
     * @returns {void}
     */
    const load: () => void = (): void => {
      if (!import.meta.client) {
        return
      }

      const storedPath: string | null = localStorage.getItem(DESKTOP_SETTINGS_STORAGE_KEYS.windscribeCliPath)
      const storedLocation: string | null = localStorage.getItem(DESKTOP_SETTINGS_STORAGE_KEYS.windscribeLocation)
      const storedCapSolver: string | null = localStorage.getItem(DESKTOP_SETTINGS_STORAGE_KEYS.capsolverApiKey)

      windscribeCliPath.value = storedPath?.trim() || DEFAULT_WINDSCRIBE_CLI_PATH
      windscribeLocation.value = storedLocation?.trim() || DEFAULT_WINDSCRIBE_LOCATION
      capsolverApiKey.value = storedCapSolver?.trim() || DEFAULT_CAPSOLVER_API_KEY
    }

    /**
     * Persiste les parametres dans localStorage.
     * @returns {void}
     */
    const save: () => void = (): void => {
      if (!import.meta.client) {
        return
      }

      localStorage.setItem(DESKTOP_SETTINGS_STORAGE_KEYS.windscribeCliPath, windscribeCliPath.value.trim())
      localStorage.setItem(DESKTOP_SETTINGS_STORAGE_KEYS.windscribeLocation, windscribeLocation.value.trim())
      localStorage.setItem(DESKTOP_SETTINGS_STORAGE_KEYS.capsolverApiKey, capsolverApiKey.value.trim())
      savedMessage.value = 'Parametres enregistres.'
    }

    /**
     * Reinitialise les valeurs par defaut puis enregistre.
     * @returns {void}
     */
    const resetToDefaults: () => void = (): void => {
      windscribeCliPath.value = DEFAULT_WINDSCRIBE_CLI_PATH
      windscribeLocation.value = DEFAULT_WINDSCRIBE_LOCATION
      capsolverApiKey.value = DEFAULT_CAPSOLVER_API_KEY
      save()
    }

    return {
      windscribeCliPath,
      windscribeLocation,
      capsolverApiKey,
      savedMessage,
      load,
      save,
      resetToDefaults,
      isVpnRotationConfigured,
      isCapSolverConfigured,
    }
  },
)
