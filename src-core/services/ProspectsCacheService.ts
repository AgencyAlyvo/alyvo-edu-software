import { invoke } from '@tauri-apps/api/core'
import type { LinkedinProspectSummary, LinkedinProspectListResponse } from '#src-core/types/response/linkedin.types'
import type {
  LocalBusinessProspectSummary,
  LocalBusinessProspectListResponse,
} from '#src-core/types/response/local-business.types'
import type { ListLinkedinProspectsQuery } from '#src-core/types/payload/linkedin.types'
import type { ListLocalBusinessProspectsQuery } from '#src-core/types/payload/local-business.types'

/**
 * Evenement de calendrier d'appels (LinkedIn).
 */
export type LinkedinCallEvent = {
  prospect: LinkedinProspectSummary
  callType: 'discovery' | 'sales'
  dateIso: string
  hasTime: boolean
  timeLabel: string
}

/**
 * Evenement de calendrier d'appels (business local).
 */
export type LocalBusinessCallEvent = {
  prospect: LocalBusinessProspectSummary
  callType: 'discovery' | 'sales'
  dateIso: string
  hasTime: boolean
  timeLabel: string
}

let cachedAvailability: boolean | undefined

/**
 * Service de cache prospects natif (Tauri/Rust) avec fallback navigateur.
 * En mode Tauri : les prospects sont stockes dans un RwLock<Vec<Prospect>>
 * cote Rust et les filtrages/aggregations sont faits via Rayon multi-threads.
 * En mode navigateur (dev SPA) : les methodes echouent gracieusement (retour vide
 * ou no-op), les stores doivent fallback sur l'API HTTP directe.
 */
export class ProspectsCacheService {
  /**
   * Indique si le cache natif Tauri est disponible.
   * @returns {boolean} True si on tourne dans Tauri.
   */
  public static isAvailable(): boolean {
    if (cachedAvailability !== undefined) {
      return cachedAvailability
    }
    if (typeof window === 'undefined') {
      cachedAvailability = false
      return false
    }
    const tauriGlobal: unknown = (window as unknown as Record<string, unknown>).__TAURI_INTERNALS__
    cachedAvailability = tauriGlobal !== undefined && tauriGlobal !== null
    return cachedAvailability
  }

  /**
   * Tente d'executer une commande Tauri en encapsulant les erreurs.
   * En cas d'echec IPC, on logge en console.error pour que le probleme
   * soit immediatement visible en DevTools.
   * @param {string} command - Nom de la commande Tauri.
   * @param {Record<string, unknown>} args - Arguments serialises.
   * @template T
   * @returns {Promise<T | undefined>} Resultat ou undefined si indisponible/erreur.
   */
  private static async tryInvoke<T>(command: string, args?: Record<string, unknown>): Promise<T | undefined> {
    if (!this.isAvailable()) {
      return undefined
    }
    try {
      return await invoke<T>(command, args)
    } catch (error) {
      console.error(`[ProspectsCacheService] ${command} failed`, error)
      return undefined
    }
  }

  /**
   * Replace tous les prospects LinkedIn en cache.
   * @param {LinkedinProspectSummary[]} prospects - Prospects.
   * @returns {Promise<void>}
   */
  public static async linkedinSetAll(prospects: readonly LinkedinProspectSummary[]): Promise<void> {
    await this.tryInvoke<void>('linkedin_set_all', { prospects })
  }

  /**
   * Upsert un prospect LinkedIn.
   * @param {LinkedinProspectSummary} prospect - Prospect.
   * @returns {Promise<void>}
   */
  public static async linkedinUpsert(prospect: LinkedinProspectSummary): Promise<void> {
    await this.tryInvoke<void>('linkedin_upsert', { prospect })
  }

  /**
   * Upsert plusieurs prospects LinkedIn d'un coup.
   * @param {readonly LinkedinProspectSummary[]} prospects - Prospects.
   * @returns {Promise<void>}
   */
  public static async linkedinUpsertMany(prospects: readonly LinkedinProspectSummary[]): Promise<void> {
    await this.tryInvoke<void>('linkedin_upsert_many', { prospects })
  }

  /**
   * Supprime un prospect LinkedIn du cache.
   * @param {number} id - Identifiant prospect.
   * @returns {Promise<void>}
   */
  public static async linkedinRemove(id: number): Promise<void> {
    await this.tryInvoke<void>('linkedin_remove', { id })
  }

  /**
   * Vide le cache LinkedIn.
   * @returns {Promise<void>}
   */
  public static async linkedinClear(): Promise<void> {
    await this.tryInvoke<void>('linkedin_clear')
  }

  /**
   * Compte les prospects LinkedIn en cache.
   * @returns {Promise<number>} Total cache (0 si indisponible).
   */
  public static async linkedinCount(): Promise<number> {
    const value: number | undefined = await this.tryInvoke<number>('linkedin_count')
    return value ?? 0
  }

  /**
   * Interroge le cache LinkedIn avec filtres + pagination.
   * Filtrage et tri executes en parallele cote Rust.
   * @param {ListLinkedinProspectsQuery} filters - Filtres.
   * @returns {Promise<LinkedinProspectListResponse | undefined>} Slice paginee ou undefined si cache indisponible.
   */
  public static async linkedinQuery(
    filters: ListLinkedinProspectsQuery,
  ): Promise<LinkedinProspectListResponse | undefined> {
    return await this.tryInvoke<LinkedinProspectListResponse>('linkedin_query', {
      filters: {
        search: filters.search,
        statuses: filters.status,
        isFavorite: filters.isFavorite,
        week: filters.week,
        sortBy: filters.sortBy,
        sortDir: filters.sortDir,
        page: filters.page,
        perPage: filters.perPage,
      },
    })
  }

