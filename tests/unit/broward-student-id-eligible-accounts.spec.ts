import { describe, expect, it } from 'vitest'

import type { ManagedAccount } from '#src-core/types/response/managed-accounts.types'
import {
  isBrowardStudentIdEligibleAccount,
  listBrowardStudentIdEligibleAccounts,
} from '#src-core/utils/broward-student-id-eligible-accounts'

/**
 * Fabrique un compte managed pour les tests.
 * @param {Partial<ManagedAccount>} partial - Champs a surcharger.
 * @returns {ManagedAccount} Compte de test.
 */
function account(partial: Partial<ManagedAccount>): ManagedAccount {
  return {
    id: 1,
    outlookEmail: null,
    outlookFirstName: null,
    outlookLastName: null,
    outlookEmailPassword: null,
    birthday: null,
    cursorPassword: null,
    schoolEmail: null,
    studentId: null,
    schoolEmailPassword: null,
    schoolEmailActivated: false,
    schoolRequestSent: false,
    schoolEmailActivatedAt: null,
    schoolRequestSentAt: null,
    cursorAccountActivated: false,
    cursorSheeridRequestSent: false,
    cursorAccountActivatedAt: null,
    cursorSheeridRequestSentAt: null,
    createdAt: '2026-01-01T00:00:00.000Z',
    updatedAt: '2026-01-01T00:00:00.000Z',
    ...partial,
  }
}

describe('isBrowardStudentIdEligibleAccount', () => {
  it('accepte un compte avec demande ecole >= 3h et sans email ecole', () => {
    const sentAt: string = new Date(Date.now() - 4 * 60 * 60 * 1000).toISOString()

    expect(
      isBrowardStudentIdEligibleAccount(
        account({
          outlookEmail: 'a@outlook.com',
          outlookEmailPassword: 'Outlook-pass1!',
          birthday: '2000-01-12',
          schoolRequestSent: true,
          schoolRequestSentAt: sentAt,
        }),
      ),
    ).toBe(true)
  })

  it('refuse si email ecole deja renseigne', () => {
    const sentAt: string = new Date(Date.now() - 4 * 60 * 60 * 1000).toISOString()

    expect(
      isBrowardStudentIdEligibleAccount(
        account({
          outlookEmail: 'a@outlook.com',
          outlookEmailPassword: 'Outlook-pass1!',
          birthday: '2000-01-12',
          schoolRequestSent: true,
          schoolRequestSentAt: sentAt,
          schoolEmail: 'user@mail.broward.edu',
        }),
      ),
    ).toBe(false)
  })

  it('refuse si moins de 3h depuis la demande', () => {
    const sentAt: string = new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString()

    expect(
      isBrowardStudentIdEligibleAccount(
        account({
          outlookEmail: 'a@outlook.com',
          outlookEmailPassword: 'Outlook-pass1!',
          birthday: '2000-01-12',
          schoolRequestSent: true,
          schoolRequestSentAt: sentAt,
        }),
      ),
    ).toBe(false)
  })
})

describe('listBrowardStudentIdEligibleAccounts', () => {
  it('trie par id croissant', () => {
    const sentAt: string = new Date(Date.now() - 4 * 60 * 60 * 1000).toISOString()
    const base: Partial<ManagedAccount> = {
      outlookEmailPassword: 'Outlook-pass1!',
      birthday: '2000-01-12',
      schoolRequestSent: true,
      schoolRequestSentAt: sentAt,
    }

    const result: ManagedAccount[] = listBrowardStudentIdEligibleAccounts([
      account({ id: 3, outlookEmail: 'c@outlook.com', ...base }),
      account({ id: 1, outlookEmail: 'a@outlook.com', ...base }),
    ])

    expect(result.map((entry: ManagedAccount) => entry.id)).toEqual([1, 3])
  })
})
