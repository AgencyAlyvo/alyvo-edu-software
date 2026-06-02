/**
 * Filtre de periode pour les statistiques LinkedIn.
 */
export type LinkedinStatsQuery = {
  from?: string
  to?: string
}

/**
 * Filtre de periode pour les statistiques business locaux.
 */
export type LocalBusinessStatsQuery = {
  from?: string
  to?: string
}

/**
 * Periode selectionnee dans le tableau de bord LinkedIn.
 */
export type DashboardDateRange = {
  from: string | null
  to: string | null
  presetId: string
  label: string
}

/**
 * Preset de periode proposable dans le selecteur de dates.
 */
export type DashboardDateRangePreset = {
  id: string
  label: string
  from: string | null
  to: string | null
}
