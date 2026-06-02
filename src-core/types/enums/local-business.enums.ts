/**
 * Statuts du tunnel de prospection des business locaux.
 */
export enum LocalBusinessStatus {
  A_CONTACTER = 'a_contacter',
  EMAIL_ENVOYE = 'email_envoye',
  APPEL_PASSE = 'appel_passe',
  RELANCE_1_ENVOYEE = 'relance_1_envoyee',
  RELANCE_2_ENVOYEE = 'relance_2_envoyee',
  RELANCE_3_ENVOYEE = 'relance_3_envoyee',
  NON_REPONDU = 'non_repondu',
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
 * Canal de prospection retenu pour un business local.
 */
export enum LocalBusinessContactChannel {
  EMAIL = 'email',
  PHONE = 'phone',
  WEBSITE_FORM = 'website_form',
  FACEBOOK = 'facebook',
}

/**
 * Origine d'une adresse email recoltee.
 */
export enum LocalBusinessEmailSource {
  OSM = 'osm',
  WEBSITE_SCRAPE = 'website_scrape',
  FACEBOOK = 'facebook',
  MANUAL = 'manual',
}

/**
 * Categorie principale (issue d'un tag OpenStreetMap).
 */
export enum LocalBusinessCategory {
  AMENITY = 'amenity',
  SHOP = 'shop',
  CRAFT = 'craft',
  OFFICE = 'office',
  HEALTHCARE = 'healthcare',
  TOURISM = 'tourism',
  LEISURE = 'leisure',
  OTHER = 'other',
}

/**
 * Libelles humains des statuts (pour les badges, filtres, etc.).
 */
export const LocalBusinessStatusLabels: Record<LocalBusinessStatus, string> = {
  [LocalBusinessStatus.A_CONTACTER]: 'A contacter',
  [LocalBusinessStatus.EMAIL_ENVOYE]: 'Email envoye',
  [LocalBusinessStatus.APPEL_PASSE]: 'Appel passe',
  [LocalBusinessStatus.RELANCE_1_ENVOYEE]: 'Relance 1 envoyee',
  [LocalBusinessStatus.RELANCE_2_ENVOYEE]: 'Relance 2 envoyee',
  [LocalBusinessStatus.RELANCE_3_ENVOYEE]: 'Relance 3 envoyee',
  [LocalBusinessStatus.NON_REPONDU]: 'Non repondu',
  [LocalBusinessStatus.REPONDU_INTERESSE]: 'Repondu (interesse)',
  [LocalBusinessStatus.REPONDU_NON_INTERESSE]: 'Repondu (non interesse)',
  [LocalBusinessStatus.APPEL_DECOUVERTE_FAIT]: 'Appel decouverte fait',
  [LocalBusinessStatus.APPEL_DE_VENTE_FAIT]: 'Appel de vente fait',
  [LocalBusinessStatus.PROPOSITION_ENVOYEE]: 'Proposition envoyee',
  [LocalBusinessStatus.PROPOSITION_ACCEPTEE]: 'Proposition acceptee',
  [LocalBusinessStatus.PROPOSITION_REFUSEE]: 'Proposition refusee',
  [LocalBusinessStatus.ARCHIVE]: 'Archive',
}

/**
 * Libelles humains des categories OSM.
 */
export const LocalBusinessCategoryLabels: Record<LocalBusinessCategory, string> = {
  [LocalBusinessCategory.AMENITY]: 'Equipement / commerce',
  [LocalBusinessCategory.SHOP]: 'Boutique',
  [LocalBusinessCategory.CRAFT]: 'Artisan',
  [LocalBusinessCategory.OFFICE]: 'Bureau',
  [LocalBusinessCategory.HEALTHCARE]: 'Sante',
  [LocalBusinessCategory.TOURISM]: 'Tourisme',
  [LocalBusinessCategory.LEISURE]: 'Loisirs',
  [LocalBusinessCategory.OTHER]: 'Autre',
}
