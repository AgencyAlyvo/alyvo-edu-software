/**
 * Parametres utilisateur LinkedIn.
 */
export type UserSettings = {
  maxInvitesPerWeek: number
  relance1DelayDays: number
  relance2DelayDays: number
  relance3DelayDays: number
}

/**
 * Reponse parametres utilisateur.
 */
export type UserSettingsResponse = {
  data: UserSettings
}
