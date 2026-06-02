import { useAuthStore } from '#src-nuxt/app/stores/auth.store'

/**
 * Options HTTP communes aux services API metier.
 */
type HttpClientRequestOptions = {
  method?: 'GET' | 'POST' | 'PATCH' | 'PUT' | 'DELETE'
  query?: Record<string, unknown>
  body?: unknown
  headers?: Record<string, string>
}

/**
 * Signature simplifiee de $fetch pour eviter l'inference des routes Nuxt dans src-core.
 */
type ApiFetch = <T>(path: string, options: HttpClientRequestOptions & { baseURL: string }) => Promise<T>

/**
 * Client HTTP authentifie pour l'API Adonis.
 */
export class HttpClientService {
  /**
   * Resout l'URL de base de l'API.
   * @returns {string} URL de base normalisee.
   */
  private static resolveBaseUrl(): string {
    const runtimeConfig: ReturnType<typeof useRuntimeConfig> = useRuntimeConfig()
    return String(runtimeConfig.public.apiBaseUrl || runtimeConfig.public.apiBase || '').replace(/\/$/, '')
  }

  /**
   * Serialise un objet de query en query string.
   * Les tableaux utilisent la notation bracket (key[]=val) attendue par qs/AdonisJS.
   * @param {Record<string, unknown>} query - Parametres a serialiser.
   * @returns {string} Query string sans le '?' initial.
   */
  private static buildQueryString(query: Record<string, unknown>): string {
    const parts: string[] = []
    for (const [key, value] of Object.entries(query)) {
      if (value === undefined || value === null) continue
      if (Array.isArray(value)) {
        for (const item of value) {
          if (item !== undefined && item !== null) {
            parts.push(`${encodeURIComponent(key)}[]=${encodeURIComponent(String(item))}`)
          }
        }
      } else {
        parts.push(`${encodeURIComponent(key)}=${encodeURIComponent(String(value))}`)
      }
    }
    return parts.join('&')
  }

  /**
   * Execute une requete API authentifiee.
   * @param {string} path - Chemin API.
   * @param {HttpClientRequestOptions} options - Options de requete.
   * @template T
   * @returns {Promise<T>} Reponse typee.
   */
  public static async request<T>(path: string, options: HttpClientRequestOptions = {}): Promise<T> {
    const baseURL: string = this.resolveBaseUrl()
    const authStore: ReturnType<typeof useAuthStore> = useAuthStore()

    if (!baseURL) {
      throw new Error('API base URL is not configured')
    }

    const apiFetch: ApiFetch = $fetch as ApiFetch

    let fullPath: string = path
    if (options.query) {
      const qs: string = this.buildQueryString(options.query)
      if (qs) fullPath = `${path}?${qs}`
    }

    return apiFetch<T>(fullPath, {
      baseURL,
      method: options.method ?? 'GET',
      body: options.body,
      headers: {
        Accept: 'application/json',
        ...(authStore.authToken ? { Authorization: `Bearer ${authStore.authToken}` } : {}),
        ...options.headers,
      },
    })
  }
}
