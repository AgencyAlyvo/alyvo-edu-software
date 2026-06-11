/**
 * Resultat d'une tache dans le pool concurrent.
 * - done : continuer la file
 * - abort : ne plus lancer de nouvelles taches (les taches en cours se terminent)
 */
export type ConcurrentPoolWorkerResult = 'done' | 'abort'

/**
 * Execute des taches en parallele avec une limite de concurrence.
 * @param {readonly TItem[]} items - Elements a traiter.
 * @param {number} limit - Nombre max de taches simultanees.
 * @param {() => boolean} shouldStop - Arret externe (ex. bouton Stop).
 * @param {(item: TItem, index: number) => Promise<ConcurrentPoolWorkerResult>} worker - Traitement unitaire.
 * @param {(completed: number, total: number) => void} [onProgress] - Progression apres chaque tache.
 * @returns {Promise<void>}
 */
export async function runConcurrentPool<TItem>(
  items: readonly TItem[],
  limit: number,
  shouldStop: () => boolean,
  worker: (item: TItem, index: number) => Promise<ConcurrentPoolWorkerResult>,
  onProgress?: (completed: number, total: number) => void,
): Promise<void> {
  if (items.length === 0) {
    return
  }

  const concurrency: number = Math.max(1, Math.min(limit, items.length))
  let nextIndex: number = 0
  let completedCount: number = 0
  let abortQueued: boolean = false

  const runWorker: () => Promise<void> = async (): Promise<void> => {
    while (!shouldStop() && !abortQueued) {
      const index: number = nextIndex
      nextIndex += 1

      if (index >= items.length) {
        return
      }

      const outcome: ConcurrentPoolWorkerResult = await worker(items[index]!, index)

      completedCount += 1
      onProgress?.(completedCount, items.length)

      if (outcome === 'abort') {
        abortQueued = true
      }
    }
  }

  await Promise.all(Array.from({ length: concurrency }, () => runWorker()))
}
