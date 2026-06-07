import { describe, expect, it } from 'vitest'

/**
 * Reproduit la detection Windscribe (logique alignee sur OutlookBatchVpnService).
 * @param {string} text - Sortie CLI Windscribe.
 * @returns {string} Texte normalise (minuscules, sans accents).
 */
function normalizeWindscribeText(text: string): string {
  return text
    .toLowerCase()
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
}

/**
 * Determine si la sortie Windscribe indique une connexion active.
 * @param {string} text - Sortie CLI Windscribe.
 * @returns {boolean} True si connecte.
 */
function isWindscribeConnectedOutput(text: string): boolean {
  const normalized: string = normalizeWindscribeText(text)

  if (
    normalized.includes('disconnected') ||
    normalized.includes('deconnecte') ||
    normalized.includes('not connected') ||
    normalized.includes('non connecte')
  ) {
    return false
  }

  if (normalized.includes('connected') || normalized.includes('connecte')) {
    return true
  }

  if (/connect[eé]\s*:/i.test(text) || text.includes('ConnectÃ©')) {
    return true
  }

  return false
}

describe('isWindscribeConnectedOutput', () => {
  it('detecte Connecte en francais (UTF-8)', () => {
    const sample: string = `Connexion : Tampa - Big Guava
*Connecté : Tampa - Big Guava
Connecté : Tampa - Big Guava`

    expect(isWindscribeConnectedOutput(sample)).toBe(true)
  })

  it('detecte le mojibake ConnectÃ© (UTF-8 lu en CP1252)', () => {
    expect(isWindscribeConnectedOutput('*ConnectÃ© : Tampa - Big Guava')).toBe(true)
  })

  it('ignore Connexion seule (en cours)', () => {
    expect(isWindscribeConnectedOutput('Connexion : Tampa - Big Guava')).toBe(false)
  })

  it('detecte connected en anglais', () => {
    expect(isWindscribeConnectedOutput('Connected to US Central')).toBe(true)
  })
})
