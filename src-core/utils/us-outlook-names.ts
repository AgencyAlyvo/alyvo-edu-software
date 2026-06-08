import firstNamesRaw from '../../sidecar/outlook-creator/data/us_first_names.txt?raw'
import lastNamesRaw from '../../sidecar/outlook-creator/data/us_last_names.txt?raw'

import { outlookNamePairKey, type OutlookNamePair } from '#src-core/utils/outlook-account-names'

const MIN_NAMES: number = 5000
const MAX_RANDOM_ATTEMPTS: number = 2000

let cachedFirstNames: string[] | null = null
let cachedLastNames: string[] | null = null

function parseNameList(raw: string): string[] {
  return raw
    .split(/\r?\n/u)
    .map((line: string) => line.trim())
    .filter((line: string) => line.length > 0 && !line.startsWith('#'))
}

function loadFirstNames(): string[] {
  if (cachedFirstNames === null) {
    cachedFirstNames = parseNameList(firstNamesRaw)

    if (cachedFirstNames.length < MIN_NAMES) {
      throw new Error(`Liste de prénoms US incomplète (${cachedFirstNames.length}).`)
    }
  }

  return cachedFirstNames
}

function loadLastNames(): string[] {
  if (cachedLastNames === null) {
    cachedLastNames = parseNameList(lastNamesRaw)

    if (cachedLastNames.length < MIN_NAMES) {
      throw new Error(`Liste de noms US incomplète (${cachedLastNames.length}).`)
    }
  }

  return cachedLastNames
}

function randomFromList(values: readonly string[]): string {
  const buffer: Uint32Array<ArrayBuffer> = new Uint32Array(new ArrayBuffer(4))
  crypto.getRandomValues(buffer)

  return values[buffer[0]! % values.length]!
}

/**
 * Tire un prénom et un nom US non déjà utilisés en base ou dans la session.
 */
export function randomUsFullName(usedPairs: readonly OutlookNamePair[]): { firstName: string; lastName: string } {
  const excluded: Set<string> = new Set(
    usedPairs.map((pair: OutlookNamePair) => outlookNamePairKey(pair.firstName, pair.lastName)),
  )
  const firstNames: string[] = loadFirstNames()
  const lastNames: string[] = loadLastNames()

  for (let attempt: number = 0; attempt < MAX_RANDOM_ATTEMPTS; attempt += 1) {
    const firstName: string = randomFromList(firstNames)
    const lastName: string = randomFromList(lastNames)
    const key: string = outlookNamePairKey(firstName, lastName)

    if (!excluded.has(key)) {
      return { firstName, lastName }
    }
  }

  throw new Error('Impossible de tirer un prénom et un nom non déjà utilisés.')
}
