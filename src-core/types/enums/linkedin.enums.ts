/**
 * Statuts disponibles pour un prospect LinkedIn.
 */
export enum LinkedinProspectStatus {
  A_INVITER = 'a_inviter',
  INVITATION_ENVOYEE = 'invitation_envoyee',
  INVITATION_ACCEPTEE = 'invitation_acceptee',
  MESSAGE_1_ENVOYE = 'message_1_envoye',
  RELANCE_1_ENVOYEE = 'relance_1_envoyee',
  RELANCE_2_ENVOYEE = 'relance_2_envoyee',
  RELANCE_3_ENVOYEE = 'relance_3_envoyee',
  NON_REPONDU_LINKEDIN = 'non_repondu_linkedin',
  REPONDU_A_QUALIFIER = 'repondu_a_qualifier',
  REPONDU_INTERESSE = 'repondu_interesse',
  REPONDU_NON_INTERESSE = 'repondu_non_interesse',
  APPEL_DECOUVERTE_FAIT = 'appel_decouverte_fait',
  APPEL_DE_VENTE_FAIT = 'appel_de_vente_fait',
  PROPOSITION_ENVOYEE = 'proposition_envoyee',
  PROPOSITION_ACCEPTEE = 'proposition_acceptee',
  PROPOSITION_REFUSEE = 'proposition_refusee',
  ARCHIVE = 'archive',
}

/**
 * Types d'actions journalisees dans la timeline (LinkedIn + Business locaux).
 */
export enum ProspectActionType {
  CREATED = 'created',
  STATUS_CHANGED = 'status_changed',
  NOTE = 'note',
  INVITATION_SENT = 'invitation_sent',
  INVITATION_ACCEPTED = 'invitation_accepted',
  MESSAGE_SENT = 'message_sent',
  RELANCE_1 = 'relance_1',
  RELANCE_2 = 'relance_2',
  RELANCE_3 = 'relance_3',
  EMAIL_SENT = 'email_sent',
  REPLY_RECEIVED = 'reply_received',
  CALL_DISCOVERY = 'call_discovery',
  CALL_SALES = 'call_sales',
  PROPOSAL_SENT = 'proposal_sent',
  PROPOSAL_ACCEPTED = 'proposal_accepted',
  PROPOSAL_REFUSED = 'proposal_refused',
  PHONE_CALL = 'phone_call',
  ENRICHED = 'enriched',
  IMPORTED_FROM_OSM = 'imported_from_osm',
}

/**
 * Canal utilise par une action.
 */
export enum ProspectChannel {
  LINKEDIN = 'linkedin',
}

/**
 * Type polymorphe actuellement expose cote front.
 */
export enum ProspectableType {
  LINKEDIN_PROSPECT = 'linkedin_prospect',
  LOCAL_BUSINESS_PROSPECT = 'local_business_prospect',
}
