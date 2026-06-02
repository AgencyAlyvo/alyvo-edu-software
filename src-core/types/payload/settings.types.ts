/**
 * Payload de mise a jour des parametres utilisateur.
 */
export type UpdateUserSettingsPayload = {
  maxInvitesPerWeek?: number
  relance1DelayDays?: number
  relance2DelayDays?: number
  relance3DelayDays?: number
}
