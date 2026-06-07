import type { ManagedAccount } from '#src-core/types/response/managed-accounts.types'

/**
 * Paire prenom et nom Outlook utilisee pour la deduplication.
 */
export type OutlookNamePair = {
  firstName: string
  lastName: string
}

/**
 * Cle de deduplication prenom + nom (insensible a la casse).
 * @param {string} firstName - Prenom Outlook.
 * @param {string} lastName - Nom Outlook.
 * @returns {string} Cle normalisee prenom|nom.
 */
export function outlookNamePairKey(firstName: string, lastName: string): string {
  return `${firstName.trim().toLowerCase()}|${lastName.trim().toLowerCase()}`
}

/**
 * Extrait les paires prenom/nom Outlook deja presentes dans les comptes geres.
 * @param {readonly ManagedAccount[]} accounts - Comptes deja enregistres.
 * @returns {OutlookNamePair[]} Paires uniques (casse normalisee).
 */
export function collectUsedOutlookNamePairs(accounts: readonly ManagedAccount[]): OutlookNamePair[] {
  const seenKeys: Set<string> = new Set()
  const pairs: OutlookNamePair[] = []

  for (const account of accounts) {
    const firstName: string | undefined = account.outlookFirstName?.trim()
    const lastName: string | undefined = account.outlookLastName?.trim()

    if (!firstName || !lastName) {
      continue
    }

    const key: string = outlookNamePairKey(firstName, lastName)

    if (seenKeys.has(key)) {
      continue
    }

    seenKeys.add(key)
    pairs.push({ firstName, lastName })
  }

  return pairs
}

/**
 * Ajoute une paire au jeu des noms deja utilises (session en cours incluse).
 * @param {OutlookNamePair[]} pairs - Liste mutable des paires deja vues.
 * @param {Set<string>} seenKeys - Cles deja enregistrees.
 * @param {string} firstName - Prenom a ajouter.
 * @param {string} lastName - Nom a ajouter.
 * @returns {void}
 */
export function registerUsedOutlookNamePair(
  pairs: OutlookNamePair[],
  seenKeys: Set<string>,
  firstName: string,
  lastName: string,
): void {
  const key: string = outlookNamePairKey(firstName, lastName)

  if (seenKeys.has(key)) {
    return
  }

  seenKeys.add(key)
  pairs.push({ firstName, lastName })
}
