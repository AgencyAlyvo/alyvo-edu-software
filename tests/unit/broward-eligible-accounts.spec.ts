import { describe, expect, it } from 'vitest'

import type { ManagedAccount } from '#src-core/types/response/managed-accounts.types'
import {
  isBrowardEligibleAccount,
  listBrowardEligibleAccounts,
  toBrowardBirthdayIso,
} from '#src-core/utils/broward-eligible-accounts'

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

describe('isBrowardEligibleAccount', () => {
  it('accepte un compte Outlook complet sans demande ecole envoyee', () => {
    expect(
      isBrowardEligibleAccount(
        account({
          outlookEmail: 'a@outlook.com',
          outlookFirstName: 'John',
          outlookLastName: 'Doe',
          outlookEmailPassword: 'Outlook-pass1!',
          birthday: '2000-01-12',
          schoolRequestSent: false,
        }),
      ),
    ).toBe(true)
  })

  it('refuse si demande ecole deja envoyee', () => {
    expect(
      isBrowardEligibleAccount(
        account({
          outlookEmail: 'a@outlook.com',
          outlookFirstName: 'John',
          outlookLastName: 'Doe',
          outlookEmailPassword: 'Outlook-pass1!',
          birthday: '2000-01-12',
          schoolRequestSent: true,
        }),
      ),
    ).toBe(false)
  })
})

describe('listBrowardEligibleAccounts', () => {
  it('trie par id croissant', () => {
    const result: ManagedAccount[] = listBrowardEligibleAccounts([
      account({
        id: 3,
        outlookEmail: 'c@outlook.com',
        outlookFirstName: 'C',
        outlookLastName: 'C',
        outlookEmailPassword: 'Outlook-pass1!',
        birthday: '2000-01-12',
      }),
      account({
        id: 1,
        outlookEmail: 'a@outlook.com',
        outlookFirstName: 'A',
        outlookLastName: 'A',
        outlookEmailPassword: 'Outlook-pass1!',
        birthday: '2000-01-12',
      }),
    ])

    expect(result.map((entry: ManagedAccount) => entry.id)).toEqual([1, 3])
  })
})

describe('toBrowardBirthdayIso', () => {
  it('extrait YYYY-MM-DD depuis ISO datetime', () => {
    expect(toBrowardBirthdayIso('2008-01-17T00:00:00.000Z')).toBe('2008-01-17')
  })
})
