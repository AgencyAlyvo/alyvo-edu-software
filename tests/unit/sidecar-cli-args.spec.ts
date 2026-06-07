import { describe, expect, it } from 'vitest'

import { formatSidecarCliOption } from '#src-core/utils/sidecar-cli-args'

describe('formatSidecarCliOption', () => {
  it('utilise la forme --flag=value pour les valeurs commencant par un tiret', () => {
    expect(formatSidecarCliOption('password', '-FR_c=Pj5YQdpQ6')).toBe('--password=-FR_c=Pj5YQdpQ6')
  })

  it('accepte un flag deja prefixe par --', () => {
    expect(formatSidecarCliOption('--birthday', '2001-01-12')).toBe('--birthday=2001-01-12')
  })
})
