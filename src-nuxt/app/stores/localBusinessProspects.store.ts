import { defineStore } from 'pinia'
import type { Ref } from 'vue'
import { shallowRef } from 'vue'
import { mergeListQueryFilters } from '#src-core/utils/mergeListQueryFilters'
import { throttle } from '#src-core/utils/throttle'
import { ProspectsCacheService, type LocalBusinessCallEvent } from '#src-core/services/ProspectsCacheService'
import { LocalBusinessProspectApiService } from '#src-core/services/LocalBusinessProspectApiService'
import { ProspectBulkAction } from '#src-core/types/enums/prospect-bulk-action.enums'
import type {
  BulkImportFromOsmOptions,
  BulkImportFromOsmPayload,
  OsmBulkImportProgress,
  CreateLocalBusinessProspectPayload,
  ListLocalBusinessProspectsQuery,
  MarkLocalBusinessActionPayload,
  OsmSearchResult,
  SearchOsmPayload,
  UpdateLocalBusinessProspectPayload,
} from '#src-core/types/payload/local-business.types'
import type {
  LocalBusinessProspectFull,
  LocalBusinessProspectListResponse,
  LocalBusinessProspectResponse,
  LocalBusinessProspectSummary,
  OsmSearchResultsResponse,
  PaginationMeta,
} from '#src-core/types/response/local-business.types'

/**
 * Store setup interne des business locaux.
 */
type LocalBusinessProspectsStoreSetup = {
  prospects: Ref<LocalBusinessProspectSummary[]>
  weekly: Ref<LocalBusinessProspectSummary[]>
  current: Ref<LocalBusinessProspectFull | undefined>
  filters: Ref<ListLocalBusinessProspectsQuery>
  pagination: Ref<PaginationMeta | undefined>
  isLoading: Ref<boolean>
  isEnriching: Ref<boolean>
  isSyncingCache: Ref<boolean>
  cacheLoaded: Ref<boolean>
  osmPreview: Ref<OsmSearchResult[]>
  osmRawCount: Ref<number>
  isSearchingOsm: Ref<boolean>
  fetchList: (query?: ListLocalBusinessProspectsQuery) => Promise<void>
  fetchWeekly: (week?: string) => Promise<void>
  fetchOne: (id: number) => Promise<void>
  create: (payload: CreateLocalBusinessProspectPayload) => Promise<void>
  update: (
    id: number,
    payload: UpdateLocalBusinessProspectPayload,
    options?: { refreshCurrent?: boolean },
  ) => Promise<void>
  destroy: (id: number) => Promise<void>
  bulkAction: (ids: number[], action: ProspectBulkAction) => Promise<number>
  markAction: (id: number, payload: MarkLocalBusinessActionPayload) => Promise<void>
  enrich: (id: number) => Promise<void>
  searchOsm: (payload: SearchOsmPayload) => Promise<void>
  bulkImport: (
    payload: BulkImportFromOsmPayload,
    options?: BulkImportFromOsmOptions,
  ) => Promise<{ inserted: number; skipped: number; enriched: number }>
  setFilters: (query: ListLocalBusinessProspectsQuery) => void
  ensureCacheLoaded: (options?: { force?: boolean }) => Promise<void>
  aggregateCallsByDay: (dateIso: string) => Promise<LocalBusinessCallEvent[]>
  aggregateTasksDue: (horizonDays: number) => Promise<LocalBusinessProspectSummary[]>
}

/**
 * Store unwrap Pinia des business locaux.
 */
