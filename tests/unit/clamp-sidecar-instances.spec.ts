import { describe, expect, it } from 'vitest'

import {
  MAX_SIDECAR_CONCURRENT_INSTANCES,
  MIN_SIDECAR_CONCURRENT_INSTANCES,
} from '#src-core/constants/desktop-settings.constants'
import { clampSidecarInstances } from '#src-core/utils/clamp-sidecar-instances'

describe('clampSidecarInstances', () => {
  it('borne entre min et max', () => {
    expect(clampSidecarInstances(0)).toBe(MIN_SIDECAR_CONCURRENT_INSTANCES)
    expect(clampSidecarInstances(99)).toBe(MAX_SIDECAR_CONCURRENT_INSTANCES)
    expect(clampSidecarInstances(3)).toBe(3)
  })

  it('retourne le min si la valeur est invalide', () => {
    expect(clampSidecarInstances(Number.NaN)).toBe(MIN_SIDECAR_CONCURRENT_INSTANCES)
  })
})
