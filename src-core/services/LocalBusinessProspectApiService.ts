import { HttpClientService } from '#src-core/services/HttpClientService'
import type {
  ProspectBulkActionPayload,
  ProspectBulkActionResponse,
} from '#src-core/types/payload/prospect-bulk-action.types'
import type {
  BulkImportFromOsmPayload,
  CreateLocalBusinessProspectPayload,
  ListLocalBusinessProspectsQuery,
  MarkLocalBusinessActionPayload,
  SearchOsmPayload,
  UpdateLocalBusinessProspectPayload,
} from '#src-core/types/payload/local-business.types'
import type {
  BulkImportFromOsmResponse,
  LocalBusinessProspectListResponse,
  LocalBusinessProspectResponse,
  LocalBusinessProspectSummary,
  OsmSearchResultsResponse,
} from '#src-core/types/response/local-business.types'

/**
 * Service API des business locaux (parallele de LinkedinProspectApiService).
 */
export class LocalBusinessProspectApiService {
  /**
   * Liste paginee des business locaux.
   * @param {ListLocalBusinessProspectsQuery} query - Filtres de liste.
   * @returns {Promise<LocalBusinessProspectListResponse>} Liste paginee.
   */
  public static async list(query: ListLocalBusinessProspectsQuery = {}): Promise<LocalBusinessProspectListResponse> {
    return await HttpClientService.request<LocalBusinessProspectListResponse>('/local-businesses', { query })
  }

  /**
   * Liste les business de la semaine.
   * @param {string | undefined} week - Semaine ISO optionnelle.
   * @returns {Promise<{ data: LocalBusinessProspectSummary[] }>} Liste hebdomadaire.
   */
  public static async weekly(week?: string): Promise<{ data: LocalBusinessProspectSummary[] }> {
    return await HttpClientService.request<{ data: LocalBusinessProspectSummary[] }>('/local-businesses/weekly', {
      query: week ? { week } : {},
    })
  }

  /**
   * Charge une fiche business local.
   * @param {number} id - Identifiant.
   * @returns {Promise<LocalBusinessProspectResponse>} Fiche complete.
   */
  public static async show(id: number): Promise<LocalBusinessProspectResponse> {
    return await HttpClientService.request<LocalBusinessProspectResponse>(`/local-businesses/${id}`)
  }

  /**
   * Cree un business local.
   * @param {CreateLocalBusinessProspectPayload} payload - Donnees du business.
   * @returns {Promise<{ data: LocalBusinessProspectSummary }>} Business cree.
   */
  public static async create(
    payload: CreateLocalBusinessProspectPayload,
  ): Promise<{ data: LocalBusinessProspectSummary }> {
    return await HttpClientService.request<{ data: LocalBusinessProspectSummary }>('/local-businesses', {
      method: 'POST',
      body: payload,
    })
  }

  /**
   * Met a jour un business local.
   * @param {number} id - Identifiant.
   * @param {UpdateLocalBusinessProspectPayload} payload - Donnees partielles.
   * @returns {Promise<LocalBusinessProspectResponse>} Business mis a jour (fiche complete).
   */
  public static async update(
    id: number,
    payload: UpdateLocalBusinessProspectPayload,
  ): Promise<LocalBusinessProspectResponse> {
    return await HttpClientService.request<LocalBusinessProspectResponse>(`/local-businesses/${id}`, {
      method: 'PATCH',
      body: payload,
    })
  }

  /**
   * Enrichit un business local via n8n (PageSpeed + scraping email site/Facebook).
   * @param {number} id - Identifiant.
   * @returns {Promise<LocalBusinessProspectResponse>} Business enrichi (fiche complete).
   */
  public static async enrich(id: number): Promise<LocalBusinessProspectResponse> {
    return await HttpClientService.request<LocalBusinessProspectResponse>(`/local-businesses/${id}/enrich`, {
      method: 'POST',
    })
  }

  /**
   * Supprime un business local.
   * @param {number} id - Identifiant.
   * @returns {Promise<void>}
   */
  public static async destroy(id: number): Promise<void> {
    await HttpClientService.request<void>(`/local-businesses/${id}`, { method: 'DELETE' })
  }

  /**
   * Actions groupées sur une selection de business locaux.
   * @param {ProspectBulkActionPayload} payload - Identifiants et action.
   * @returns {Promise<ProspectBulkActionResponse>} Nombre de lignes impactees.
   */
  public static async bulkAction(payload: ProspectBulkActionPayload): Promise<ProspectBulkActionResponse> {
    return await HttpClientService.request<ProspectBulkActionResponse>('/local-businesses/bulk-actions', {
      method: 'POST',
      body: payload,
    })
  }

  /**
   * Marque une action rapide (email envoye, appel passe, etc.).
   * @param {number} id - Identifiant.
   * @param {MarkLocalBusinessActionPayload} payload - Action a marquer.
   * @returns {Promise<{ data: LocalBusinessProspectSummary }>} Business synchronise.
   */
  public static async markAction(
    id: number,
    payload: MarkLocalBusinessActionPayload,
  ): Promise<{ data: LocalBusinessProspectSummary }> {
    return await HttpClientService.request<{ data: LocalBusinessProspectSummary }>(
      `/local-businesses/${id}/actions/${payload.actionType ?? ''}`,
      { method: 'POST', body: payload },
    )
  }

  /**
   * Recherche dans OSM par ville (preview avant import).
   * @param {SearchOsmPayload} payload - Query OSM.
   * @returns {Promise<OsmSearchResultsResponse>} Resultats bruts.
   */
  public static async searchOsm(payload: SearchOsmPayload): Promise<OsmSearchResultsResponse> {
    return await HttpClientService.request<OsmSearchResultsResponse>('/local-businesses/search-osm', {
      method: 'POST',
      body: payload,
    })
  }

  /**
   * Import en masse depuis OSM (apres preview).
   * @param {BulkImportFromOsmPayload} payload - Items selectionnes.
   * @returns {Promise<BulkImportFromOsmResponse>} Statistiques d'import.
   */
  public static async bulkImport(payload: BulkImportFromOsmPayload): Promise<BulkImportFromOsmResponse> {
    return await HttpClientService.request<BulkImportFromOsmResponse>('/local-businesses/bulk-import', {
      method: 'POST',
      body: payload,
    })
  }
}
