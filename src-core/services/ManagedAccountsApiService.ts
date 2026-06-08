import { HttpClientService } from '#src-core/services/HttpClientService'
import type {
  CreateManagedAccountPayload,
  ManagedAccountFilter,
  UpdateManagedAccountPayload,
  UploadMybcScreenshotsPayload,
} from '#src-core/types/payload/managed-accounts.types'
import type {
  ManagedAccount,
  ManagedAccountResponse,
  ManagedAccountsListResponse,
} from '#src-core/types/response/managed-accounts.types'

/**
 * Appels API CRUD des comptes geres.
 */
export class ManagedAccountsApiService {
  /**
   * Liste les comptes de l'admin connecte.
   * @param {string} token - Jeton Bearer.
   * @param {ManagedAccountFilter} [filter] - Filtre de liste.
   * @returns {Promise<ManagedAccount[]>} Comptes geres.
   */
  public static list(token: string, filter: ManagedAccountFilter = 'all'): Promise<ManagedAccount[]> {
    const query: Record<string, string> = filter === 'all' ? {} : { filter }

    return HttpClientService.get<ManagedAccountsListResponse>('/accounts', token, query).then(
      (response: ManagedAccountsListResponse) => response.data,
    )
  }

  /**
   * Detail d'un compte.
   * @param {string} token - Jeton Bearer.
   * @param {number} id - Identifiant du compte.
   * @returns {Promise<ManagedAccount>} Compte demande.
   */
  public static get(token: string, id: number): Promise<ManagedAccount> {
    return HttpClientService.get<ManagedAccountResponse>(`/accounts/${id}`, token).then(
      (response: ManagedAccountResponse) => response.data,
    )
  }

  /**
   * Cree un compte.
   * @param {string} token - Jeton Bearer.
   * @param {CreateManagedAccountPayload} payload - Donnees de creation.
   * @returns {Promise<ManagedAccount>} Compte cree.
   */
  public static create(token: string, payload: CreateManagedAccountPayload): Promise<ManagedAccount> {
    return HttpClientService.post<ManagedAccountResponse>('/accounts', token, payload).then(
      (response: ManagedAccountResponse) => response.data,
    )
  }

  /**
   * Met a jour un compte.
   * @param {string} token - Jeton Bearer.
   * @param {number} id - Identifiant du compte.
   * @param {UpdateManagedAccountPayload} payload - Champs a modifier.
   * @returns {Promise<ManagedAccount>} Compte mis a jour.
   */
  public static update(token: string, id: number, payload: UpdateManagedAccountPayload): Promise<ManagedAccount> {
    return HttpClientService.patch<ManagedAccountResponse>(`/accounts/${id}`, token, payload).then(
      (response: ManagedAccountResponse) => response.data,
    )
  }

  /**
   * Supprime un compte.
   * @param {string} token - Jeton Bearer.
   * @param {number} id - Identifiant du compte.
   * @returns {Promise<void>}
   */
  public static delete(token: string, id: number): Promise<void> {
    return HttpClientService.delete(`/accounts/${id}`, token)
  }

  /**
   * Envoie les captures myBC (PNG base64) vers S3.
   */
  public static uploadMybcScreenshots(
    token: string,
    id: number,
    payload: UploadMybcScreenshotsPayload,
  ): Promise<ManagedAccount> {
    return HttpClientService.post<ManagedAccountResponse>(`/accounts/${id}/mybc-screenshots`, token, payload).then(
      (response: ManagedAccountResponse) => response.data,
    )
  }

  /**
   * Telecharge une capture myBC depuis l'API.
   */
  public static downloadMybcScreenshot(
    token: string,
    id: number,
    kind: 'student-home' | 'prospect-menu' | 'registration-status',
  ): Promise<Blob> {
    return HttpClientService.getBlob(`/accounts/${id}/mybc-screenshots/${kind}`, token)
  }

  /**
   * Supprime une capture myBC (S3 + base).
   */
  public static deleteMybcScreenshot(
    token: string,
    id: number,
    kind: 'student-home' | 'prospect-menu' | 'registration-status',
  ): Promise<ManagedAccount> {
    return HttpClientService.delete<ManagedAccountResponse>(`/accounts/${id}/mybc-screenshots/${kind}`, token).then(
      (response: ManagedAccountResponse) => response.data,
    )
  }
}
