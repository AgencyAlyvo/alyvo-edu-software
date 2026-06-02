import { HttpClientService } from '#src-core/services/HttpClientService'
import type { LinkedinStatsQuery } from '#src-core/types/payload/stats.types'
import type { LinkedinStatsResponse } from '#src-core/types/response/stats.types'

/**
 * Service API des statistiques LinkedIn.
 */
export class LinkedinStatsApiService {
  /**
   * Charge les statistiques LinkedIn.
   * @param {LinkedinStatsQuery} [query] - Filtre de periode optionnel.
   * @returns {Promise<LinkedinStatsResponse>} Statistiques LinkedIn.
   */
  public static async linkedin(query?: LinkedinStatsQuery): Promise<LinkedinStatsResponse> {
    return await HttpClientService.request<LinkedinStatsResponse>('/stats/linkedin', { query })
  }
}
