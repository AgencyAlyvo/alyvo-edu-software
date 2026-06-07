/** Options sidecar Student ID Broward. */
export type BrowardStudentIdOptions = {
  accountId: number
  email: string
  password: string
  birthday: string
}

/** Resultat succes sidecar Student ID. */
export type BrowardStudentIdSidecarResult = {
  accountId: number
  schoolEmail: string
  studentId: string
  schoolEmailPassword: string | null
}

/** Resultat ignore (mail absent). */
export type BrowardStudentIdSkippedResult = {
  skipped: true
  accountId: number
  reason: 'MAIL_NOT_FOUND'
}
