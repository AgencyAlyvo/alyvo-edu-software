import { defineStore } from 'pinia'
import type { Ref } from 'vue'

import {
  DEFAULT_BROWARD_ACTIVATION_MAX_CONCURRENT_INSTANCES,
  DEFAULT_BROWARD_ENROLLMENT_MAX_CONCURRENT_INSTANCES,
  DEFAULT_CAPSOLVER_API_KEY,
  DEFAULT_OUTLOOK_MAX_CONCURRENT_INSTANCES,
  DEFAULT_WINDSCRIBE_CLI_PATH,
  DEFAULT_WINDSCRIBE_LOCATION,
  DESKTOP_SETTINGS_STORAGE_KEYS,
} from '#src-core/constants/desktop-settings.constants'
import { clampSidecarInstances } from '#src-core/utils/clamp-sidecar-instances'

/**
 * Etat expose par le store des parametres desktop.
 */
type DesktopSettingsStore = {
  windscribeCliPath: string
  windscribeLocation: string
  capsolverApiKey: string
  outlookMaxConcurrentInstances: number
  browardEnrollmentMaxConcurrentInstances: number
  browardActivationMaxConcurrentInstances: number
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
  outlookMaxConcurrentInstances: Ref<number>
  browardEnrollmentMaxConcurrentInstances: Ref<number>
  browardActivationMaxConcurrentInstances: Ref<number>
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
    const outlookMaxConcurrentInstances: Ref<number> = ref(DEFAULT_OUTLOOK_MAX_CONCURRENT_INSTANCES)
    const browardEnrollmentMaxConcurrentInstances: Ref<number> = ref(
      DEFAULT_BROWARD_ENROLLMENT_MAX_CONCURRENT_INSTANCES,
    )
    const browardActivationMaxConcurrentInstances: Ref<number> = ref(
      DEFAULT_BROWARD_ACTIVATION_MAX_CONCURRENT_INSTANCES,
    )
    const savedMessage: Ref<string | null> = ref(null)

    /**
     * Lit un entier stocke ou la valeur par defaut.
     * @param {string | null} raw - Valeur localStorage.
     * @param {number} fallback - Defaut si invalide.
     * @returns {number} Entier borne.
     */
    const readStoredInstances: (raw: string | null, fallback: number) => number = (
      raw: string | null,
      fallback: number,
    ): number => {
      if (raw === null || raw.trim().length === 0) {
        return fallback
      }

      return clampSidecarInstances(Number.parseInt(raw, 10))
    }

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
      const storedOutlookInstances: string | null = localStorage.getItem(
        DESKTOP_SETTINGS_STORAGE_KEYS.outlookMaxConcurrentInstances,
      )
      const storedBrowardEnrollmentInstances: string | null = localStorage.getItem(
        DESKTOP_SETTINGS_STORAGE_KEYS.browardEnrollmentMaxConcurrentInstances,
      )
      const storedBrowardActivationInstances: string | null = localStorage.getItem(
        DESKTOP_SETTINGS_STORAGE_KEYS.browardActivationMaxConcurrentInstances,
      )

      windscribeCliPath.value = storedPath?.trim() || DEFAULT_WINDSCRIBE_CLI_PATH
      windscribeLocation.value = storedLocation?.trim() || DEFAULT_WINDSCRIBE_LOCATION
      capsolverApiKey.value = storedCapSolver?.trim() || DEFAULT_CAPSOLVER_API_KEY
      outlookMaxConcurrentInstances.value = readStoredInstances(
        storedOutlookInstances,
        DEFAULT_OUTLOOK_MAX_CONCURRENT_INSTANCES,
      )
      browardEnrollmentMaxConcurrentInstances.value = readStoredInstances(
        storedBrowardEnrollmentInstances,
        DEFAULT_BROWARD_ENROLLMENT_MAX_CONCURRENT_INSTANCES,
      )
      browardActivationMaxConcurrentInstances.value = readStoredInstances(
        storedBrowardActivationInstances,
        DEFAULT_BROWARD_ACTIVATION_MAX_CONCURRENT_INSTANCES,
      )
    }

    /**
     * Persiste les parametres dans localStorage.
     * @returns {void}
     */
    const save: () => void = (): void => {
      if (!import.meta.client) {
        return
      }

      outlookMaxConcurrentInstances.value = clampSidecarInstances(outlookMaxConcurrentInstances.value)
      browardEnrollmentMaxConcurrentInstances.value = clampSidecarInstances(
        browardEnrollmentMaxConcurrentInstances.value,
      )
      browardActivationMaxConcurrentInstances.value = clampSidecarInstances(
        browardActivationMaxConcurrentInstances.value,
      )

      localStorage.setItem(DESKTOP_SETTINGS_STORAGE_KEYS.windscribeCliPath, windscribeCliPath.value.trim())
      localStorage.setItem(DESKTOP_SETTINGS_STORAGE_KEYS.windscribeLocation, windscribeLocation.value.trim())
      localStorage.setItem(DESKTOP_SETTINGS_STORAGE_KEYS.capsolverApiKey, capsolverApiKey.value.trim())
      localStorage.setItem(
        DESKTOP_SETTINGS_STORAGE_KEYS.outlookMaxConcurrentInstances,
        String(outlookMaxConcurrentInstances.value),
      )
      localStorage.setItem(
        DESKTOP_SETTINGS_STORAGE_KEYS.browardEnrollmentMaxConcurrentInstances,
        String(browardEnrollmentMaxConcurrentInstances.value),
      )
      localStorage.setItem(
        DESKTOP_SETTINGS_STORAGE_KEYS.browardActivationMaxConcurrentInstances,
        String(browardActivationMaxConcurrentInstances.value),
      )
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
      outlookMaxConcurrentInstances.value = DEFAULT_OUTLOOK_MAX_CONCURRENT_INSTANCES
      browardEnrollmentMaxConcurrentInstances.value = DEFAULT_BROWARD_ENROLLMENT_MAX_CONCURRENT_INSTANCES
      browardActivationMaxConcurrentInstances.value = DEFAULT_BROWARD_ACTIVATION_MAX_CONCURRENT_INSTANCES
      save()
    }

    return {
      windscribeCliPath,
      windscribeLocation,
      capsolverApiKey,
      outlookMaxConcurrentInstances,
      browardEnrollmentMaxConcurrentInstances,
      browardActivationMaxConcurrentInstances,
      savedMessage,
      load,
      save,
      resetToDefaults,
      isVpnRotationConfigured,
      isCapSolverConfigured,
    }
  },
)
