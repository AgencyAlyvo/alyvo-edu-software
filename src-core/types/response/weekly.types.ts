/**
 * Objectif hebdomadaire LinkedIn.
 */
export type WeeklyObjective = {
  week: string
  invitesTarget: number
  invitesSent: number
  invitesRemaining: number
  progressionPercent: number
}

/**
 * Reponse objectif hebdomadaire.
 */
export type WeeklyObjectiveResponse = {
  data: WeeklyObjective
}
