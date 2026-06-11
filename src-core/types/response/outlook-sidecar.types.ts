/**
 * Donnees retournees au frontend apres une creation Outlook reussie via le sidecar.
 * Le mot de passe n'est pas persisté en base API.
 */
export type OutlookSidecarResult = {
  email: string
  password: string
  firstName: string
  lastName: string
  birthday: string
}

/**
 * Paire prenom / nom deja attribuee a un compte gere.
 */
export type OutlookUsedNamePair = {
  firstName: string
  lastName: string
}

/**
 * Parametres passes au sidecar pour chaque creation Outlook.
 */
export type OutlookCreationOptions = {
  password: string
  birthday: string
  /** Paires prenom/nom deja presentes en base (evite les doublons). */
  usedNamePairs?: readonly OutlookUsedNamePair[]
  /** Prenom impose (parallele) ; sinon tire au sort dans le sidecar. */
  firstName?: string
  /** Nom impose (parallele) ; sinon tire au sort dans le sidecar. */
  lastName?: string
  /** true si le flush DNS a deja ete fait par l'app avant le sidecar. */
  skipDnsFlush?: boolean
  /** Slot fenetre Chrome (0-based) dans la vague parallele. */
  windowSlot?: number
  /** Nombre d'instances Chrome simultanees pour le placement fenetre. */
  windowSlots?: number
}
