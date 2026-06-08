/** Ligne JSON stdout du sidecar Student ID Broward. */
export type SidecarBrowardStudentIdJsonLine = {
  ok?: boolean
  skipped?: boolean
  reason?: string
  accountId?: number
  schoolEmail?: string
  studentId?: string
  schoolEmailPassword?: string | null
  mybcScreenshots?: {
    studentHome: string
    prospectMenu: string
    registrationStatus: string
  }
  mybcScreenshotPaths?: {
    studentHome: string
    prospectMenu: string
    registrationStatus: string
  }
  error?: string
}
