/**
 * Donnees envoyees au sidecar Broward pour une inscription.
 */
export type BrowardEnrollmentOptions = {
  accountId: number
  firstName: string
  lastName: string
  birthday: string
  email: string
  password: string
  /** Slot fenetre Chrome (0-based) dans la vague parallele. */
  windowSlot?: number
  /** Nombre d'instances Chrome simultanees pour le placement fenetre. */
  windowSlots?: number
}

/**
 * Resultat d'une inscription Broward reussie.
 */
export type BrowardSidecarResult = {
  accountId: number
  email: string
}
