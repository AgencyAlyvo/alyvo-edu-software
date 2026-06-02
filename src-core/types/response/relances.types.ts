import type { LinkedinProspectSummary } from '#src-core/types/response/linkedin.types'

/**
 * Relance LinkedIn due pour un prospect.
 */
export type DueRelance = {
  prospect: LinkedinProspectSummary
  relanceNumber: 1 | 2 | 3
  dueAt: string
  message1SentAt: string
  isDue: boolean
  daysOverdue: number
}

/**
 * Reponse liste des relances dues.
 */
export type DueRelancesListResponse = {
  data: DueRelance[]
}
