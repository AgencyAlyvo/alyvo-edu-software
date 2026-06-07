import { describe, expect, it } from 'vitest'

import { generateOutlookPassword } from '#src-core/utils/generate-outlook-password'
import { isValidOutlookPassword } from '#src-core/utils/outlook-password.validation'

describe('generateOutlookPassword', () => {
  it('returns a valid unique password distinct from recent ones', () => {
    const recent: string[] = []
    const passwords: string[] = []

    for (let index: number = 0; index < 10; index += 1) {
      const password: string = generateOutlookPassword(recent)
      expect(isValidOutlookPassword(password)).toBe(true)
      expect(recent).not.toContain(password)
      passwords.push(password)
      recent.push(password)
    }

    expect(new Set(passwords).size).toBe(passwords.length)
  })
})
