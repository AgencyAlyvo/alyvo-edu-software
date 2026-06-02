import type { ProspectActionType, ProspectChannel, ProspectableType } from '#src-core/types/enums/linkedin.enums'

/**
 * Action de timeline retournee par l'API.
 */
export type ProspectAction = {
  id: number
  prospectableType: ProspectableType
  prospectableId: number
  actionType: ProspectActionType
  channel: ProspectChannel
  content: string | null
  occurredAt: string
  createdAt: string
}

/**
 * Reponse liste de timeline.
 */
export type ProspectActionsListResponse = {
  data: ProspectAction[]
}
