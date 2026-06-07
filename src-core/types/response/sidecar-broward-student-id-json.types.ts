/** Ligne JSON stdout du sidecar Student ID Broward. */
export type SidecarBrowardStudentIdJsonLine = {
  ok?: boolean
  skipped?: boolean
  reason?: string
  accountId?: number
  schoolEmail?: string
  studentId?: string
  schoolEmailPassword?: string | null
  error?: string
}
