import { LinkedinProspectStatus, ProspectActionType } from '#src-core/types/enums/linkedin.enums'

/**
 * Libelle du statut "sans reponse" apres la sequence de relances.
 */
export const NON_REPONDU_LINKEDIN_LABEL: string = 'Non repondu LinkedIn apres toutes les relances'

/**
 * Libelles des statuts LinkedIn selectionnables manuellement (hors relances automatiques).
 */
export const linkedinSelectableStatusLabels: Record<LinkedinProspectStatus, string> = {
  [LinkedinProspectStatus.A_INVITER]: 'A inviter',
  [LinkedinProspectStatus.INVITATION_ENVOYEE]: 'Invitation envoyee',
  [LinkedinProspectStatus.INVITATION_ACCEPTEE]: 'Invitation acceptee',
  [LinkedinProspectStatus.MESSAGE_1_ENVOYE]: 'Message 1 envoye',
  [LinkedinProspectStatus.RELANCE_1_ENVOYEE]: 'Message 1 envoye',
  [LinkedinProspectStatus.RELANCE_2_ENVOYEE]: 'Message 1 envoye',
  [LinkedinProspectStatus.RELANCE_3_ENVOYEE]: 'Message 1 envoye',
  [LinkedinProspectStatus.NON_REPONDU_LINKEDIN]: NON_REPONDU_LINKEDIN_LABEL,
  [LinkedinProspectStatus.REPONDU_A_QUALIFIER]: 'Repondu a qualifier',
  [LinkedinProspectStatus.REPONDU_INTERESSE]: 'Repondu interesse',
  [LinkedinProspectStatus.REPONDU_NON_INTERESSE]: 'Repondu non interesse',
  [LinkedinProspectStatus.APPEL_DECOUVERTE_FAIT]: 'Appel decouverte fait',
  [LinkedinProspectStatus.APPEL_DE_VENTE_FAIT]: 'Appel de vente fait',
  [LinkedinProspectStatus.PROPOSITION_ENVOYEE]: 'Proposition envoyee',
  [LinkedinProspectStatus.PROPOSITION_ACCEPTEE]: 'Proposition acceptee',
  [LinkedinProspectStatus.PROPOSITION_REFUSEE]: 'Proposition refusee',
  [LinkedinProspectStatus.ARCHIVE]: 'Archive',
}

/**
 * Statuts LinkedIn proposables dans les listes deroulantes manuelles.
 */
export const linkedinSelectableStatuses: LinkedinProspectStatus[] = [
  LinkedinProspectStatus.A_INVITER,
  LinkedinProspectStatus.INVITATION_ENVOYEE,
  LinkedinProspectStatus.INVITATION_ACCEPTEE,
  LinkedinProspectStatus.MESSAGE_1_ENVOYE,
  LinkedinProspectStatus.NON_REPONDU_LINKEDIN,
  LinkedinProspectStatus.REPONDU_A_QUALIFIER,
  LinkedinProspectStatus.REPONDU_INTERESSE,
  LinkedinProspectStatus.REPONDU_NON_INTERESSE,
  LinkedinProspectStatus.APPEL_DECOUVERTE_FAIT,
  LinkedinProspectStatus.APPEL_DE_VENTE_FAIT,
  LinkedinProspectStatus.PROPOSITION_ENVOYEE,
  LinkedinProspectStatus.PROPOSITION_ACCEPTEE,
  LinkedinProspectStatus.PROPOSITION_REFUSEE,
  LinkedinProspectStatus.ARCHIVE,
]

/**
 * Statuts de relance automatique calcules cote backend. Affiches comme "Message 1 envoye"
 * dans le selecteur de statut pour eviter de polluer l'UI avec les etapes intermediaires.
 */
export const linkedinRelanceOnlyStatuses: LinkedinProspectStatus[] = [
  LinkedinProspectStatus.RELANCE_1_ENVOYEE,
  LinkedinProspectStatus.RELANCE_2_ENVOYEE,
  LinkedinProspectStatus.RELANCE_3_ENVOYEE,
]

/**
 * Item de liste deroulante pour un statut LinkedIn.
 */
export type LinkedinStatusSelectItem = {
  label: string
  value: LinkedinProspectStatus
}

/**
 * Construit les options de select dans l'ordre du tunnel commercial.
 * @returns {LinkedinStatusSelectItem[]} Options ordonnees.
 */
export const buildLinkedinStatusSelectItems: () => LinkedinStatusSelectItem[] = (): LinkedinStatusSelectItem[] =>
  linkedinSelectableStatuses.map(
    (status: LinkedinProspectStatus): LinkedinStatusSelectItem => ({
      label: linkedinSelectableStatusLabels[status],
      value: status,
    }),
  )

/**
 * Couleur Nuxt UI d'un badge de statut.
 */
export type LinkedinStatusBadgeColor = 'neutral' | 'primary' | 'success' | 'warning' | 'error' | 'info'

/**
 * Styles visuels des badges par statut (libelles dans linkedinSelectableStatusLabels).
 */
