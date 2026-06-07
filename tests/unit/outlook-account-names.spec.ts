import { describe, expect, it } from 'vitest'

import type { ManagedAccount } from '#src-core/types/response/managed-accounts.types'
import {
  collectUsedOutlookNamePairs,
  outlookNamePairKey,
  registerUsedOutlookNamePair,
  type OutlookNamePair,
} from '#src-core/utils/outlook-account-names'

describe('outlook-account-names', () => {
  it('deduplicates name pairs case-insensitively', () => {
    const accounts: ManagedAccount[] = [
      {
        id: 1,
        outlookFirstName: 'John',
        outlookLastName: 'Doe',
      } as ManagedAccount,
      {
        id: 2,
        outlookFirstName: 'john',
        outlookLastName: 'DOE',
      } as ManagedAccount,
    ]

    const pairs: OutlookNamePair[] = collectUsedOutlookNamePairs(accounts)

    expect(pairs).toHaveLength(1)
    expect(pairs[0]).toEqual({ firstName: 'John', lastName: 'Doe' })
  })

  it('registers pairs during a batch without duplicates', () => {
    const pairs: OutlookNamePair[] = collectUsedOutlookNamePairs([])
    const keys: Set<string> = new Set<string>()

    registerUsedOutlookNamePair(pairs, keys, 'Amy', 'Lee')
    registerUsedOutlookNamePair(pairs, keys, 'amy', 'lee')

    expect(pairs).toHaveLength(1)
    expect(outlookNamePairKey('Amy', 'Lee')).toBe(outlookNamePairKey('amy', 'lee'))
  })
})
