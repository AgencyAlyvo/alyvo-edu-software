import { describe, expect, it } from 'vitest'

import { runConcurrentPool } from '#src-core/utils/run-concurrent-pool'

describe('runConcurrentPool', () => {
  it('respecte la limite de concurrence', async () => {
    const items: number[] = [0, 1, 2, 3, 4]
    let running: number = 0
    let maxRunning: number = 0

    await runConcurrentPool(
      items,
      2,
      () => false,
      async () => {
        running += 1
        maxRunning = Math.max(maxRunning, running)
        await new Promise((resolve: (value: void) => void) => setTimeout(resolve, 20))
        running -= 1

        return 'done'
      },
    )

    expect(maxRunning).toBeLessThanOrEqual(2)
    expect(maxRunning).toBeGreaterThan(1)
  })
})
