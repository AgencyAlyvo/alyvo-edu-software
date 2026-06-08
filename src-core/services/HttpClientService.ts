/**
 * Client HTTP partage pour les appels API authentifies.
 */
export class HttpClientService {
  /**
   * Resout l'URL de base de l'API depuis la configuration Nuxt runtime.
   * @returns {string} URL de base sans slash final.
   */
  public static resolveBaseUrl(): string {
    const runtimeConfig: ReturnType<typeof useRuntimeConfig> = useRuntimeConfig()
    return String(runtimeConfig.public.apiBaseUrl || runtimeConfig.public.apiBase || '').replace(/\/$/, '')
  }

  /**
   * En-tetes JSON avec bearer optionnel.
   * @param {string} [token] - Jeton Bearer Adonis.
   * @returns {Record<string, string>} En-tetes HTTP.
   */
  public static authHeaders(token?: string): Record<string, string> {
    const headers: Record<string, string> = {
      Accept: 'application/json',
    }

    if (token) {
      headers.Authorization = `Bearer ${token}`
    }

    return headers
  }

  /**
   * GET authentifie.
   * @template T
   * @param {string} path - Chemin relatif de l'API.
   * @param {string} token - Jeton Bearer.
   * @param {Record<string, string>} [query] - Parametres de requete.
   * @returns {Promise<T>} Corps JSON deserialise.
   */
  public static get<T>(path: string, token: string, query?: Record<string, string>): Promise<T> {
    const baseURL: string = this.resolveBaseUrl()

    if (!baseURL) {
      throw new Error('API base URL is not configured')
    }

    const url: URL = new URL(path, `${baseURL}/`)

    if (query) {
      for (const [key, value] of Object.entries(query)) {
        url.searchParams.set(key, value)
      }
    }

    return $fetch<T>(url.toString(), {
      method: 'GET',
      headers: this.authHeaders(token),
    })
  }

  /**
   * POST authentifie.
   * @template T
   * @param {string} path - Chemin relatif de l'API.
   * @param {string} token - Jeton Bearer.
   * @param {Record<string, unknown>} [body] - Corps JSON.
   * @returns {Promise<T>} Corps JSON deserialise.
   */
  public static post<T>(path: string, token: string, body?: Record<string, unknown>): Promise<T> {
    const baseURL: string = this.resolveBaseUrl()

    if (!baseURL) {
      throw new Error('API base URL is not configured')
    }

    return $fetch<T>(`${baseURL}${path}`, {
      method: 'POST',
      headers: this.authHeaders(token),
      body,
    })
  }

  /**
   * PATCH authentifie.
   * @template T
   * @param {string} path - Chemin relatif de l'API.
   * @param {string} token - Jeton Bearer.
   * @param {Record<string, unknown>} [body] - Corps JSON.
   * @returns {Promise<T>} Corps JSON deserialise.
   */
  public static patch<T>(path: string, token: string, body?: Record<string, unknown>): Promise<T> {
    const baseURL: string = this.resolveBaseUrl()

    if (!baseURL) {
      throw new Error('API base URL is not configured')
    }

    return $fetch<T>(`${baseURL}${path}`, {
      method: 'PATCH',
      headers: this.authHeaders(token),
      body,
    })
  }

  /**
   * DELETE authentifie.
   * @param {string} path - Chemin relatif de l'API.
   * @param {string} token - Jeton Bearer.
   * @returns {Promise<void>}
   */
  /**
   * GET authentifie — reponse binaire (blob).
   */
  public static getBlob(path: string, token: string): Promise<Blob> {
    const baseURL: string = this.resolveBaseUrl()

    if (!baseURL) {
      throw new Error('API base URL is not configured')
    }

    return $fetch<Blob>(`${baseURL}${path}`, {
      method: 'GET',
      headers: this.authHeaders(token),
      responseType: 'blob',
    })
  }

  public static delete<T = void>(path: string, token: string): Promise<T> {
    const baseURL: string = this.resolveBaseUrl()

    if (!baseURL) {
      throw new Error('API base URL is not configured')
    }

    return $fetch<T>(`${baseURL}${path}`, {
      method: 'DELETE',
      headers: this.authHeaders(token),
    })
  }
}
