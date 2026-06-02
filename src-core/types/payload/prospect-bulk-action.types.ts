import type { ProspectBulkAction } from '#src-core/types/enums/prospect-bulk-action.enums'

/**
 * Corps d'une requete d'action groupée.
 */
export type ProspectBulkActionPayload = {
  ids: number[]
  action: ProspectBulkAction
}

/**
 * Reponse d'une action groupée.
 */
export type ProspectBulkActionResponse = {
  affected: number
}
