/**
 * Statistiques LinkedIn retournees par l'API.
 */
export type LinkedinStats = {
  invitationsSent: number
  invitationsAccepted: number
  acceptanceRate: number
  messagesSent: number
  replies: number
  replyRate: number
  positiveReplies: number
  negativeReplies: number
  positiveReplyRate: number
  discoveryCallsScheduled: number
  discoveryCallsDone: number
  salesCallsScheduled: number
  salesCallsDone: number
  appointmentRate: number
  proposalsSent: number
  proposalsAccepted: number
  proposalsRefused: number
  closingRate: number
  totalProposalAmount: number
  totalSignedAmount: number
}

/**
 * Reponse statistiques LinkedIn.
 */
export type LinkedinStatsResponse = {
  data: LinkedinStats
}

/**
 * Statistiques business locaux retournees par l'API.
 */
export type LocalBusinessStats = {
  totalProspects: number
  withEmail: number
  withPhone: number
  withWebsite: number
  enriched: number
  emailsSent: number
  callsMade: number
  contactsMade: number
  positiveReplies: number
  negativeReplies: number
  replyRate: number
  positiveReplyRate: number
  discoveryCallsDone: number
  salesCallsDone: number
  proposalsSent: number
  proposalsAccepted: number
  proposalsRefused: number
  closingRate: number
  totalProposalAmount: number
  totalSignedAmount: number
  lighthouseAnalyzed: number
  averageSeoScore: number
  averagePerformanceScore: number
  averageAccessibilityScore: number
  averageBestPracticesScore: number
}

/**
 * Reponse statistiques business locaux.
 */
export type LocalBusinessStatsResponse = {
  data: LocalBusinessStats
}
