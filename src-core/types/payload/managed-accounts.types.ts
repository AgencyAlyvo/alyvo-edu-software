/** Filtre de liste des comptes geres. */
export type ManagedAccountFilter = 'all' | 'school_active' | 'school_inactive' | 'cursor_active' | 'cursor_inactive'

/** Payload de creation d'un compte gere. */
export type CreateManagedAccountPayload = {
  outlookEmail?: string | null
  outlookFirstName?: string | null
  outlookLastName?: string | null
  outlookEmailPassword?: string | null
  birthday?: string | null
  cursorPassword?: string | null
  schoolEmail?: string | null
  studentId?: string | null
  schoolEmailPassword?: string | null
  schoolEmailActivated?: boolean
  schoolRequestSent?: boolean
  cursorAccountActivated?: boolean
  cursorSheeridRequestSent?: boolean
  schoolEmailActivatedAt?: string | null
  schoolRequestSentAt?: string | null
  cursorAccountActivatedAt?: string | null
  cursorSheeridRequestSentAt?: string | null
}

/** Payload de mise a jour d'un compte gere. */
export type UpdateManagedAccountPayload = {
  outlookEmail?: string | null
  outlookFirstName?: string | null
  outlookLastName?: string | null
  outlookEmailPassword?: string | null
  birthday?: string | null
  cursorPassword?: string | null
  schoolEmail?: string | null
  studentId?: string | null
  schoolEmailPassword?: string | null
  schoolEmailActivated?: boolean
  schoolRequestSent?: boolean
  cursorAccountActivated?: boolean
  cursorSheeridRequestSent?: boolean
  schoolEmailActivatedAt?: string | null
  schoolRequestSentAt?: string | null
  cursorAccountActivatedAt?: string | null
  cursorSheeridRequestSentAt?: string | null
}

/** Upload des captures myBC (PNG base64). */
export type UploadMybcScreenshotsPayload = {
  studentHomeBase64: string
  prospectMenuBase64: string
  registrationStatusBase64: string
}
