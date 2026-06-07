import { isValidOutlookPassword } from '#src-core/utils/outlook-password.validation'

const UPPERCASE: string = 'ABCDEFGHJKLMNPQRSTUVWXYZ'
const LOWERCASE: string = 'abcdefghjkmnpqrstuvwxyz'
const DIGITS: string = '23456789'
const SYMBOLS: string = '!@#$%&*-_+=?'
const ALL_CHARS: string = UPPERCASE + LOWERCASE + DIGITS + SYMBOLS

const MIN_LENGTH: number = 14
const MAX_LENGTH: number = 18
const RECENT_MIN_LEVENSHTEIN: number = 6
const MAX_GENERATION_ATTEMPTS: number = 64

/**
 * Genere un mot de passe aleatoire conforme Outlook, different des precedents de la session.
 * @param {readonly string[]} recentPasswords - Mots de passe deja utilises dans le lot en cours.
 * @returns {string} Mot de passe unique et conforme.
 */
export function generateOutlookPassword(recentPasswords: readonly string[] = []): string {
  for (let attempt: number = 0; attempt < MAX_GENERATION_ATTEMPTS; attempt += 1) {
    const password: string = buildRandomPassword()

    if (!isValidOutlookPassword(password) || password.startsWith('-')) {
      continue
    }

    if (recentPasswords.includes(password)) {
      continue
    }

    const tooSimilar: boolean = recentPasswords.some(
      (previous: string) => levenshteinDistance(password, previous) < RECENT_MIN_LEVENSHTEIN,
    )

    if (tooSimilar) {
      continue
    }

    return password
  }

  throw new Error('Impossible de générer un mot de passe Outlook unique.')
}

/**
 * Construit un mot de passe aleatoire de longueur variable.
 * @returns {string} Mot de passe brut avant validation de similarite.
 */
function buildRandomPassword(): string {
  const length: number = MIN_LENGTH + randomInt(MAX_LENGTH - MIN_LENGTH + 1)
  const chars: string[] = [pickChar(UPPERCASE), pickChar(LOWERCASE), pickChar(DIGITS), pickChar(SYMBOLS)]

  while (chars.length < length) {
    chars.push(pickChar(ALL_CHARS))
  }

  return shuffle(chars).join('')
}

/**
 * Choisit un caractere aleatoire dans un alphabet.
 * @param {string} pool - Alphabet source.
 * @returns {string} Caractere tire.
 */
function pickChar(pool: string): string {
  return pool.charAt(randomInt(pool.length))
}

/**
 * Melange un tableau de caracteres (Fisher-Yates).
 * @param {string[]} values - Caracteres a melanger.
 * @returns {string[]} Copie melangee.
 */
function shuffle(values: string[]): string[] {
  const copy: string[] = [...values]

  for (let index: number = copy.length - 1; index > 0; index -= 1) {
    const swapIndex: number = randomInt(index + 1)
    const current: string = copy[index]!
    copy[index] = copy[swapIndex]!
    copy[swapIndex] = current
  }

  return copy
}

/**
 * Entier aleatoire cryptographique dans [0, maxExclusive).
 * @param {number} maxExclusive - Borne superieure exclusive.
 * @returns {number} Entier tire.
 */
function randomInt(maxExclusive: number): number {
  if (maxExclusive <= 0) {
    return 0
  }

  const buffer: Uint32Array<ArrayBuffer> = new Uint32Array(new ArrayBuffer(4))
  crypto.getRandomValues(buffer)

  return buffer[0]! % maxExclusive
}

/**
 * Distance de Levenshtein entre deux chaines.
 * @param {string} left - Premiere chaine.
 * @param {string} right - Seconde chaine.
 * @returns {number} Nombre d'operations d'edition minimales.
 */
function levenshteinDistance(left: string, right: string): number {
  const rows: number = left.length + 1
  const cols: number = right.length + 1
  const matrix: number[][] = Array.from({ length: rows }, () => Array<number>(cols).fill(0))

  for (let row: number = 0; row < rows; row += 1) {
    matrix[row]![0] = row
  }

  for (let col: number = 0; col < cols; col += 1) {
    matrix[0]![col] = col
  }

  for (let row: number = 1; row < rows; row += 1) {
    for (let col: number = 1; col < cols; col += 1) {
      const cost: number = left.charAt(row - 1) === right.charAt(col - 1) ? 0 : 1
      matrix[row]![col] = Math.min(
        matrix[row - 1]![col]! + 1,
        matrix[row]![col - 1]! + 1,
        matrix[row - 1]![col - 1]! + cost,
      )
    }
  }

  return matrix[left.length]![right.length]!
}
