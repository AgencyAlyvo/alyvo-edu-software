import { DateTime } from 'luxon'
import { PARIS_TIME_ZONE } from '#src-nuxt/app/utils/parisTime'

/**
 * Formate l'intervalle calendaire d'une semaine ISO en francais.
 * @param {DateTime} start - Debut de semaine (lundi).
 * @param {DateTime} end - Fin de semaine (dimanche).
 * @returns {string} Plage lisible, ex. "25 au 31 mai".
 */
const formatParisWeekRange: (start: DateTime, end: DateTime) => string = (start: DateTime, end: DateTime): string => {
  const startDay: string = start.setLocale('fr').toFormat('d')
  const startMonth: string = start.setLocale('fr').toFormat('MMMM')
  const endDay: string = end.setLocale('fr').toFormat('d')
  const endMonth: string = end.setLocale('fr').toFormat('MMMM')

  if (start.month === end.month && start.year === end.year) {
    return `${startDay} au ${endDay} ${endMonth}`
  }

  return `${startDay} ${startMonth} au ${endDay} ${endMonth}`
}

/**
 * Construit le libelle affiche d'une semaine ISO (numero + plage de dates).
 * @param {string | undefined} week - Semaine ISO au format YYYY-Www.
 * @returns {string} Libelle complet, ex. "Semaine 22 - 25 au 31 mai 2026".
 */
export const formatIsoWeekDisplayLabel: (week?: string) => string = (week?: string): string => {
  if (!week) {
    return 'Semaine en cours'
  }

  const [yearPart, weekPart]: string[] = week.split('-W')
  if (!yearPart || !weekPart) {
    return week
  }

  const weekYear: number = Number.parseInt(yearPart, 10)
  const weekNumber: number = Number.parseInt(weekPart, 10)

  if (Number.isNaN(weekYear) || Number.isNaN(weekNumber)) {
    return week
  }

  const weekStart: DateTime = DateTime.fromObject({ weekYear, weekNumber }, { zone: PARIS_TIME_ZONE })
  if (!weekStart.isValid) {
    return `Semaine ${weekNumber} - ${weekYear}`
  }

  const weekEnd: DateTime = weekStart.plus({ days: 6 })
  const dateRange: string = formatParisWeekRange(weekStart, weekEnd)

  return `Semaine ${weekNumber} - ${dateRange} ${weekYear}`
}