  /**
   * Filtre les prospects LinkedIn ayant un appel un jour donne.
   * @param {string} dateIso - Date au format YYYY-MM-DD (zone Paris).
   * @returns {Promise<LinkedinCallEvent[]>} Evenements ou tableau vide.
   */
  public static async linkedinCallsByDay(dateIso: string): Promise<LinkedinCallEvent[]> {
    const value: LinkedinCallEvent[] | undefined = await this.tryInvoke<LinkedinCallEvent[]>('linkedin_calls_by_day', {
      dateIso,
    })
    return value ?? []
  }

  /**
   * Filtre les prospects LinkedIn avec une echeance dans un horizon donne.
   * @param {number} horizonDays - Nombre de jours.
   * @param {string} nowIso - Instant present ISO (transmis par le JS pour coherence).
   * @returns {Promise<LinkedinProspectSummary[]>} Prospects ordonnes par echeance.
   */
  public static async linkedinTasksDue(horizonDays: number, nowIso: string): Promise<LinkedinProspectSummary[]> {
    const value: LinkedinProspectSummary[] | undefined = await this.tryInvoke<LinkedinProspectSummary[]>(
      'linkedin_tasks_due',
      { horizonDays, nowIso },
    )
    return value ?? []
  }

  /**
   * Replace tous les business locaux en cache.
   * @param {readonly LocalBusinessProspectSummary[]} prospects - Business.
   * @returns {Promise<void>}
   */
  public static async localBusinessSetAll(prospects: readonly LocalBusinessProspectSummary[]): Promise<void> {
    await this.tryInvoke<void>('local_business_set_all', { prospects })
  }

  /**
   * Upsert un business local.
   * @param {LocalBusinessProspectSummary} prospect - Business.
   * @returns {Promise<void>}
   */
  public static async localBusinessUpsert(prospect: LocalBusinessProspectSummary): Promise<void> {
    await this.tryInvoke<void>('local_business_upsert', { prospect })
  }

  /**
   * Upsert plusieurs business locaux d'un coup.
   * @param {readonly LocalBusinessProspectSummary[]} prospects - Business.
   * @returns {Promise<void>}
   */
  public static async localBusinessUpsertMany(prospects: readonly LocalBusinessProspectSummary[]): Promise<void> {
    await this.tryInvoke<void>('local_business_upsert_many', { prospects })
  }

  /**
   * Supprime un business local du cache.
   * @param {number} id - Identifiant business.
   * @returns {Promise<void>}
   */
  public static async localBusinessRemove(id: number): Promise<void> {
    await this.tryInvoke<void>('local_business_remove', { id })
  }

  /**
   * Vide le cache business local.
   * @returns {Promise<void>}
   */
  public static async localBusinessClear(): Promise<void> {
    await this.tryInvoke<void>('local_business_clear')
  }

  /**
   * Compte les business locaux en cache.
   * @returns {Promise<number>} Total cache (0 si indisponible).
   */
  public static async localBusinessCount(): Promise<number> {
    const value: number | undefined = await this.tryInvoke<number>('local_business_count')
    return value ?? 0
  }

  /**
   * Interroge le cache business locaux avec filtres + pagination.
   * @param {ListLocalBusinessProspectsQuery} filters - Filtres.
   * @returns {Promise<LocalBusinessProspectListResponse | undefined>} Slice paginee ou undefined.
   */
  public static async localBusinessQuery(
    filters: ListLocalBusinessProspectsQuery,
  ): Promise<LocalBusinessProspectListResponse | undefined> {
    return await this.tryInvoke<LocalBusinessProspectListResponse>('local_business_query', {
      filters: {
        search: filters.search,
        statuses: filters.status,
        category: filters.category,
        city: filters.city,
        region: filters.region,
        postalCode: filters.postalCode,
        hasWebsite: filters.hasWebsite,
        hasEmail: filters.hasEmail,
        hasPhone: filters.hasPhone,
        seoScoreMax: filters.seoScoreMax,
        isFavorite: filters.isFavorite,
        week: filters.week,
        sortBy: filters.sortBy,
        sortDir: filters.sortDir,
        page: filters.page,
        perPage: filters.perPage,
      },
    })
  }

  /**
   * Filtre les business locaux ayant un appel un jour donne.
   * @param {string} dateIso - YYYY-MM-DD.
   * @returns {Promise<LocalBusinessCallEvent[]>} Evenements.
   */
  public static async localBusinessCallsByDay(dateIso: string): Promise<LocalBusinessCallEvent[]> {
    const value: LocalBusinessCallEvent[] | undefined = await this.tryInvoke<LocalBusinessCallEvent[]>(
      'local_business_calls_by_day',
      { dateIso },
    )
    return value ?? []
  }

  /**
   * Filtre les business locaux avec une echeance dans un horizon donne.
   * @param {number} horizonDays - Nombre de jours.
   * @param {string} nowIso - Instant present ISO.
   * @returns {Promise<LocalBusinessProspectSummary[]>} Business ordonnes par echeance.
   */
  public static async localBusinessTasksDue(
    horizonDays: number,
    nowIso: string,
  ): Promise<LocalBusinessProspectSummary[]> {
    const value: LocalBusinessProspectSummary[] | undefined = await this.tryInvoke<LocalBusinessProspectSummary[]>(
      'local_business_tasks_due',
      { horizonDays, nowIso },
    )
    return value ?? []
  }
}
