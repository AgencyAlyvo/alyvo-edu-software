import { describe, expect, it } from 'vitest'

import { decodeProcessOutput } from '../../src-core/utils/decode-process-output'

describe('decodeProcessOutput', () => {
  it('decode une chaine deja lisible', () => {
    expect(decodeProcessOutput('Connecté')).toBe('Connecté')
  })

  it('decode un Uint8Array UTF-8', () => {
    expect(decodeProcessOutput(new TextEncoder().encode('Email prevu : test@outlook.com'))).toBe(
      'Email prevu : test@outlook.com',
    )
  })

  it('decode un ArrayBuffer UTF-8', () => {
    const bytes: Uint8Array = new TextEncoder().encode('Connecté : Chicago - Bulls')

    expect(decodeProcessOutput(bytes.buffer)).toBe('Connecté : Chicago - Bulls')
  })

  it('decode un tableau de bytes serialise par Tauri', () => {
    const bytes: number[] = [...new TextEncoder().encode('Inscription terminee : test@outlook.com')]

    expect(decodeProcessOutput(bytes)).toBe('Inscription terminee : test@outlook.com')
  })

  it('decode un payload objet contenant un tableau de bytes', () => {
    const bytes: number[] = [...new TextEncoder().encode('Email cible : test@outlook.com')]

    expect(decodeProcessOutput({ data: bytes })).toBe('Email cible : test@outlook.com')
  })
})
