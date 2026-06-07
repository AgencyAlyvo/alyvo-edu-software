/**
 * Message lisible pour toute valeur lancee en erreur (Tauri, fetch, etc.).
 * @param {unknown} error - Erreur ou valeur rejetee.
 * @returns {string} Message exploitable par l'interface.
 */
export function formatErrorMessage(error: unknown): string {
  if (error instanceof Error) {
    return error.message
  }

  if (typeof error === 'string') {
    return error
  }

  if (typeof error === 'object' && error !== null) {
    const record: Record<string, unknown> = error as Record<string, unknown>

    if (typeof record.message === 'string') {
      return record.message
    }

    try {
      return JSON.stringify(error)
    } catch {
      return String(error)
    }
  }

  return String(error)
}
