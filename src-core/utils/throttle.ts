/**
 * Retourne une version throttlee d'une fonction (dernier appel garanti).
 * @template T
 * @param {T} fn - Fonction a limiter.
 * @param {number} waitMs - Delai minimum entre deux executions.
 * @returns {T} Fonction throttlee.
 */
export function throttle<T extends (...args: never[]) => void>(fn: T, waitMs: number): T {
  let lastRunAt: number = 0
  let timeoutId: ReturnType<typeof setTimeout> | undefined

  /**
   * Version throttlee de la fonction d'origine.
   * @param {...Parameters<T>} args - Arguments de la fonction source.
   * @returns {void}
   */
  function throttled(...args: Parameters<T>): void {
    const now: number = Date.now()
    const elapsed: number = now - lastRunAt

    /**
     * Execute la fonction source avec les arguments en attente.
     * @returns {void}
     */
    function run(): void {
      lastRunAt = Date.now()
      fn(...args)
    }

    if (elapsed >= waitMs) {
      if (timeoutId !== undefined) {
        clearTimeout(timeoutId)
        timeoutId = undefined
      }
      run()
      return
    }

    if (timeoutId !== undefined) {
      clearTimeout(timeoutId)
    }
    timeoutId = setTimeout(function onThrottleDelay(): void {
      timeoutId = undefined
      run()
    }, waitMs - elapsed)
  }

  return throttled as T
}
