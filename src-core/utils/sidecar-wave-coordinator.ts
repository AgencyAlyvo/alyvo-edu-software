const WAVE_SLOT_POLL_MS: number = 300

let activeSidecarSlots: number = 0

/**
 * Reinitialise le compteur de sidecars actifs (debut de lot UI).
 * @returns {void}
 */
export function resetSidecarWaveCoordinator(): void {
  activeSidecarSlots = 0
}

/**
 * @returns {number} Nombre de sidecars Chrome encore actifs.
 */
export function getActiveSidecarSlotCount(): number {
  return activeSidecarSlots
}

/**
 * Enregistre le demarrage d'un sidecar Chrome (mode multi-instance).
 * @param {number} maxConcurrent - Limite de concurrence configuree.
 * @returns {void}
 */
export function acquireSidecarWaveSlot(maxConcurrent: number): void {
  if (maxConcurrent <= 1) {
    return
  }

  activeSidecarSlots += 1
}

/**
 * Libere un slot sidecar a la fin du traitement d'un compte.
 * @param {number} maxConcurrent - Limite de concurrence configuree.
 * @returns {void}
 */
export function releaseSidecarWaveSlot(maxConcurrent: number): void {
  if (maxConcurrent <= 1) {
    return
  }

  activeSidecarSlots = Math.max(0, activeSidecarSlots - 1)
}

/**
 * Attend que tous les sidecars de la vague precedente aient libere leur slot.
 * @returns {Promise<void>}
 */
export async function waitForNoActiveSidecarSlots(): Promise<void> {
  while (activeSidecarSlots > 0) {
    await new Promise<void>((resolve: (value: void) => void) => {
      setTimeout(resolve, WAVE_SLOT_POLL_MS)
    })
  }
}
