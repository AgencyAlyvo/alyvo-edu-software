import { HttpClientService } from '#src-core/services/HttpClientService'
import type { UpdateUserSettingsPayload } from '#src-core/types/payload/settings.types'
import type { UserSettingsResponse } from '#src-core/types/response/settings.types'

/**
 * Service API des parametres utilisateur.
 */
export class UserSettingsApiService {
  /**
   * Charge les parametres.
   * @returns {Promise<UserSettingsResponse>} Parametres utilisateur.
   */
  public static async get(): Promise<UserSettingsResponse> {
    return await HttpClientService.request<UserSettingsResponse>('/settings')
  }

  /**
   * Met a jour les parametres.
   * @param {UpdateUserSettingsPayload} payload - Donnees de mise a jour.
   * @returns {Promise<UserSettingsResponse>} Parametres mis a jour.
   */
  public static async update(payload: UpdateUserSettingsPayload): Promise<UserSettingsResponse> {
    return await HttpClientService.request<UserSettingsResponse>('/settings', { method: 'PUT', body: payload })
  }
}
