import { HttpClientService } from '#src-core/services/HttpClientService'
import type {
  ProspectBulkActionPayload,
  ProspectBulkActionResponse,
} from '#src-core/types/payload/prospect-bulk-action.types'
import type {
  CreateLinkedinProspectPayload,
  ListLinkedinProspectsQuery,
  MarkLinkedinActionPayload,
  UpdateLinkedinProspectPayload,
} from '#src-core/types/payload/linkedin.types'
import type {
  LinkedinProspectEnrichmentResponse,
  LinkedinProspectListResponse,
  LinkedinProspectResponse,
  LinkedinProspectSummary,
} from '#src-core/types/response/linkedin.types'
import type { DueRelancesListResponse } from '#src-core/types/response/relances.types'

/**
 * Service API des prospects LinkedIn.
 */
export class LinkedinProspectApiService {
  /**
   * Liste les prospects LinkedIn.
   * @param {ListLinkedinProspectsQuery} query - Filtres de liste.
   * @returns {Promise<LinkedinProspectListResponse>} Liste paginee.
   */
  public static async list(query: ListLinkedinProspectsQuery = {}): Promise<LinkedinProspectListResponse> {
    return await HttpClientService.request<LinkedinProspectListResponse>('/linkedin-prospects', { query })
  }

  /**
   * Liste les prospects de la semaine.
   * @param {string | undefined} week - Semaine ISO optionnelle.
   * @returns {Promise<{ data: LinkedinProspectSummary[] }>} Liste hebdomadaire.
   */
  public static async weekly(week?: string): Promise<{ data: LinkedinProspectSummary[] }> {
    return await HttpClientService.request<{ data: LinkedinProspectSummary[] }>('/linkedin-prospects/weekly', {
      query: week ? { week } : {},
    })
  }

  /**
   * Liste les relances LinkedIn dues selon message1SentAt et les delais utilisateur.
   * @returns {Promise<DueRelancesListResponse>} Relances dues.
   */
  public static async dueRelances(): Promise<DueRelancesListResponse> {
    return await HttpClientService.request<DueRelancesListResponse>('/linkedin-prospects/due-relances')
  }

  /**
   * Charge une fiche prospect.
   * @param {number} id - Identifiant prospect.
   * @returns {Promise<LinkedinProspectResponse>} Fiche prospect.
   */
  public static async show(id: number): Promise<LinkedinProspectResponse> {
    return await HttpClientService.request<LinkedinProspectResponse>(`/linkedin-prospects/${id}`)
  }

  /**
   * Cree un prospect LinkedIn.
   * @param {CreateLinkedinProspectPayload} payload - Donnees prospect.
   * @returns {Promise<{ data: LinkedinProspectSummary }>} Prospect cree.
   */
  public static async create(payload: CreateLinkedinProspectPayload): Promise<{ data: LinkedinProspectSummary }> {
    return await HttpClientService.request<{ data: LinkedinProspectSummary }>('/linkedin-prospects', {
      method: 'POST',
      body: payload,
    })
  }

  /**
   * Enrichit un prospect LinkedIn depuis son URL sans le creer.
   * @param {string} linkedinUrl - URL LinkedIn du prospect.
   * @returns {Promise<LinkedinProspectEnrichmentResponse>} Donnees pre-remplies.
   */
  public static async enrich(linkedinUrl: string): Promise<LinkedinProspectEnrichmentResponse> {
    return await HttpClientService.request<LinkedinProspectEnrichmentResponse>('/linkedin-prospects/enrich', {
      method: 'POST',
      body: { linkedinUrl },
    })
  }

  /**
   * Met a jour un prospect LinkedIn.
   * @param {number} id - Identifiant prospect.
   * @param {UpdateLinkedinProspectPayload} payload - Donnees partielles.
   * @returns {Promise<LinkedinProspectResponse>} Prospect mis a jour (fiche complete).
   */
  public static async update(id: number, payload: UpdateLinkedinProspectPayload): Promise<LinkedinProspectResponse> {
    return await HttpClientService.request<LinkedinProspectResponse>(`/linkedin-prospects/${id}`, {
      method: 'PATCH',
      body: payload,
    })
  }

  /**
   * Rafraichit un prospect LinkedIn depuis n8n.
   * @param {number} id - Identifiant prospect.
   * @returns {Promise<{ data: LinkedinProspectSummary }>} Prospect mis a jour.
   */
  public static async refresh(id: number): Promise<{ data: LinkedinProspectSummary }> {
    return await HttpClientService.request<{ data: LinkedinProspectSummary }>(`/linkedin-prospects/${id}/refresh`, {
      method: 'POST',
    })
  }

  /**
   * Supprime un prospect.
   * @param {number} id - Identifiant prospect.
   * @returns {Promise<void>}
   */
  public static async destroy(id: number): Promise<void> {
    await HttpClientService.request<void>(`/linkedin-prospects/${id}`, { method: 'DELETE' })
  }

  /**
   * Actions groupées sur une selection de prospects.
   * @param {ProspectBulkActionPayload} payload - Identifiants et action.
   * @returns {Promise<ProspectBulkActionResponse>} Nombre de lignes impactees.
   */
  public static async bulkAction(payload: ProspectBulkActionPayload): Promise<ProspectBulkActionResponse> {
    return await HttpClientService.request<ProspectBulkActionResponse>('/linkedin-prospects/bulk-actions', {
      method: 'POST',
      body: payload,
    })
  }

  /**
   * Marque une action rapide.
   * @param {number} id - Identifiant prospect.
   * @param {MarkLinkedinActionPayload} payload - Action a marquer.
   * @returns {Promise<{ data: LinkedinProspectSummary }>} Prospect synchronise.
   */
  public static async markAction(
    id: number,
    payload: MarkLinkedinActionPayload,
  ): Promise<{ data: LinkedinProspectSummary }> {
    return await HttpClientService.request<{ data: LinkedinProspectSummary }>(
      `/linkedin-prospects/${id}/actions/${payload.actionType ?? ''}`,
      { method: 'POST', body: payload },
    )
  }
}
