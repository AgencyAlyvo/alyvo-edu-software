import { afterEach, describe, expect, it, vi } from 'vitest'

import {
  buildRecaptchaV2ProxyLessCreatePayload,
  CapSolverError,
  type CapSolverFetch,
  type CapSolverJson,
  isCapSolverResultPending,
  parseCapSolverRecaptchaToken,
  parseCapSolverTaskId,
  solveRecaptchaV2ProxyLess,
} from '#src-core/utils/capsolver-client'

/**
 * Sleep noop pour accelerer les tests de poll CapSolver.
 * @param {number} _ms - Delai ignore.
 * @returns {Promise<void>} Promise resolue immediatement.
 */
function noopCapSolverSleep(_ms: number): Promise<void> {
  return Promise.resolve()
}

describe('buildRecaptchaV2ProxyLessCreatePayload', () => {
  it('utilise ReCaptchaV2TaskProxyLess', () => {
    const payload: CapSolverJson = buildRecaptchaV2ProxyLessCreatePayload('CAP-key', 'https://example.com', 'site-key')

    expect(payload).toEqual({
      clientKey: 'CAP-key',
      task: {
        type: 'ReCaptchaV2TaskProxyLess',
        websiteURL: 'https://example.com',
        websiteKey: 'site-key',
      },
    })
  })
})

describe('parseCapSolverTaskId', () => {
  it('retourne le taskId si errorId vaut 0', () => {
    expect(parseCapSolverTaskId({ errorId: 0, taskId: 'task-123' })).toBe('task-123')
  })

  it('leve si errorId non nul', () => {
    expect(() => parseCapSolverTaskId({ errorId: 1, errorDescription: 'bad key' })).toThrow(CapSolverError)
  })
})

describe('parseCapSolverRecaptchaToken', () => {
  it('extrait gRecaptchaResponse quand status est ready', () => {
    expect(
      parseCapSolverRecaptchaToken({
        errorId: 0,
        status: 'ready',
        solution: { gRecaptchaResponse: 'token-abc' },
      }),
    ).toBe('token-abc')
  })
})

describe('isCapSolverResultPending', () => {
  it('retourne true pour processing', () => {
    expect(isCapSolverResultPending({ errorId: 0, status: 'processing' })).toBe(true)
  })
})

describe('solveRecaptchaV2ProxyLess', () => {
  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('mock createTask puis getTaskResult jusqu au token', async () => {
    const fetchImpl: CapSolverFetch = vi.fn((url: string): Promise<Response> => {
      if (url.includes('createTask')) {
        return Promise.resolve(new Response(JSON.stringify({ errorId: 0, taskId: 'task-1' }), { status: 200 }))
      }

      return Promise.resolve(
        new Response(
          JSON.stringify({
            errorId: 0,
            status: 'ready',
            solution: { gRecaptchaResponse: 'solved-token' },
          }),
          { status: 200 },
        ),
      )
    }) as CapSolverFetch

    const token: string = await solveRecaptchaV2ProxyLess('CAP-test', 'https://broward.example', 'site-key', {
      fetchImpl,
      pollIntervalMs: 0,
      maxPollAttempts: 3,
      sleep: noopCapSolverSleep,
    })

    expect(token).toBe('solved-token')
    expect(fetchImpl).toHaveBeenCalledTimes(2)
  })

  it('refuse une cle API vide', async () => {
    await expect(solveRecaptchaV2ProxyLess('  ', 'https://broward.example', 'site-key')).rejects.toThrow(
      'CAPSOLVER_API_KEY manquante.',
    )
  })
})
