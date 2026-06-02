import type { LinkedinProspectStatus, ProspectActionType } from '#src-core/types/enums/linkedin.enums'

/**
 * Payload de creation d'un prospect LinkedIn.
 */
export type CreateLinkedinProspectPayload = {
  firstName: string
  lastName: string
  position?: string
  company?: string
  industry?: string
  city?: string
  region?: string
  country?: string
  profileHeadline?: string
  openToWork?: boolean | null
  hiring?: boolean | null
  connectionsCount?: number | null
  followerCount?: number | null
  linkedinUrl?: string
  companyLinkedinUrl?: string
  websiteUrl?: string
  email?: string
  phone?: string
  companyEmployeeCountRange?: string
  companyType?: string
  companyTagline?: string
  companyDescription?: string
  status?: LinkedinProspectStatus
}

/**
 * Champs commerciaux modifiables sur un prospect LinkedIn.
 */
export type UpdateLinkedinProspectCommercialFields = {
  nextAction?: string | null
  nextActionAt?: string | null
  identifiedNeed?: string | null
  proposalAmount?: number | null
  signedAmount?: number | null
  lossReason?: string | null
  discoveryCallAt?: string | null
  salesCallAt?: string | null
  proposalSentAt?: string | null
  signedAt?: string | null
}

/**
 * Payload de mise a jour partielle d'un prospect LinkedIn.
 */
export type UpdateLinkedinProspectPayload = Partial<CreateLinkedinProspectPayload> &
  UpdateLinkedinProspectCommercialFields & {
    isFavorite?: boolean
  }

/**
 * Filtres du listing de prospects LinkedIn.
 */
export type ListLinkedinProspectsQuery = {
  page?: number
  perPage?: number
  search?: string
  status?: LinkedinProspectStatus[]
  isFavorite?: boolean
  week?: string
  sortBy?: 'createdAt' | 'nextActionAt' | 'invitationSentAt' | 'lastName'
  sortDir?: 'asc' | 'desc'
}

/**
 * Payload d'une action rapide sur prospect.
 */
export type MarkLinkedinActionPayload = {
  actionType?: ProspectActionType
}
