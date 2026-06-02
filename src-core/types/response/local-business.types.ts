import type { LocalBusinessStatus } from '#src-core/types/enums/local-business.enums'
import type { OsmSearchResult } from '#src-core/types/payload/local-business.types'
import type { ProspectAction } from '#src-core/types/response/actions.types'

/**
 * Meta de pagination (alias du LinkedIn).
 */
export type PaginationMeta = {
  total: number
  perPage: number
  currentPage: number
  lastPage: number
  firstPage?: number
  firstPageUrl?: string | null
  lastPageUrl?: string | null
  nextPageUrl?: string | null
  previousPageUrl?: string | null
}

/**
 * Business local compact.
 */
export type LocalBusinessProspectSummary = {
  id: number
  name: string
  category: string | null
  subcategory: string | null
  osmType: string | null
  osmId: string | null
  address: string | null
  city: string | null
  postalCode: string | null
  region: string | null
  country: string | null
  latitude: number | null
  longitude: number | null
  phone: string | null
  email: string | null
  emailSource: string | null
  website: string | null
  pagesJaunesUrl: string | null
  hasWebsite: boolean
  seoScore: number | null
  performanceScore: number | null
  accessibilityScore: number | null
  bestPracticesScore: number | null
  lighthouseFetchedAt: string | null
  enrichedAt: string | null
  status: LocalBusinessStatus
  isFavorite: boolean
  contactChannel: string | null
  nextAction: string | null
  nextActionAt: string | null
  firstContactAt: string | null
  relancesCount: number
  repliedAt: string | null
  positiveReply: boolean
  discoveryCallAt: string | null
  salesCallAt: string | null
  proposalAmount: number | null
  signedAmount: number | null
  addedAtWeek: string | null
  createdAt: string
}

/**
 * Fiche complete d'un business local.
 */
export type LocalBusinessProspectFull = LocalBusinessProspectSummary & {
  openingHours: string | null
  notes: string | null
  identifiedNeed: string | null
  relance1At: string | null
  relance2At: string | null
  relance3At: string | null
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
 * Reponse paginee.
 */
export type LocalBusinessProspectListResponse = {
  data: LocalBusinessProspectSummary[]
  meta: PaginationMeta
}

/**
 * Reponse d'une fiche detaillee.
 */
export type LocalBusinessProspectResponse = {
  data: LocalBusinessProspectFull
}

/**
 * Reponse de la recherche OSM (preview).
 * meta.rawCount = nb avant filtrage anti-doublon, filteredCount = nb apres exclusion des deja-importes.
 */
export type OsmSearchResultsResponse = {
  data: OsmSearchResult[]
  meta?: {
    rawCount: number
    filteredCount: number
  }
}

/**
 * Reponse de l'import en masse.
 * `enriched` compte les business pour lesquels au moins un champ vient du workflow n8n
 * (verification de site web + Pages Jaunes). 0 si le webhook n8n n'est pas configure
 * ou indisponible, auquel cas l'import retombe sur les donnees OSM brutes.
 */
export type BulkImportFromOsmResponse = {
  inserted: number
  skipped: number
  enriched: number
}
