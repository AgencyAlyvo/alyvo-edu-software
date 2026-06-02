import { HttpClientService } from '#src-core/services/HttpClientService'
import type { LocalBusinessStatsQuery } from '#src-core/types/payload/stats.types'
import type { LocalBusinessStatsResponse } from '#src-core/types/response/stats.types'

/**
 * Service API des statistiques business locaux.
 */
export class LocalBusinessStatsApiService {
  /**
   * Charge les statistiques business locaux.
   * @param {LocalBusinessStatsQuery} [query] - Filtre de periode optionnel.
   * @returns {Promise<LocalBusinessStatsResponse>} Statistiques business locaux.
   */
  public static async localBusiness(query?: LocalBusinessStatsQuery): Promise<LocalBusinessStatsResponse> {
    return await HttpClientService.request<LocalBusinessStatsResponse>('/stats/local-business', { query })
  }
}
