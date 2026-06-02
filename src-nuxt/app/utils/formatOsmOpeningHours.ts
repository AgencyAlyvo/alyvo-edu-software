const DAY_CODES: readonly string[] = ['Mo', 'Tu', 'We', 'Th', 'Fr', 'Sa', 'Su'] as const

const DAY_LABELS_FR: Record<string, string> = {
  Mo: 'lundi',
  Tu: 'mardi',
  We: 'mercredi',
  Th: 'jeudi',
  Fr: 'vendredi',
  Sa: 'samedi',
  Su: 'dimanche',
  PH: 'jours feries',
}

const ALWAYS_OPEN_PATTERNS: RegExp[] = [/^24\s*\/\s*7$/i, /^24\s*h(?:ours?)?$/i, /^open$/i, /^always\s+open$/i]

/**
 * Indique si la valeur OSM correspond a une ouverture permanente.
 * @param {string} value - Chaine opening_hours brute.
 * @returns {boolean} True si ouvert en continu.
 */
const isAlwaysOpen: (value: string) => boolean = (value: string): boolean => {
  const normalized: string = value.trim()
  if (ALWAYS_OPEN_PATTERNS.some((pattern: RegExp): boolean => pattern.test(normalized))) {
    return true
  }
  return /(?:^|;\s*)(?:Mo|Tu|We|Th|Fr|Sa|Su)(?:-(?:Mo|Tu|We|Th|Fr|Sa|Su))?\s+00:00-24:00\s*$/i.test(normalized)
}

/**
 * Met une majuscule sur la premiere lettre.
 * @param {string} text - Texte a capitaliser.
 * @returns {string} Texte capitalise.
 */
const capitalize: (text: string) => string = (text: string): string =>
  text.length > 0 ? `${text.charAt(0).toUpperCase()}${text.slice(1)}` : text

/**
 * Formate une heure HH:mm en libelle francais.
 * @param {string} time - Heure au format HH:mm.
 * @returns {string} Heure lisible.
 */
const formatClock: (time: string) => string = (time: string): string => {
  const match: RegExpMatchArray | null = time.trim().match(/^(\d{1,2}):(\d{2})$/)
  const hoursRaw: string | undefined = match?.[1]
  const minutesRaw: string | undefined = match?.[2]
  if (!hoursRaw || !minutesRaw) {
    return time.trim()
  }
  const hours: string = hoursRaw.padStart(2, '0')
  return `${hours} h ${minutesRaw}`
}

/**
 * Formate une plage horaire OSM (ex. 10:00-12:30).
 * @param {string} range - Plage horaire.
 * @returns {string} Plage lisible.
 */
const formatTimeRange: (range: string) => string = (range: string): string => {
  const trimmed: string = range.trim()
  if (!trimmed || trimmed.toLowerCase() === 'off') {
    return 'ferme'
  }
  if (trimmed === '24:00' || trimmed === '00:00-24:00') {
    return '24 h/24'
  }
  const parts: string[] = trimmed.split('-')
  const start: string | undefined = parts[0]
  const end: string | undefined = parts[1]
  if (!start || !end) {
    return trimmed
  }
  return `${formatClock(start)} – ${formatClock(end)}`
}

/**
 * Retourne l'index d'un code jour OSM.
 * @param {string} code - Code jour (Mo, Tu, ...).
 * @returns {number | null} Index ou null.
 */
const dayIndex: (code: string) => number | null = (code: string): number | null => {
  const index: number = DAY_CODES.indexOf(code)
  return index >= 0 ? index : null
}

/**
 * Developpe une plage de jours (ex. Tu-Sa).
 * @param {string} from - Jour de debut.
 * @param {string} to - Jour de fin.
 * @returns {number[]} Indices des jours inclus.
 */
const expandDayRange: (from: string, to: string) => number[] = (from: string, to: string): number[] => {
  const start: number | null = dayIndex(from)
  const end: number | null = dayIndex(to)
  if (start === null || end === null) {
    return []
  }
  if (start <= end) {
    return Array.from({ length: end - start + 1 }, (_: unknown, i: number): number => start + i)
  }
  return [
    ...Array.from({ length: DAY_CODES.length - start }, (_: unknown, i: number): number => start + i),
    ...Array.from({ length: end + 1 }, (_: unknown, i: number): number => i),
  ]
}

/**
 * Parse une specification de jours OSM en indices.
 * @param {string} daySpec - Specification (Mo-Fr, Tu,We, ...).
 * @returns {number[]} Indices des jours.
 */
const parseDayIndices: (daySpec: string) => number[] = (daySpec: string): number[] => {
  const spec: string = daySpec.trim()
  if (spec === 'PH') {
    return []
  }
  const indices: Set<number> = new Set<number>()
  for (const token of spec.split(',')) {
    const part: string = token.trim()
    if (!part) continue
    if (part.includes('-') && !part.includes('[')) {
      const dashIndex: number = part.indexOf('-')
      const from: string = part.slice(0, dashIndex).trim()
      const to: string = part.slice(dashIndex + 1).trim()
      if (from && to) {
        for (const index of expandDayRange(from, to)) {
          indices.add(index)
        }
      }
      continue
    }
    const index: number | null = dayIndex(part)
    if (index !== null) {
      indices.add(index)
    }
  }
  return [...indices].sort((a: number, b: number): number => a - b)
}

