import { describe, expect, it } from 'vitest'

import { buildOutlookEmail, buildOutlookLocalPart } from '#src-core/utils/build-outlook-email'

describe('build-outlook-email', () => {
  it('builds a local part from first and last name', () => {
    const localPart: string = buildOutlookLocalPart('John', 'Doe', 4)

    expect(localPart.startsWith('johndoe')).toBe(true)
    expect(localPart).toMatch(/^johndoe\d{4}$/u)
  })

  it('builds a full outlook.com address', () => {
    const email: string = buildOutlookEmail('Amy', 'Lee')

    expect(email.endsWith('@outlook.com')).toBe(true)
    expect(email.startsWith('amylee')).toBe(true)
  })
})
