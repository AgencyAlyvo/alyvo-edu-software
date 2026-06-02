import type { LinkedinProspectStatus } from '#src-core/types/enums/linkedin.enums'
import type { CreateLinkedinProspectPayload } from '#src-core/types/payload/linkedin.types'
import type { ProspectAction } from '#src-core/types/response/actions.types'

/**
 * Meta de pagination Adonis.
 */
export type PaginationMeta = {
  total: number
  perPage: number
  currentPage: number
  lastPage: number
  firstPage: number
  firstPageUrl: string | null
  lastPageUrl: string | null
  nextPageUrl: string | null
  previousPageUrl: string | null
}

/**
 * Prospect LinkedIn compact.
 */
export type LinkedinProspectSummary = {
  id: number
  firstName: string
  lastName: string
  position: string | null
  company: string | null
  industry: string | null
  city: string | null
  region: string | null
  linkedinUrl: string | null
  companyLinkedinUrl: string | null
  websiteUrl: string | null
  email: string | null
  phone: string | null
  status: LinkedinProspectStatus
  isFavorite: boolean
  invitationSentAt: string | null
  invitationAcceptedAt: string | null
  message1SentAt: string | null
  repliedAt: string | null
  positiveReply: boolean
  relancesCount: number
  nextAction: string | null
  nextActionAt: string | null
  discoveryCallAt: string | null
  salesCallAt: string | null
  proposalAmount: number | null
  signedAmount: number | null
  addedAtWeek: string | null
  createdAt: string
}

/**
 * Fiche complete d'un prospect LinkedIn.
 */
export type LinkedinProspectFull = LinkedinProspectSummary & {
  country: string | null
  profileHeadline: string | null
  openToWork: boolean | null
  hiring: boolean | null
  connectionsCount: number | null
  followerCount: number | null
  companyEmployeeCountRange: string | null
  companyType: string | null
  companyTagline: string | null
  companyDescription: string | null
  relance1At: string | null
  relance2At: string | null
  relance3At: string | null
  identifiedNeed: string | null
  discoveryCallDone: boolean
  salesCallDone: boolean
  proposalSentAt: string | null
  dealWon: boolean
  signedAt: string | null
  lossReason: string | null
  updatedAt: string | null
  actions: ProspectAction[]
}

/**
 * Reponse paginee de prospects LinkedIn.
 */
export type LinkedinProspectListResponse = {
  data: LinkedinProspectSummary[]
  meta: PaginationMeta
}

/**
 * Reponse d'une fiche prospect.
 */
export type LinkedinProspectResponse = {
  data: LinkedinProspectFull
}

/**
 * Reponse d'enrichissement LinkedIn avant creation.
 */
export type LinkedinProspectEnrichmentResponse = {
  data: Partial<CreateLinkedinProspectPayload>
}
