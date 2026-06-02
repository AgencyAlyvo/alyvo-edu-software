import type {
  LocalBusinessContactChannel,
  LocalBusinessEmailSource,
  LocalBusinessStatus,
} from '#src-core/types/enums/local-business.enums'
import type { ProspectActionType } from '#src-core/types/enums/linkedin.enums'

/**
 * Payload de creation d'un business local.
 */
export type CreateLocalBusinessProspectPayload = {
  name: string
  category?: string | null
  subcategory?: string | null
  osmType?: string | null
  osmId?: string | null
  address?: string | null
  city?: string | null
  postalCode?: string | null
  region?: string | null
  country?: string | null
  latitude?: number | null
  longitude?: number | null
  phone?: string | null
  email?: string | null
  emailSource?: LocalBusinessEmailSource | null
  website?: string | null
  pagesJaunesUrl?: string | null
  openingHours?: string | null
  contactChannel?: LocalBusinessContactChannel | null
  notes?: string | null
  status?: LocalBusinessStatus
}

/**
 * Champs commerciaux et scores modifiables.
 */
export type UpdateLocalBusinessProspectCommercialFields = {
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
  seoScore?: number | null
  performanceScore?: number | null
  accessibilityScore?: number | null
  bestPracticesScore?: number | null
}

/**
 * Payload de mise a jour partielle d'un business local.
 */
export type UpdateLocalBusinessProspectPayload = Partial<CreateLocalBusinessProspectPayload> &
  UpdateLocalBusinessProspectCommercialFields & {
    isFavorite?: boolean
  }

/**
 * Filtres du listing.
 */
export type ListLocalBusinessProspectsQuery = {
  page?: number
  perPage?: number
  search?: string
  status?: LocalBusinessStatus[]
  category?: string
  city?: string
  region?: string
  postalCode?: string
  hasWebsite?: boolean
  hasEmail?: boolean
  hasPhone?: boolean
  seoScoreMax?: number
  isFavorite?: boolean
  week?: string
  sortBy?: 'createdAt' | 'nextActionAt' | 'name' | 'seoScore' | 'performanceScore'
  sortDir?: 'asc' | 'desc'
}

/**
 * Payload d'une action rapide.
 */
export type MarkLocalBusinessActionPayload = {
  actionType?: ProspectActionType
}

/**
 * Payload de recherche dans OSM (preview avant import).
 */
export type SearchOsmPayload = {
  city: string
  category?: string
  /** Plafond optionnel ; omis = tous les POI correspondants dans le .pbf */
  limit?: number
}

/**
 * Resultat brut d'une recherche OSM.
 */
export type OsmSearchResult = {
  osmType: string
  osmId: string
  name: string
  category: string | null
  subcategory: string | null
  address: string | null
  city: string | null
  postalCode: string | null
  region: string | null
  latitude: number | null
  longitude: number | null
  phone: string | null
  email: string | null
  website: string | null
  openingHours: string | null
}

/**
 * Payload d'import en masse depuis OSM.
 */
export type BulkImportFromOsmPayload = {
  items: OsmSearchResult[]
}

/**
 * Progression d'un import OSM (lots envoyes au backend).
 * `enriched` est le cumul des business pour lesquels n8n a enrichi au moins un champ.
 */
export type OsmBulkImportProgress = {
  total: number
  processed: number
  inserted: number
  skipped: number
  enriched: number
}

/**
 * Options de l'import OSM en masse.
 */
export type BulkImportFromOsmOptions = {
  onProgress?: (progress: OsmBulkImportProgress) => void
}
