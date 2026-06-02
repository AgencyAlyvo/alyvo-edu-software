import { DateTime } from 'luxon'
import type { CalendarDate } from '@internationalized/date'
import { parseDate } from '@internationalized/date'
import type { DashboardDateRange, DashboardDateRangePreset } from '#src-core/types/payload/stats.types'
import { PARIS_TIME_ZONE } from '#src-nuxt/app/utils/parisTime'

/**
 * Identifiant du preset "depuis le debut".
 */
export const DASHBOARD_DATE_RANGE_ALL_ID: string = 'all'

/**
 * Formate une date ISO (YYYY-MM-DD) en libelle court francais.
 * @param {string} isoDate - Date ISO sans heure.
 * @returns {string} Libelle lisible.
 */
export const formatDashboardIsoDate: (isoDate: string) => string = (isoDate: string): string => {
  const date: DateTime = DateTime.fromISO(isoDate, { zone: PARIS_TIME_ZONE })
  return date.setLocale('fr').toFormat('d MMM yyyy')
}

/**
 * Convertit un CalendarDate en date ISO (YYYY-MM-DD).
 * @param {CalendarDate | null} date - Date du calendrier.
 * @returns {string | null} Date ISO ou null.
 */
export const calendarDateToIsoDate: (date: CalendarDate | null) => string | null = (
  date: CalendarDate | null,
): string | null => {
  if (!date) {
    return null
  }

  const year: string = String(date.year).padStart(4, '0')
  const month: string = String(date.month).padStart(2, '0')
  const day: string = String(date.day).padStart(2, '0')
  return `${year}-${month}-${day}`
}

/**
 * Convertit une date ISO (YYYY-MM-DD) en CalendarDate.
 * @param {string | null} isoDate - Date ISO sans heure.
 * @returns {CalendarDate | null} Date calendrier ou null.
 */
export const isoDateToCalendarDate: (isoDate: string | null) => CalendarDate | null = (
  isoDate: string | null,
): CalendarDate | null => {
  if (!isoDate) {
    return null
  }

  try {
    return parseDate(isoDate)
  } catch {
    return null
  }
}

/**
 * Construit un libelle lisible pour une periode dashboard.
 * @param {string | null} from - Date de debut.
 * @param {string | null} to - Date de fin.
 * @returns {string} Libelle affiche dans le bouton.
 */
export const buildDashboardDateRangeLabel: (from: string | null, to: string | null) => string = (
  from: string | null,
  to: string | null,
): string => {
  if (!from && !to) {
    return 'Depuis le debut'
  }

  if (from && to) {
    return `${formatDashboardIsoDate(from)} - ${formatDashboardIsoDate(to)}`
  }

  if (from) {
    return `Depuis le ${formatDashboardIsoDate(from)}`
  }

  return `Jusqu'au ${formatDashboardIsoDate(to!)}`
}

/**
 * Retourne la periode par defaut du dashboard (cumul global).
 * @returns {DashboardDateRange} Periode initiale.
 */
export const createDefaultDashboardDateRange: () => DashboardDateRange = (): DashboardDateRange => ({
  from: null,
  to: null,
  presetId: DASHBOARD_DATE_RANGE_ALL_ID,
  label: 'Depuis le debut',
})

/**
 * Liste les presets disponibles pour le tableau de bord LinkedIn.
 * @returns {DashboardDateRangePreset[]} Presets ordonnes.
 */
export const listDashboardDateRangePresets: () => DashboardDateRangePreset[] = (): DashboardDateRangePreset[] => {
  const now: DateTime = DateTime.now().setZone(PARIS_TIME_ZONE)
  const thisWeekStartDate: DateTime = DateTime.fromObject(
    { weekYear: now.weekYear, weekNumber: now.weekNumber },
    { zone: PARIS_TIME_ZONE },
  )
  const thisWeekStart: string = thisWeekStartDate.toISODate()!
  const thisWeekEnd: string = thisWeekStartDate.plus({ days: 6 }).toISODate()!
  const lastWeekStartDate: DateTime = thisWeekStartDate.minus({ weeks: 1 })
  const lastWeekStart: string = lastWeekStartDate.toISODate()!
  const lastWeekEnd: string = lastWeekStartDate.plus({ days: 6 }).toISODate()!
  const thisMonthStart: string = now.startOf('month').toISODate()!
  const thisMonthEnd: string = now.endOf('month').toISODate()!
  const lastMonth: DateTime = now.minus({ months: 1 })
  const lastMonthStart: string = lastMonth.startOf('month').toISODate()!
  const lastMonthEnd: string = lastMonth.endOf('month').toISODate()!
  const thisYearStart: string = now.startOf('year').toISODate()!
  const thisYearEnd: string = now.endOf('year').toISODate()!
  const lastYear: DateTime = now.minus({ years: 1 })
  const lastYearStart: string = lastYear.startOf('year').toISODate()!
  const lastYearEnd: string = lastYear.endOf('year').toISODate()!

  return [
    {
      id: DASHBOARD_DATE_RANGE_ALL_ID,
      label: 'Depuis le debut',
      from: null,
      to: null,
    },
    {
      id: 'this-week',
      label: 'Cette semaine',
      from: thisWeekStart,
      to: thisWeekEnd,
    },
    {
      id: 'last-week',
      label: 'Semaine precedente',
      from: lastWeekStart,
      to: lastWeekEnd,
    },
    {
      id: 'this-month',
      label: 'Ce mois',
      from: thisMonthStart,
      to: thisMonthEnd,
    },
    {
      id: 'last-month',
      label: 'Mois precedent',
      from: lastMonthStart,
      to: lastMonthEnd,
    },
    {
      id: 'this-year',
      label: 'Cette annee',
      from: thisYearStart,
      to: thisYearEnd,
    },
    {
      id: 'last-year',
      label: 'Annee precedente',
      from: lastYearStart,
      to: lastYearEnd,
    },
  ]
}

/**
 * Transforme une periode dashboard en query API.
 * @param {DashboardDateRange} range - Periode selectionnee.
 * @returns {{ from?: string; to?: string }} Query serialisable.
 */
export const dashboardDateRangeToQuery: (range: DashboardDateRange) => { from?: string; to?: string } = (
  range: DashboardDateRange,
): { from?: string; to?: string } => {
  if (!range.from && !range.to) {
    return {}
  }

  return {
    ...(range.from ? { from: range.from } : {}),
    ...(range.to ? { to: range.to } : {}),
  }
}

/**
 * Construit une periode dashboard depuis un preset ou une plage personnalisee.
 * @param {object} params - Parametres de construction.
 * @param {string | null} params.from - Date de debut.
 * @param {string | null} params.to - Date de fin.
 * @param {string} params.presetId - Identifiant du preset.
 * @returns {DashboardDateRange} Periode normalisee.
 */
export const createDashboardDateRange: (params: {
  from: string | null
  to: string | null
  presetId: string
}) => DashboardDateRange = (params: {
  from: string | null
  to: string | null
  presetId: string
}): DashboardDateRange => ({
  from: params.from,
  to: params.to,
  presetId: params.presetId,
  label: buildDashboardDateRangeLabel(params.from, params.to),
})
