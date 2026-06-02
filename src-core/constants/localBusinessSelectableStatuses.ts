import { LocalBusinessStatus, LocalBusinessStatusLabels } from '#src-core/types/enums/local-business.enums'
import { ProspectActionType } from '#src-core/types/enums/linkedin.enums'

/**
 * Statuts business local proposables manuellement (hors statuts internes de relance).
 */
export const localBusinessSelectableStatuses: LocalBusinessStatus[] = [
  LocalBusinessStatus.A_CONTACTER,
  LocalBusinessStatus.EMAIL_ENVOYE,
  LocalBusinessStatus.APPEL_PASSE,
  LocalBusinessStatus.NON_REPONDU,
  LocalBusinessStatus.REPONDU_INTERESSE,
  LocalBusinessStatus.REPONDU_NON_INTERESSE,
  LocalBusinessStatus.APPEL_DECOUVERTE_FAIT,
  LocalBusinessStatus.APPEL_DE_VENTE_FAIT,
  LocalBusinessStatus.PROPOSITION_ENVOYEE,
  LocalBusinessStatus.PROPOSITION_ACCEPTEE,
  LocalBusinessStatus.PROPOSITION_REFUSEE,
  LocalBusinessStatus.ARCHIVE,
]

/** Statuts proposables dans les filtres de listing. */
export const localBusinessFilterStatuses: LocalBusinessStatus[] = localBusinessSelectableStatuses

/** Statuts pour lesquels le motif de perte est pertinent en suivi commercial. */
export const localBusinessLossReasonStatuses: LocalBusinessStatus[] = [
  LocalBusinessStatus.REPONDU_NON_INTERESSE,
  LocalBusinessStatus.PROPOSITION_REFUSEE,
]

/**
 * Item de select pour les statuts.
 */
export type LocalBusinessStatusSelectItem = {
  label: string
  value: LocalBusinessStatus
}

/**
 * Construit les options de select dans l'ordre du tunnel.
 * @returns {LocalBusinessStatusSelectItem[]} Options ordonnees.
 */
export const buildLocalBusinessStatusSelectItems: () => LocalBusinessStatusSelectItem[] =
  (): LocalBusinessStatusSelectItem[] =>
    localBusinessSelectableStatuses.map(
      (status: LocalBusinessStatus): LocalBusinessStatusSelectItem => ({
        label: LocalBusinessStatusLabels[status],
        value: status,
      }),
    )

/**
 * Construit les options de filtre par statut (listing).
 * @returns {LocalBusinessStatusSelectItem[]} Options ordonnees.
 */
export const buildLocalBusinessFilterStatusSelectItems: () => LocalBusinessStatusSelectItem[] =
  (): LocalBusinessStatusSelectItem[] =>
    localBusinessFilterStatuses.map(
      (status: LocalBusinessStatus): LocalBusinessStatusSelectItem => ({
        label: LocalBusinessStatusLabels[status],
        value: status,
      }),
    )

/**
 * Couleur de badge par statut.
 */
export const localBusinessStatusBadgeStyles: Record<LocalBusinessStatus, string> = {
  [LocalBusinessStatus.A_CONTACTER]: 'bg-purple-700',
  [LocalBusinessStatus.EMAIL_ENVOYE]: 'bg-blue-700',
  [LocalBusinessStatus.APPEL_PASSE]: 'bg-blue-700',
  [LocalBusinessStatus.RELANCE_1_ENVOYEE]: 'bg-blue-700',
  [LocalBusinessStatus.RELANCE_2_ENVOYEE]: 'bg-blue-700',
  [LocalBusinessStatus.RELANCE_3_ENVOYEE]: 'bg-blue-700',
  [LocalBusinessStatus.NON_REPONDU]: 'bg-slate-700',
  [LocalBusinessStatus.REPONDU_INTERESSE]: 'bg-emerald-700',
  [LocalBusinessStatus.REPONDU_NON_INTERESSE]: 'bg-red-700',
  [LocalBusinessStatus.APPEL_DECOUVERTE_FAIT]: 'bg-emerald-700',
  [LocalBusinessStatus.APPEL_DE_VENTE_FAIT]: 'bg-emerald-700',
  [LocalBusinessStatus.PROPOSITION_ENVOYEE]: 'bg-purple-700',
  [LocalBusinessStatus.PROPOSITION_ACCEPTEE]: 'bg-emerald-700',
  [LocalBusinessStatus.PROPOSITION_REFUSEE]: 'bg-red-700',
  [LocalBusinessStatus.ARCHIVE]: 'bg-slate-700',
}

/**
 * Libelles des actions affichees dans la timeline.
 */
export const localBusinessActionTypeLabels: Partial<Record<ProspectActionType, string>> = {
  [ProspectActionType.CREATED]: 'Business cree',
  [ProspectActionType.STATUS_CHANGED]: 'Statut modifie',
  [ProspectActionType.NOTE]: 'Note ajoutee',
  [ProspectActionType.IMPORTED_FROM_OSM]: 'Importe depuis OpenStreetMap',
  [ProspectActionType.ENRICHED]: 'Enrichissement (PageSpeed + emails) effectue',
  [ProspectActionType.EMAIL_SENT]: 'Email envoye',
  [ProspectActionType.PHONE_CALL]: 'Appel telephonique passe',
  [ProspectActionType.RELANCE_1]: 'Relance 1 envoyee',
  [ProspectActionType.RELANCE_2]: 'Relance 2 envoyee',
  [ProspectActionType.RELANCE_3]: 'Relance 3 envoyee',
  [ProspectActionType.REPLY_RECEIVED]: 'Reponse recue',
  [ProspectActionType.CALL_DISCOVERY]: 'Appel decouverte fait',
  [ProspectActionType.CALL_SALES]: 'Appel de vente fait',
  [ProspectActionType.PROPOSAL_SENT]: 'Proposition envoyee',
  [ProspectActionType.PROPOSAL_ACCEPTED]: 'Proposition acceptee',
  [ProspectActionType.PROPOSAL_REFUSED]: 'Proposition refusee',
}
