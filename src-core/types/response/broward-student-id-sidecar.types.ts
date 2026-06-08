/** Options sidecar Student ID Broward. */
export type BrowardStudentIdOptions = {
  accountId: number
  email: string
  password: string
  birthday: string
}

/** Resultat succes sidecar Student ID. */
export type BrowardStudentIdMybcScreenshots = {
  studentHomeBase64: string
  prospectMenuBase64: string
  registrationStatusBase64: string
}

export type BrowardStudentIdSidecarResult = {
  accountId: number
  schoolEmail: string
  studentId: string
  schoolEmailPassword: string | null
  mybcScreenshots: BrowardStudentIdMybcScreenshots | null
}

/** Resultat ignore (mail absent). */
export type BrowardStudentIdSkippedResult = {
  skipped: true
  accountId: number
  reason: 'MAIL_NOT_FOUND'
}