/**
 * Formate une liste d'indices de jours en francais.
 * @param {number[]} indices - Indices Mo=0 ... Su=6.
 * @returns {string} Libelle des jours.
 */
const formatDayIndices: (indices: number[]) => string = (indices: number[]): string => {
  if (indices.length === 0) {
    return ''
  }
  const labels: string[] = indices.map((index: number): string => {
    const code: string | undefined = DAY_CODES[index]
    if (!code) {
      return String(index)
    }
    return DAY_LABELS_FR[code] ?? code
  })
  const onlyLabel: string | undefined = labels.at(0)
  if (labels.length === 1) {
    return onlyLabel ?? ''
  }
  const groups: Array<{ start: number; end: number; label: string }> = []
  let groupStart: number = 0
  for (let i: number = 1; i <= labels.length; i += 1) {
    const prevDay: number | undefined = indices.at(i - 1)
    const nextDay: number | undefined = indices.at(i)
    const consecutive: boolean =
      i < labels.length && prevDay !== undefined && nextDay !== undefined && nextDay === prevDay + 1
    if (!consecutive) {
      const startLabel: string | undefined = labels.at(groupStart)
      const endLabel: string | undefined = labels.at(i - 1)
      const startIdx: number | undefined = indices.at(groupStart)
      const endIdx: number | undefined = indices.at(i - 1)
      if (!startLabel || !endLabel || startIdx === undefined || endIdx === undefined) {
        groupStart = i
        continue
      }
      groups.push({
        start: startIdx,
        end: endIdx,
        label: groupStart === i - 1 ? startLabel : `${startLabel} au ${endLabel}`,
      })
      groupStart = i
    }
  }
  const singleGroup: { start: number; end: number; label: string } | undefined = groups.at(0)
  if (groups.length === 1) {
    return singleGroup?.label ?? ''
  }
  const last: { start: number; end: number; label: string } | undefined = groups.at(-1)
  if (!last) {
    return ''
  }
  const head: string = groups
    .slice(0, -1)
    .map((group: { label: string }): string => group.label)
    .join(', ')
  return `${head} et ${last.label}`
}

/**
 * Formate la partie jours d'une regle OSM.
 * @param {string} daySpec - Specification des jours.
 * @returns {string} Libelle francais.
 */
const formatDaySpec: (daySpec: string) => string = (daySpec: string): string => {
  const spec: string = daySpec.trim()
  if (spec === 'PH') {
    return 'jours feries'
  }
  if (/\[/.test(spec)) {
    return spec
  }
  const indices: number[] = parseDayIndices(spec)
  if (indices.length === 0) {
    return spec
  }
  return formatDayIndices(indices)
}

/**
 * Formate une regle OSM unique (ex. Tu-Sa 10:00-12:30,15:00-19:30).
 * @param {string} rule - Regle brute.
 * @returns {string | null} Ligne lisible ou null si non parsee.
 */
const formatRule: (rule: string) => string | null = (rule: string): string | null => {
  const trimmed: string = rule.trim()
  if (!trimmed) {
    return null
  }
  if (trimmed.toLowerCase() === 'off') {
    return 'Ferme'
  }

  const match: RegExpMatchArray | null = trimmed.match(/^([A-Za-z0-9,\[\]-]+)\s+(.+)$/s)
  if (!match) {
    if (isAlwaysOpen(trimmed)) {
      return 'Ouvert en continu, 24 h/24 et 7 j/7'
    }
    return trimmed
  }

  const daySpec: string = match[1] as string
  const timeSpec: string = (match[2] as string).trim()
  if (timeSpec.toLowerCase() === 'off') {
    return `${capitalize(formatDaySpec(daySpec))} : ferme`
  }

  const timeRanges: string = timeSpec
    .split(',')
    .map((part: string): string => formatTimeRange(part))
    .filter((part: string): boolean => part.length > 0)
    .join(' et ')

  return `${capitalize(formatDaySpec(daySpec))} : ${timeRanges}`
}

/**
 * Formate une valeur opening_hours OSM pour affichage en francais.
 * @param {string | null | undefined} raw - Valeur brute OSM.
 * @returns {string | null} Texte multiligne lisible ou null.
 */
export const formatOsmOpeningHoursForDisplay: (raw: string | null | undefined) => string | null = (
  raw: string | null | undefined,
): string | null => {
  if (!raw?.trim()) {
    return null
  }

  const value: string = raw.trim().replace(/;\s*$/, '')
  if (isAlwaysOpen(value)) {
    return 'Ouvert en continu, 24 h/24 et 7 j/7'
  }

  const rules: string[] = value
    .split(';')
    .map((part: string): string => part.trim())
    .filter((part: string): boolean => part.length > 0)

  const lines: string[] = rules
    .map((rule: string): string | null => formatRule(rule))
    .filter((line: string | null): line is string => Boolean(line))

  if (lines.length === 0) {
    return value
  }

  return lines.join('\n')
}
