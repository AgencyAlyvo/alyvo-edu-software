/**
 * Compte gere retourne par l'API.
 */
export type ManagedAccount = {
  id: number
  outlookEmail: string | null
  outlookFirstName: string | null
  outlookLastName: string | null
  outlookEmailPassword: string | null
  birthday: string | null
  cursorPassword: string | null
  schoolEmail: string | null
  studentId: string | null
  schoolEmailPassword: string | null
  schoolEmailActivated: boolean
  schoolRequestSent: boolean
  cursorAccountActivated: boolean
  cursorSheeridRequestSent: boolean
  schoolEmailActivatedAt: string | null
  schoolRequestSentAt: string | null
  cursorAccountActivatedAt: string | null
  cursorSheeridRequestSentAt: string | null
  createdAt: string
  updatedAt: string | null
}

/**
 *
 */
export type ManagedAccountsListResponse = {
  data: ManagedAccount[]
}

/**
 *
 */
export type ManagedAccountResponse = {
  data: ManagedAccount
}
