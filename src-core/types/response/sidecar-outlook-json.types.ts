/**
 * Contrat JSON (une ligne) emis sur stdout par le binaire Python `outlook-creator`.
 * En cas d'echec, `ok` vaut false et `error` contient le message lisible.
 */
export type SidecarOutlookJsonLine = {
  ok: boolean
  email?: string
  password?: string
  firstName?: string
  lastName?: string
  birthday?: string
  error?: string
}
