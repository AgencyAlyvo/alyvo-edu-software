import type { LoginPayload, SignUpPayload } from '#src-core/types/payload/auth.types'
import type { SignInResponse, SignUpResponse } from '#src-core/types/response/auth.types'

/**
 * Service dédié aux appels HTTP vers les endpoints d'authentification Adonis.
 */
export class AuthApiService {
  /**
   * Résout l'URL de base de l'API depuis la configuration Nuxt runtime.
   * @returns {string} URL de base normalisée.
   */
  private static resolveBaseUrl(): string {
    const runtimeConfig: ReturnType<typeof useRuntimeConfig> = useRuntimeConfig()
    return String(runtimeConfig.public.apiBaseUrl || runtimeConfig.public.apiBase || '').replace(/\/$/, '')
  }

  /**
   * Envoie les identifiants au endpoint signin et retourne le token bearer.
   * @param {LoginPayload} payload - Email et mot de passe saisis.
   * @returns {Promise<SignInResponse>} Token bearer retourné par Adonis.
   */
  public static async signIn(payload: LoginPayload): Promise<SignInResponse> {
    const baseURL: string = this.resolveBaseUrl()

    if (!baseURL) {
      throw new Error('API base URL is not configured')
    }

    return $fetch<SignInResponse>('/signin', {
      baseURL,
      method: 'POST',
      headers: {
        Accept: 'application/json',
      },
      body: payload,
    })
  }

  /**
   * Envoie les données d'inscription au endpoint signup et retourne le token bearer.
   * @param {SignUpPayload} payload - Email, mot de passe et confirmation saisis.
   * @returns {Promise<SignUpResponse>} Token bearer retourné par Adonis.
   */
  public static async signUp(payload: SignUpPayload): Promise<SignUpResponse> {
    const baseURL: string = this.resolveBaseUrl()

    if (!baseURL) {
      throw new Error('API base URL is not configured')
    }

    return $fetch<SignUpResponse>('/signup', {
      baseURL,
      method: 'POST',
      headers: {
        Accept: 'application/json',
      },
      body: payload,
    })
  }

  /**
   * Révoque le token actif côté API via le endpoint logout.
   * @param {string} token - Token bearer à révoquer.
   * @returns {Promise<void>}
   */
  public static async signOut(token: string): Promise<void> {
    const baseURL: string = this.resolveBaseUrl()

    if (!baseURL) {
      return
    }

    await $fetch('/logout', {
      baseURL,
      method: 'DELETE',
      headers: {
        Accept: 'application/json',
        Authorization: `Bearer ${token}`,
      },
    })
  }
}
