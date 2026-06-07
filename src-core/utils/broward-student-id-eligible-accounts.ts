import type { ManagedAccount } from '#src-core/types/response/managed-accounts.types'

import { BROWARD_STUDENT_ID_MIN_HOURS_AFTER_REQUEST } from '#src-core/constants/broward-student-id-sidecar.constants'

const MIN_HOURS_AFTER_REQUEST_MS: number = BROWARD_STUDENT_ID_MIN_HOURS_AFTER_REQUEST * 60 * 60 * 1000

/**
 * Indique si un compte managed est pret pour la recuperation Student ID.
 * @param {ManagedAccount} account - Compte a verifier.
 * @returns {boolean} True si eligible.
 */
export function isBrowardStudentIdEligibleAccount(account: ManagedAccount): boolean {
  if (!account.schoolRequestSent) {
    return false
  }

  if ((account.schoolEmail?.trim().length ?? 0) > 0 || (account.studentId?.trim().length ?? 0) > 0) {
    return false
  }

  if (
    (account.outlookEmail?.trim().length ?? 0) === 0 ||
    (account.outlookEmailPassword?.trim().length ?? 0) === 0 ||
    (account.birthday?.trim().length ?? 0) === 0
  ) {
    return false
  }

  const sentAt: string | null = account.schoolRequestSentAt

  if (!sentAt) {
    return false
  }

  const sentMs: number = new Date(sentAt).getTime()

  if (Number.isNaN(sentMs)) {
    return false
  }

  return Date.now() - sentMs >= MIN_HOURS_AFTER_REQUEST_MS
}

/**
 * Filtre et trie les comptes eligibles Student ID (id croissant).
 * @param {readonly ManagedAccount[]} accounts - Liste complete.
 * @returns {ManagedAccount[]} Comptes eligibles tries.
 */
export function listBrowardStudentIdEligibleAccounts(accounts: readonly ManagedAccount[]): ManagedAccount[] {
  return accounts
    .filter(isBrowardStudentIdEligibleAccount)
    .sort((a: ManagedAccount, b: ManagedAccount): number => a.id - b.id)
}

export { toBrowardBirthdayIso } from '#src-core/utils/broward-eligible-accounts'
