const DIGITS: string = '0123456789'

/**
 * Construit la partie locale d'un email Outlook (prenomnom + chiffres).
 */
export function buildOutlookLocalPart(firstName: string, lastName: string, digitCount: number = 12): string {
  const base: string = `${firstName}${lastName}`.toLowerCase().replace(/[^a-z0-9]/g, '')
  const normalizedBase: string = base.length >= 2 ? base : 'user'
  let digits: string = ''

  for (let index: number = 0; index < digitCount; index += 1) {
    digits += DIGITS.charAt(randomInt(DIGITS.length))
  }

  return `${normalizedBase}${digits}`
}

/**
 * Retourne une adresse @outlook.com suggérée pour l'inscription manuelle.
 */
export function buildOutlookEmail(firstName: string, lastName: string): string {
  return `${buildOutlookLocalPart(firstName, lastName)}@outlook.com`
}

function randomInt(maxExclusive: number): number {
  if (maxExclusive <= 0) {
    return 0
  }

  const buffer: Uint32Array<ArrayBuffer> = new Uint32Array(new ArrayBuffer(4))
  crypto.getRandomValues(buffer)

  return buffer[0]! % maxExclusive
}
