/**
 * Mutex asynchrone simple (file d'attente de promesses).
 * @returns {(task: () => Promise<T>) => Promise<T>} Executeur serialise.
 */
export function createAsyncMutex(): <T>(task: () => Promise<T>) => Promise<T> {
  let chain: Promise<void> = Promise.resolve()

  return async <T>(task: () => Promise<T>): Promise<T> => {
    const previous: Promise<void> = chain
    let release!: () => void
    chain = new Promise<void>((resolve: () => void): void => {
      release = resolve
    })

    await previous

    try {
      return await task()
    } finally {
      release()
    }
  }
}
