import { CalendarDateTime, parseAbsolute, parseDateTime, parseDate } from '@internationalized/date'

/**
 * Fuseau horaire de reference pour toutes les dates de l'application.
 */
export const PARIS_TIME_ZONE: string = 'Europe/Paris'

/**
 * Indique si une chaine ISO contient un fuseau horaire explicite (Z ou +HH:MM).
 * @param {string} iso - Date ISO.
 * @returns {boolean} True si un offset ou Z est present.
 */
export const hasExplicitTimeZone: (iso: string) => boolean = (iso: string): boolean =>
  /(?:z|[+-]\d{2}:?\d{2})$/i.test(iso.trim())

/**
 * Parse une chaine ISO en Date JS en interpretant les chaines sans fuseau horaire
 * comme du temps local Paris (et non UTC, contrairement au comportement par defaut du moteur JS).
 * @param {string | null | undefined} iso - Date ISO optionnelle.
 * @returns {Date | null} Objet Date ou null si invalide.
 */
export const parseIsoAsParisDate: (iso: string | null | undefined) => Date | null = (
  iso: string | null | undefined,
): Date | null => {
  if (!iso) return null

  if (hasExplicitTimeZone(iso)) {
    const date: Date = new Date(iso)
    return Number.isNaN(date.getTime()) ? null : date
  }

  try {
    const trimmed: string = iso.length >= 19 ? iso.slice(0, 19) : `${iso.slice(0, 16)}:00`
    const calendar: CalendarDateTime = parseDateTime(trimmed.slice(0, 19)) as CalendarDateTime
    return calendar.toDate(PARIS_TIME_ZONE)
  } catch {
    try {
      const dateOnly: ReturnType<typeof parseDate> = parseDate(iso.slice(0, 10))
      const calendar: CalendarDateTime = new CalendarDateTime(dateOnly.year, dateOnly.month, dateOnly.day, 0, 0)
      return calendar.toDate(PARIS_TIME_ZONE)
    } catch {
      return null
    }
  }
}

/**
 * Convertit un CalendarDateTime (interpretee comme heure locale Paris) en chaine ISO UTC.
 * @param {CalendarDateTime | null} dt - Date object.
 * @returns {string | null} Chaine ISO UTC (avec Z) ou null si absente.
 */
export const calendarParisToUtcIso: (dt: CalendarDateTime | null) => string | null = (
  dt: CalendarDateTime | null,
): string | null => {
  if (!dt) return null

  return dt.toDate(PARIS_TIME_ZONE).toISOString()
}

/**
 * Convertit une chaine ISO UTC en CalendarDateTime avec l'heure murale Paris.
 * @param {string | null | undefined} iso - Date ISO optionnelle.
 * @returns {CalendarDateTime | null} CalendarDateTime au mur Paris ou null si invalide.
 */
export const utcIsoToCalendarParis: (iso: string | null | undefined) => CalendarDateTime | null = (
  iso: string | null | undefined,
): CalendarDateTime | null => {
  if (!iso) return null

  try {
    if (hasExplicitTimeZone(iso)) {
      const zoned: ReturnType<typeof parseAbsolute> = parseAbsolute(iso, PARIS_TIME_ZONE)

      return new CalendarDateTime(zoned.year, zoned.month, zoned.day, zoned.hour, zoned.minute, zoned.second)
    }

    const trimmed: string = iso.slice(0, 16)
    if (/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}$/.test(trimmed)) {
      return parseDateTime(trimmed) as CalendarDateTime
    }

    const dateOnly: ReturnType<typeof parseDate> = parseDate(iso.slice(0, 10))
    return new CalendarDateTime(dateOnly.year, dateOnly.month, dateOnly.day, 0, 0)
  } catch {
    return null
  }
}

/**
 * Formate une date ISO dans le fuseau Paris avec les options Intl fournies.
 * @param {string | null | undefined} iso - Date ISO optionnelle.
 * @param {Intl.DateTimeFormatOptions} options - Options Intl.
 * @returns {string | null} Date formatee ou null si absente.
 */
export const formatParisDate: (iso: string | null | undefined, options: Intl.DateTimeFormatOptions) => string | null = (
  iso: string | null | undefined,
  options: Intl.DateTimeFormatOptions,
): string | null => {
  const date: Date | null = parseIsoAsParisDate(iso)
  if (!date) return null

  return new Intl.DateTimeFormat('fr-FR', { timeZone: PARIS_TIME_ZONE, ...options }).format(date)
}

/**
 * Extrait l'heure (0-23) dans le fuseau Paris depuis une Date JS.
 * @param {Date} date - Date a evaluer.
 * @returns {number} Heure dans le fuseau Paris.
 */
export const getParisHour: (date: Date) => number = (date: Date): number => {
  const part: string = new Intl.DateTimeFormat('en-GB', {
    timeZone: PARIS_TIME_ZONE,
    hour: '2-digit',
    hourCycle: 'h23',
  }).format(date)

  return Number.parseInt(part, 10)
}

/**
 * Retourne l'annee, le mois et le jour d'une Date JS dans le fuseau Paris.
 * @param {Date} date - Date a evaluer.
 * @returns {{ year: number; month: number; day: number }} Composantes calendrier Paris.
 */
export const getParisDateParts: (date: Date) => { year: number; month: number; day: number } = (
  date: Date,
): { year: number; month: number; day: number } => {
  const parts: Intl.DateTimeFormatPart[] = new Intl.DateTimeFormat('en-GB', {
    timeZone: PARIS_TIME_ZONE,
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
  }).formatToParts(date)

  /**
   * Extrait une partie numerique depuis le decoupage Intl.
   * @param {Intl.DateTimeFormatPartTypes} type - Type de partie.
   * @returns {number} Valeur numerique.
   */
  const valueOf: (type: Intl.DateTimeFormatPartTypes) => number = (type: Intl.DateTimeFormatPartTypes): number =>
    Number.parseInt(parts.find((part: Intl.DateTimeFormatPart): boolean => part.type === type)?.value ?? '0', 10)

  return { year: valueOf('year'), month: valueOf('month'), day: valueOf('day') }
}

/**
 * Verifie si deux dates correspondent au meme jour calendaire en fuseau Paris.
 * @param {Date} a - Premiere date.
 * @param {Date} b - Deuxieme date.
 * @returns {boolean} True si les deux dates sont le meme jour Paris.
 */
export const isSameDayInParis: (a: Date, b: Date) => boolean = (a: Date, b: Date): boolean => {
  const partsA: { year: number; month: number; day: number } = getParisDateParts(a)
  const partsB: { year: number; month: number; day: number } = getParisDateParts(b)

  return partsA.year === partsB.year && partsA.month === partsB.month && partsA.day === partsB.day
}
