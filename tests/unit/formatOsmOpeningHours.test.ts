import { describe, expect, it } from 'vitest'
import { formatOsmOpeningHoursForDisplay } from '#src-nuxt/app/utils/formatOsmOpeningHours'

describe('formatOsmOpeningHoursForDisplay', () => {
  it('formats 24/7 in French', () => {
    expect(formatOsmOpeningHoursForDisplay('24/7')).toContain('24 h/24')
    expect(formatOsmOpeningHoursForDisplay('24/7')).toContain('7 j/7')
  })

  it('formats day ranges and split hours', () => {
    const result: string | null = formatOsmOpeningHoursForDisplay('Tu-Sa 10:00-12:30,15:00-19:30')
    expect(result).toContain('Mardi au samedi')
    expect(result).toContain('10 h 00 – 12 h 30')
    expect(result).toContain('15 h 00 – 19 h 30')
  })

  it('formats multiple rules', () => {
    const result: string | null = formatOsmOpeningHoursForDisplay('Mo-Fr 09:00-18:00; Sa 10:00-13:00')
    expect(result).toContain('Lundi au vendredi')
    expect(result).toContain('Samedi')
  })
})
