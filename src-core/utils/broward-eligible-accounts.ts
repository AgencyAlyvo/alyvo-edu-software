import type { ManagedAccount } from '#src-core/types/response/managed-accounts.types'

/**
 * Indique si un compte managed est pret pour l'inscription Broward.
 * @param {ManagedAccount} account - Compte a verifier.
 * @returns {boolean} True si Outlook est complet (mot de passe inclus) et demande ecole non encore envoyee.
 */
export function isBrowardEligibleAccount(account: ManagedAccount): boolean {
  return (
    (account.outlookEmail?.trim().length ?? 0) > 0 &&
    (account.outlookFirstName?.trim().length ?? 0) > 0 &&
    (account.outlookLastName?.trim().length ?? 0) > 0 &&
    (account.outlookEmailPassword?.trim().length ?? 0) > 0 &&
    (account.birthday?.trim().length ?? 0) > 0 &&
    account.schoolRequestSent === false
  )
}

/**
 * Filtre et trie les comptes eligibles Broward (id croissant).
 * @param {readonly ManagedAccount[]} accounts - Liste complete.
 * @returns {ManagedAccount[]} Comptes eligibles tries.
 */
export function listBrowardEligibleAccounts(accounts: readonly ManagedAccount[]): ManagedAccount[] {
  return accounts.filter(isBrowardEligibleAccount).sort((a: ManagedAccount, b: ManagedAccount): number => a.id - b.id)
}

/**
 * Normalise une date API en YYYY-MM-DD pour le sidecar.
 * @param {string | null | undefined} value - Date ISO ou vide.
 * @returns {string} Date normalisee ou chaine vide.
 */
export function toBrowardBirthdayIso(value: string | null | undefined): string {
  if (!value) {
    return ''
  }

  return value.includes('T') ? value.split('T')[0]! : value.slice(0, 10)
}
