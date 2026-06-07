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
}

/**
 * Resultat d'une inscription Broward reussie.
 */
export type BrowardSidecarResult = {
  accountId: number
  email: string
}
