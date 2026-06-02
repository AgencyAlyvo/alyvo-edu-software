import { HttpClientService } from '#src-core/services/HttpClientService'
import type { WeeklyObjectiveResponse } from '#src-core/types/response/weekly.types'

/**
 * Service API de l'objectif hebdomadaire.
 */
export class WeeklyObjectiveApiService {
  /**
   * Charge l'objectif courant.
   * @returns {Promise<WeeklyObjectiveResponse>} Objectif courant.
   */
  public static async getCurrent(): Promise<WeeklyObjectiveResponse> {
    return await HttpClientService.request<WeeklyObjectiveResponse>('/weekly-objectives/current')
  }
}