type LocalBusinessProspectsStore = {
  prospects: LocalBusinessProspectSummary[]
  weekly: LocalBusinessProspectSummary[]
  current: LocalBusinessProspectFull | undefined
  filters: ListLocalBusinessProspectsQuery
  pagination: PaginationMeta | undefined
  isLoading: boolean
  isEnriching: boolean
  isSyncingCache: boolean
  cacheLoaded: boolean
  osmPreview: OsmSearchResult[]
  osmRawCount: number
  isSearchingOsm: boolean
  fetchList: (query?: ListLocalBusinessProspectsQuery) => Promise<void>
  fetchWeekly: (week?: string) => Promise<void>
  fetchOne: (id: number) => Promise<void>
  create: (payload: CreateLocalBusinessProspectPayload) => Promise<void>
  update: (
    id: number,
    payload: UpdateLocalBusinessProspectPayload,
    options?: { refreshCurrent?: boolean },
  ) => Promise<void>
  destroy: (id: number) => Promise<void>
  bulkAction: (ids: number[], action: ProspectBulkAction) => Promise<number>
  markAction: (id: number, payload: MarkLocalBusinessActionPayload) => Promise<void>
  enrich: (id: number) => Promise<void>
  searchOsm: (payload: SearchOsmPayload) => Promise<void>
  bulkImport: (
    payload: BulkImportFromOsmPayload,
    options?: BulkImportFromOsmOptions,
  ) => Promise<{ inserted: number; skipped: number; enriched: number }>
  setFilters: (query: ListLocalBusinessProspectsQuery) => void
  ensureCacheLoaded: (options?: { force?: boolean }) => Promise<void>
  aggregateCallsByDay: (dateIso: string) => Promise<LocalBusinessCallEvent[]>
  aggregateTasksDue: (horizonDays: number) => Promise<LocalBusinessProspectSummary[]>
}

/**
 * Type callable du store business locaux.
 */
type UseLocalBusinessProspectsStore = () => LocalBusinessProspectsStore

const SYNC_PER_PAGE: number = 500

