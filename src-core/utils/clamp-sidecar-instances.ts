import {
  MAX_SIDECAR_CONCURRENT_INSTANCES,
  MIN_SIDECAR_CONCURRENT_INSTANCES,
} from '#src-core/constants/desktop-settings.constants'

/**
 * Borne un nombre d'instances Chrome entre les limites autorisees.
 * @param {number} value - Valeur saisie ou lue.
 * @returns {number} Entier dans [MIN, MAX].
 */
export function clampSidecarInstances(value: number): number {
  const rounded: number = Math.round(value)

  if (!Number.isFinite(rounded)) {
    return MIN_SIDECAR_CONCURRENT_INSTANCES
  }

  return Math.min(MAX_SIDECAR_CONCURRENT_INSTANCES, Math.max(MIN_SIDECAR_CONCURRENT_INSTANCES, rounded))
}