export const linkedinStatusBadgeStyles: Record<
  LinkedinProspectStatus,
  { color: LinkedinStatusBadgeColor; className: string }
> = {
  [LinkedinProspectStatus.A_INVITER]: { color: 'primary', className: 'bg-purple-700' },
  [LinkedinProspectStatus.INVITATION_ENVOYEE]: { color: 'info', className: 'bg-blue-700' },
  [LinkedinProspectStatus.INVITATION_ACCEPTEE]: { color: 'success', className: 'bg-emerald-700' },
  [LinkedinProspectStatus.MESSAGE_1_ENVOYE]: { color: 'info', className: 'bg-blue-700' },
  [LinkedinProspectStatus.RELANCE_1_ENVOYEE]: { color: 'info', className: 'bg-blue-700' },
  [LinkedinProspectStatus.RELANCE_2_ENVOYEE]: { color: 'info', className: 'bg-blue-700' },
  [LinkedinProspectStatus.RELANCE_3_ENVOYEE]: { color: 'info', className: 'bg-blue-700' },
  [LinkedinProspectStatus.NON_REPONDU_LINKEDIN]: { color: 'neutral', className: 'bg-slate-700' },
  [LinkedinProspectStatus.REPONDU_A_QUALIFIER]: { color: 'success', className: 'bg-emerald-700' },
  [LinkedinProspectStatus.REPONDU_INTERESSE]: { color: 'success', className: 'bg-emerald-700' },
  [LinkedinProspectStatus.REPONDU_NON_INTERESSE]: { color: 'error', className: 'bg-red-700' },
  [LinkedinProspectStatus.APPEL_DECOUVERTE_FAIT]: { color: 'success', className: 'bg-emerald-700' },
  [LinkedinProspectStatus.APPEL_DE_VENTE_FAIT]: { color: 'success', className: 'bg-emerald-700' },
  [LinkedinProspectStatus.PROPOSITION_ENVOYEE]: { color: 'primary', className: 'bg-purple-700' },
  [LinkedinProspectStatus.PROPOSITION_ACCEPTEE]: { color: 'success', className: 'bg-emerald-700' },
  [LinkedinProspectStatus.PROPOSITION_REFUSEE]: { color: 'error', className: 'bg-red-700' },
  [LinkedinProspectStatus.ARCHIVE]: { color: 'neutral', className: 'bg-slate-700' },
}

/**
 * Libelles des types d'action affiches dans la timeline.
 */
export const linkedinProspectActionTypeLabels: Partial<Record<ProspectActionType, string>> = {
  [ProspectActionType.CREATED]: 'Prospect cree',
  [ProspectActionType.STATUS_CHANGED]: 'Statut modifie',
  [ProspectActionType.NOTE]: 'Note ajoutee',
  [ProspectActionType.INVITATION_SENT]: 'Invitation LinkedIn envoyee',
  [ProspectActionType.INVITATION_ACCEPTED]: 'Invitation LinkedIn acceptee',
  [ProspectActionType.MESSAGE_SENT]: 'Message 1 envoye',
  [ProspectActionType.RELANCE_1]: 'Relance 1 envoyee',
  [ProspectActionType.RELANCE_2]: 'Relance 2 envoyee',
  [ProspectActionType.RELANCE_3]: 'Relance 3 envoyee',
  [ProspectActionType.EMAIL_SENT]: 'Email envoye',
  [ProspectActionType.REPLY_RECEIVED]: 'Reponse recue',
  [ProspectActionType.CALL_DISCOVERY]: 'Appel decouverte fait',
  [ProspectActionType.CALL_SALES]: 'Appel de vente fait',
  [ProspectActionType.PROPOSAL_SENT]: 'Proposition envoyee',
  [ProspectActionType.PROPOSAL_ACCEPTED]: 'Proposition acceptee',
  [ProspectActionType.PROPOSAL_REFUSED]: 'Proposition refusee',
}

/**
 * Libelles affiches quand aucune prochaine action n'est definie.
 */
export const linkedinTerminalNextActionLabels: Partial<Record<LinkedinProspectStatus, string>> = {
  [LinkedinProspectStatus.NON_REPONDU_LINKEDIN]: 'Aucune action suivante',
  [LinkedinProspectStatus.REPONDU_NON_INTERESSE]: 'Aucune action suivante',
  [LinkedinProspectStatus.PROPOSITION_ACCEPTEE]: 'Aucune action suivante',
  [LinkedinProspectStatus.PROPOSITION_REFUSEE]: 'Aucune action suivante',
  [LinkedinProspectStatus.ARCHIVE]: 'Aucune action suivante',
}

/** Statuts pour lesquels le motif de perte est pertinent en suivi commercial. */
export const linkedinLossReasonStatuses: LinkedinProspectStatus[] = [
  LinkedinProspectStatus.REPONDU_NON_INTERESSE,
  LinkedinProspectStatus.PROPOSITION_REFUSEE,
]