export const useLocalBusinessProspectsStore: UseLocalBusinessProspectsStore = defineStore(
  'localBusinessProspects',
  (): LocalBusinessProspectsStoreSetup => {
    const prospects: Ref<LocalBusinessProspectSummary[]> = shallowRef([])
    const weekly: Ref<LocalBusinessProspectSummary[]> = shallowRef([])
    const current: Ref<LocalBusinessProspectFull | undefined> = ref(undefined)
    const filters: Ref<ListLocalBusinessProspectsQuery> = ref({
      page: 1,
      perPage: 50,
      sortBy: 'createdAt',
      sortDir: 'desc',
    })
    const pagination: Ref<PaginationMeta | undefined> = ref(undefined)
    const isLoading: Ref<boolean> = ref(false)
    const isEnriching: Ref<boolean> = ref(false)
    const isSyncingCache: Ref<boolean> = ref(false)
    const cacheLoaded: Ref<boolean> = ref(false)
    const fullCacheFallback: Ref<LocalBusinessProspectSummary[]> = shallowRef([])
    const osmPreview: Ref<OsmSearchResult[]> = shallowRef([])
    const osmRawCount: Ref<number> = ref(0)
    const isSearchingOsm: Ref<boolean> = ref(false)

    /**
     * Injecte un business compact dans les listes locales et synchronise le cache.
     * @param {LocalBusinessProspectSummary} prospect - Prospect synchronise.
     * @returns {void}
     */
    const upsertLocal: (prospect: LocalBusinessProspectSummary) => void = (
      prospect: LocalBusinessProspectSummary,
    ): void => {
      prospects.value = [
        prospect,
        ...prospects.value.filter((item: LocalBusinessProspectSummary): boolean => item.id !== prospect.id),
      ]
      const weekList: LocalBusinessProspectSummary[] = weekly.value
      const existsInWeekly: boolean = weekList.some(
        (item: LocalBusinessProspectSummary): boolean => item.id === prospect.id,
      )
      weekly.value = existsInWeekly
        ? weekList.map(
            (item: LocalBusinessProspectSummary): LocalBusinessProspectSummary =>
              item.id === prospect.id ? prospect : item,
          )
        : weekList
      if (!ProspectsCacheService.isAvailable()) {
        const existsIndex: number = fullCacheFallback.value.findIndex(
          (item: LocalBusinessProspectSummary): boolean => item.id === prospect.id,
        )
        if (existsIndex >= 0) {
          const next: LocalBusinessProspectSummary[] = fullCacheFallback.value.slice()
          next[existsIndex] = prospect
          fullCacheFallback.value = next
        } else if (cacheLoaded.value) {
          fullCacheFallback.value = [prospect, ...fullCacheFallback.value]
        }
      }
      void ProspectsCacheService.localBusinessUpsert(prospect)
    }

    /**
     * Definit les filtres courants.
     * @param {ListLocalBusinessProspectsQuery} query - Filtres a fusionner.
     * @returns {void}
     */
    const setFilters: (query: ListLocalBusinessProspectsQuery) => void = (
      query: ListLocalBusinessProspectsQuery,
    ): void => {
      filters.value = mergeListQueryFilters(filters.value, query)
    }

    /**
     * Charge la liste paginee.
     * @param {ListLocalBusinessProspectsQuery | undefined} query - Filtres optionnels.
     * @returns {Promise<void>}
     */
    const fetchList: (query?: ListLocalBusinessProspectsQuery) => Promise<void> = async (
      query?: ListLocalBusinessProspectsQuery,
    ): Promise<void> => {
      isLoading.value = true
      try {
        setFilters(query ?? {})
        const response: LocalBusinessProspectListResponse = await LocalBusinessProspectApiService.list(filters.value)
        prospects.value = response.data
        pagination.value = response.meta
        if (response.data.length > 0) {
          void ProspectsCacheService.localBusinessUpsertMany(response.data)
        }
      } finally {
        isLoading.value = false
      }
    }

    /**
     * Charge l'integralite des business dans le cache natif Rust.
     * En mode navigateur (cache indisponible), fallback en memoire JS.
     * @param {{ force?: boolean } | undefined} options - Si force=true, recharge meme si deja en cache.
     * @param {boolean} [options.force] - Force le rechargement complet meme si le cache est deja construit.
     * @returns {Promise<void>}
     */
    const ensureCacheLoaded: (options?: { force?: boolean }) => Promise<void> = async (options?: {
      force?: boolean
    }): Promise<void> => {
      if (cacheLoaded.value && !options?.force) return
      isSyncingCache.value = true
      try {
        const cacheAvailable: boolean = ProspectsCacheService.isAvailable()
        if (cacheAvailable) {
          await ProspectsCacheService.localBusinessClear()
        }
        fullCacheFallback.value = []

        let page: number = 1
        let lastPage: number = 1
        let fetched: number = 0
        const buffer: LocalBusinessProspectSummary[] = []
        do {
          const response: LocalBusinessProspectListResponse = await LocalBusinessProspectApiService.list({
            page,
            perPage: SYNC_PER_PAGE,
            sortBy: 'createdAt',
            sortDir: 'desc',
          })
          lastPage = response.meta.lastPage
          if (response.data.length > 0) {
            fetched += response.data.length
            buffer.push(...response.data)
            if (cacheAvailable) {
              await ProspectsCacheService.localBusinessUpsertMany(response.data)
            }
          }
          page += 1
        } while (page <= lastPage)

        if (cacheAvailable && fetched > 0) {
          const cached: number = await ProspectsCacheService.localBusinessCount()
          if (cached === 0) {
            console.error(
              `[localBusinessProspects.store] cache Rust vide apres sync (${fetched} business pousses). Fallback JS active.`,
            )
            fullCacheFallback.value = buffer
          }
        } else {
          fullCacheFallback.value = buffer
        }
        cacheLoaded.value = true
      } finally {
        isSyncingCache.value = false
      }
    }

    /**
     * Charge les business de la semaine.
     * @param {string | undefined} week - Semaine ISO optionnelle.
     * @returns {Promise<void>}
     */
    const fetchWeekly: (week?: string) => Promise<void> = async (week?: string): Promise<void> => {
      isLoading.value = true
      try {
        const response: { data: LocalBusinessProspectSummary[] } | LocalBusinessProspectSummary[] =
          await LocalBusinessProspectApiService.weekly(week)
        let items: LocalBusinessProspectSummary[] = []
        if (Array.isArray(response)) {
          items = response
        } else if (Array.isArray(response.data)) {
          items = response.data
        }
        weekly.value = items
        if (items.length > 0) {
          void ProspectsCacheService.localBusinessUpsertMany(items)
        }
      } finally {
        isLoading.value = false
      }
    }

    /**
     * Charge la fiche detaillee d'un prospect.
     * @param {number} id - Identifiant du prospect.
     * @returns {Promise<void>}
     */
    const fetchOne: (id: number) => Promise<void> = async (id: number): Promise<void> => {
      isLoading.value = true
      try {
        const response: LocalBusinessProspectResponse = await LocalBusinessProspectApiService.show(id)
        current.value = response.data
      } finally {
        isLoading.value = false
      }
    }

    /**
     * Cree un prospect business local.
     * @param {CreateLocalBusinessProspectPayload} payload - Donnees de creation.
     * @returns {Promise<void>}
     */
    const create: (payload: CreateLocalBusinessProspectPayload) => Promise<void> = async (
      payload: CreateLocalBusinessProspectPayload,
    ): Promise<void> => {
      const response: { data: LocalBusinessProspectSummary } = await LocalBusinessProspectApiService.create(payload)
      upsertLocal(response.data)
    }

    /**
     * Met a jour un prospect.
     * @param {number} id - Identifiant du prospect.
     * @param {UpdateLocalBusinessProspectPayload} payload - Champs a modifier.
     * @param {{ refreshCurrent?: boolean } | undefined} options - Options de rafraichissement.
     * @param {boolean} [options.refreshCurrent] - Recharge la fiche courante.
     * @returns {Promise<void>}
     */
    const update: (
      id: number,
      payload: UpdateLocalBusinessProspectPayload,
      options?: { refreshCurrent?: boolean },
    ) => Promise<void> = async (
      id: number,
      payload: UpdateLocalBusinessProspectPayload,
      options?: { refreshCurrent?: boolean },
    ): Promise<void> => {
      const response: LocalBusinessProspectResponse = await LocalBusinessProspectApiService.update(id, payload)
      upsertLocal(response.data)
      if (options?.refreshCurrent && current.value?.id === id) {
        current.value = response.data
      }
    }

    /**
     * Supprime un prospect.
     * @param {number} id - Identifiant du prospect.
     * @returns {Promise<void>}
     */
    const destroy: (id: number) => Promise<void> = async (id: number): Promise<void> => {
      await LocalBusinessProspectApiService.destroy(id)
      prospects.value = prospects.value.filter((item: LocalBusinessProspectSummary): boolean => item.id !== id)
      weekly.value = weekly.value.filter((item: LocalBusinessProspectSummary): boolean => item.id !== id)
      if (!ProspectsCacheService.isAvailable()) {
        fullCacheFallback.value = fullCacheFallback.value.filter(
          (item: LocalBusinessProspectSummary): boolean => item.id !== id,
        )
      }
      void ProspectsCacheService.localBusinessRemove(id)
    }

    /**
     * Applique une action groupée et synchronise le store local.
     * @param {number[]} ids - Identifiants cibles.
     * @param {ProspectBulkAction} action - Action a executer.
     * @returns {Promise<number>} Nombre de lignes impactees.
     */
    const bulkAction: (ids: number[], action: ProspectBulkAction) => Promise<number> = async (
      ids: number[],
      action: ProspectBulkAction,
    ): Promise<number> => {
      const uniqueIds: number[] = [...new Set(ids)]
      if (uniqueIds.length === 0) {
        return 0
      }
      const response: { affected: number } = await LocalBusinessProspectApiService.bulkAction({
        ids: uniqueIds,
        action,
      })
      const idSet: Set<number> = new Set(uniqueIds)

      if (action === ProspectBulkAction.DELETE) {
        prospects.value = prospects.value.filter((item: LocalBusinessProspectSummary): boolean => !idSet.has(item.id))
        weekly.value = weekly.value.filter((item: LocalBusinessProspectSummary): boolean => !idSet.has(item.id))
        if (!ProspectsCacheService.isAvailable()) {
          fullCacheFallback.value = fullCacheFallback.value.filter(
            (item: LocalBusinessProspectSummary): boolean => !idSet.has(item.id),
          )
        }
        for (const id of uniqueIds) {
          void ProspectsCacheService.localBusinessRemove(id)
        }
        if (current.value && idSet.has(current.value.id)) {
          current.value = undefined
        }
        return response.affected
      }

      const isFavorite: boolean = action === ProspectBulkAction.FAVORITE
      /**
       * Met a jour le flag favori sur les business selectionnes.
       * @param {LocalBusinessProspectSummary[]} list - Liste a parcourir.
       * @returns {LocalBusinessProspectSummary[]} Liste mise a jour.
       */
      const patchList: (list: LocalBusinessProspectSummary[]) => LocalBusinessProspectSummary[] = (
        list: LocalBusinessProspectSummary[],
      ): LocalBusinessProspectSummary[] =>
        list.map(
          (item: LocalBusinessProspectSummary): LocalBusinessProspectSummary =>
            idSet.has(item.id) ? { ...item, isFavorite } : item,
        )

      prospects.value = patchList(prospects.value)
      weekly.value = patchList(weekly.value)
      if (!ProspectsCacheService.isAvailable()) {
        fullCacheFallback.value = patchList(fullCacheFallback.value)
      } else {
        const updated: LocalBusinessProspectSummary[] = prospects.value.filter(
          (item: LocalBusinessProspectSummary): boolean => idSet.has(item.id),
        )
        if (updated.length > 0) {
          void ProspectsCacheService.localBusinessUpsertMany(updated)
        }
      }
      if (current.value && idSet.has(current.value.id)) {
        current.value = { ...current.value, isFavorite }
      }
      return response.affected
    }

    /**
     * Marque une action rapide sur un prospect.
     * @param {number} id - Identifiant du prospect.
     * @param {MarkLocalBusinessActionPayload} payload - Action a journaliser.
     * @returns {Promise<void>}
     */
    const markAction: (id: number, payload: MarkLocalBusinessActionPayload) => Promise<void> = async (
      id: number,
      payload: MarkLocalBusinessActionPayload,
    ): Promise<void> => {
      const response: { data: LocalBusinessProspectSummary } = await LocalBusinessProspectApiService.markAction(
        id,
        payload,
      )
      upsertLocal(response.data)
    }

    /**
     * Lance l'enrichissement n8n d'un prospect.
     * @param {number} id - Identifiant du prospect.
     * @returns {Promise<void>}
     */
    const enrich: (id: number) => Promise<void> = async (id: number): Promise<void> => {
      isEnriching.value = true
      try {
        const response: LocalBusinessProspectResponse = await LocalBusinessProspectApiService.enrich(id)
        upsertLocal(response.data)
        if (current.value?.id === id) {
          current.value = response.data
        }
      } finally {
        isEnriching.value = false
      }
    }

    /**
     * Recherche des POI OSM par ville (preview).
     * @param {SearchOsmPayload} payload - Criteres de recherche.
     * @returns {Promise<void>}
     */
    const searchOsm: (payload: SearchOsmPayload) => Promise<void> = async (
      payload: SearchOsmPayload,
    ): Promise<void> => {
      isSearchingOsm.value = true
      try {
        const response: OsmSearchResultsResponse = await LocalBusinessProspectApiService.searchOsm(payload)
        osmPreview.value = response.data
        osmRawCount.value = response.meta?.rawCount ?? response.data.length
      } finally {
        isSearchingOsm.value = false
      }
    }

    /**
     * Importe en masse des resultats OSM valides.
     * Chaque chunk envoye au backend est enrichi cote serveur via n8n
     * (verification site web + Pages Jaunes) avant insertion.
     * @param {BulkImportFromOsmPayload} payload - Items a importer.
     * @param {BulkImportFromOsmOptions} [options] - Callback de progression optionnel.
     * @returns {Promise<{ inserted: number; skipped: number; enriched: number }>} Statistiques d'import.
     */
    const bulkImport: (
      payload: BulkImportFromOsmPayload,
      options?: BulkImportFromOsmOptions,
    ) => Promise<{ inserted: number; skipped: number; enriched: number }> = async (
      payload: BulkImportFromOsmPayload,
      options?: BulkImportFromOsmOptions,
    ): Promise<{ inserted: number; skipped: number; enriched: number }> => {
      const total: number = payload.items.length
      const BATCH_SIZE: number = options?.onProgress ? 100 : 1000
      let inserted: number = 0
      let skipped: number = 0
      let enriched: number = 0
      let processed: number = 0

      const emitProgress: (progress: OsmBulkImportProgress) => void = options?.onProgress
        ? throttle(function emitThrottledOsmImportProgress(progress: OsmBulkImportProgress): void {
            options.onProgress?.(progress)
          }, 120)
        : function noopOsmImportProgress(): void {}

      /**
       * Emet la progression courante de l'import OSM.
       * @returns {void}
       */
      const reportProgress: () => void = function reportOsmImportProgress(): void {
        emitProgress({ total, processed, inserted, skipped, enriched })
      }

      reportProgress()

      for (let offset: number = 0; offset < payload.items.length; offset += BATCH_SIZE) {
        const chunk: BulkImportFromOsmPayload['items'] = payload.items.slice(offset, offset + BATCH_SIZE)
        const stats: { inserted: number; skipped: number; enriched: number } =
          await LocalBusinessProspectApiService.bulkImport({
            items: chunk,
          })
        inserted += stats.inserted
        skipped += stats.skipped
        enriched += stats.enriched
        processed += chunk.length
        reportProgress()
      }

      if (options?.onProgress) {
        options.onProgress({ total, processed, inserted, skipped, enriched })
      }

      cacheLoaded.value = false

      return { inserted, skipped, enriched }
    }

    /**
     * Retourne les appels d'un jour via cache natif.
     * Fallback JS si cache indisponible.
     * @param {string} dateIso - YYYY-MM-DD.
     * @returns {Promise<LocalBusinessCallEvent[]>} Evenements ordonnes par heure.
     */
    const aggregateCallsByDay: (dateIso: string) => Promise<LocalBusinessCallEvent[]> = async (
      dateIso: string,
    ): Promise<LocalBusinessCallEvent[]> => {
      if (ProspectsCacheService.isAvailable()) {
        const cacheResult: LocalBusinessCallEvent[] = await ProspectsCacheService.localBusinessCallsByDay(dateIso)
        if (cacheResult.length > 0 || fullCacheFallback.value.length === 0) {
          return cacheResult
        }
      }
      const result: LocalBusinessCallEvent[] = []
      for (const prospect of fullCacheFallback.value) {
        if (prospect.discoveryCallAt?.slice(0, 10) === dateIso) {
          result.push({
            prospect,
            callType: 'discovery',
            dateIso: prospect.discoveryCallAt,
            hasTime: prospect.discoveryCallAt.length > 10,
            timeLabel: prospect.discoveryCallAt.length > 10 ? prospect.discoveryCallAt.slice(11, 16) : '',
          })
        }
        if (prospect.salesCallAt?.slice(0, 10) === dateIso) {
          result.push({
            prospect,
            callType: 'sales',
            dateIso: prospect.salesCallAt,
            hasTime: prospect.salesCallAt.length > 10,
            timeLabel: prospect.salesCallAt.length > 10 ? prospect.salesCallAt.slice(11, 16) : '',
          })
        }
      }
      return result.sort((a: LocalBusinessCallEvent, b: LocalBusinessCallEvent): number =>
        a.dateIso.localeCompare(b.dateIso),
      )
    }

    /**
     * Retourne les business avec une echeance dans l'horizon donne.
     * Fallback JS si cache indisponible.
     * @param {number} horizonDays - Nombre de jours.
     * @returns {Promise<LocalBusinessProspectSummary[]>} Business ordonnes par echeance.
     */
    const aggregateTasksDue: (horizonDays: number) => Promise<LocalBusinessProspectSummary[]> = async (
      horizonDays: number,
    ): Promise<LocalBusinessProspectSummary[]> => {
      const nowIso: string = new Date().toISOString()
      if (ProspectsCacheService.isAvailable()) {
        const cacheResult: LocalBusinessProspectSummary[] = await ProspectsCacheService.localBusinessTasksDue(
          horizonDays,
          nowIso,
        )
        if (cacheResult.length > 0 || fullCacheFallback.value.length === 0) {
          return cacheResult
        }
      }
      const now: number = Date.now()
      const horizon: number = now + horizonDays * 86_400_000
      return fullCacheFallback.value
        .filter((p: LocalBusinessProspectSummary): boolean => {
          if (!p.nextActionAt) return false
          return new Date(p.nextActionAt).getTime() <= horizon
        })
        .sort((a: LocalBusinessProspectSummary, b: LocalBusinessProspectSummary): number => {
          const at: number = a.nextActionAt ? new Date(a.nextActionAt).getTime() : Number.MAX_SAFE_INTEGER
          const bt: number = b.nextActionAt ? new Date(b.nextActionAt).getTime() : Number.MAX_SAFE_INTEGER
          return at - bt
        })
    }

    return {
      prospects,
      weekly,
      current,
      filters,
      pagination,
      isLoading,
      isEnriching,
      isSyncingCache,
      cacheLoaded,
      osmPreview,
      osmRawCount,
      isSearchingOsm,
      fetchList,
      fetchWeekly,
      fetchOne,
      create,
      update,
      destroy,
      bulkAction,
      markAction,
      enrich,
      searchOsm,
      bulkImport,
      setFilters,
      ensureCacheLoaded,
      aggregateCallsByDay,
      aggregateTasksDue,
    }
  },
)
