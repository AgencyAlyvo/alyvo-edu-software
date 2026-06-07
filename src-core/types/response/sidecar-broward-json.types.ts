/**
 * Ligne JSON finale sur stdout du sidecar broward-enrollment.
 */
export type SidecarBrowardJsonLine = {
  ok: boolean
  accountId?: number
  email?: string
  error?: string
}
