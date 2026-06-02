import { defineStore } from 'pinia'
import type { Ref } from 'vue'
import { shallowRef } from 'vue'
import { ProspectsCacheService, type LinkedinCallEvent } from '#src-core/services/ProspectsCacheService'
import { mergeListQueryFilters } from '#src-core/utils/mergeListQueryFilters'
import { LinkedinProspectApiService } from '#src-core/services/LinkedinProspectApiService'
import { ProspectBulkAction } from '#src-core/types/enums/prospect-bulk-action.enums'
import type {
  CreateLinkedinProspectPayload,
  ListLinkedinProspectsQuery,
  MarkLinkedinActionPayload,
  UpdateLinkedinProspectPayload,
} from '#src-core/types/payload/linkedin.types'
import type {
  LinkedinProspectFull,
  LinkedinProspectEnrichmentResponse,
  LinkedinProspectListResponse,
  LinkedinProspectResponse,
  LinkedinProspectSummary,
  PaginationMeta,
} from '#src-core/types/response/linkedin.types'

/**
 * Store unwrap Pinia des prospects LinkedIn.
 */
type LinkedinProspectsStore = {
  prospects: LinkedinProspectSummary[]
  weekly: LinkedinProspectSummary[]
  current: LinkedinProspectFull | undefined
  filters: ListLinkedinProspectsQuery
  pagination: PaginationMeta | undefined
  isLoading: boolean
  isSyncingCache: boolean
  cacheLoaded: boolean
  fetchList: (query?: ListLinkedinProspectsQuery) => Promise<void>
  fetchWeekly: (week?: string) => Promise<void>
  fetchOne: (id: number) => Promise<void>
  enrich: (linkedinUrl: string) => Promise<Partial<CreateLinkedinProspectPayload>>
  create: (payload: CreateLinkedinProspectPayload) => Promise<void>
  update: (id: number, payload: UpdateLinkedinProspectPayload, options?: { refreshCurrent?: boolean }) => Promise<void>
  refresh: (id: number) => Promise<void>
  destroy: (id: number) => Promise<void>
  bulkAction: (ids: number[], action: ProspectBulkAction) => Promise<number>
  markAction: (id: number, payload: MarkLinkedinActionPayload) => Promise<void>
  setFilters: (query: ListLinkedinProspectsQuery) => void
  ensureCacheLoaded: (options?: { force?: boolean }) => Promise<void>
  aggregateCallsByDay: (dateIso: string) => Promise<LinkedinCallEvent[]>
  aggregateTasksDue: (horizonDays: number) => Promise<LinkedinProspectSummary[]>
}

/**
 * Store setup interne des prospects LinkedIn.
 */
type LinkedinProspectsStoreSetup = {
  prospects: Ref<LinkedinProspectSummary[]>
  weekly: Ref<LinkedinProspectSummary[]>
  current: Ref<LinkedinProspectFull | undefined>
  filters: Ref<ListLinkedinProspectsQuery>
  pagination: Ref<PaginationMeta | undefined>
  isLoading: Ref<boolean>
  isSyncingCache: Ref<boolean>
  cacheLoaded: Ref<boolean>
  fetchList: (query?: ListLinkedinProspectsQuery) => Promise<void>
  fetchWeekly: (week?: string) => Promise<void>
  fetchOne: (id: number) => Promise<void>
  enrich: (linkedinUrl: string) => Promise<Partial<CreateLinkedinProspectPayload>>
  create: (payload: CreateLinkedinProspectPayload) => Promise<void>
  update: (id: number, payload: UpdateLinkedinProspectPayload, options?: { refreshCurrent?: boolean }) => Promise<void>
  refresh: (id: number) => Promise<void>
  destroy: (id: number) => Promise<void>
  bulkAction: (ids: number[], action: ProspectBulkAction) => Promise<number>
  markAction: (id: number, payload: MarkLinkedinActionPayload) => Promise<void>
  setFilters: (query: ListLinkedinProspectsQuery) => void
  ensureCacheLoaded: (options?: { force?: boolean }) => Promise<void>
  aggregateCallsByDay: (dateIso: string) => Promise<LinkedinCallEvent[]>
  aggregateTasksDue: (horizonDays: number) => Promise<LinkedinProspectSummary[]>
}

/**
 * Type callable du store prospects.
 */
type UseLinkedinProspectsStore = () => LinkedinProspectsStore

const SYNC_PER_PAGE: number = 500

export const useLinkedinProspectsStore: UseLinkedinProspectsStore = defineStore(
  'linkedinProspects',
  (): LinkedinProspectsStoreSetup => {
    const prospects: Ref<LinkedinProspectSummary[]> = shallowRef([])
    const weekly: Ref<LinkedinProspectSummary[]> = shallowRef([])
    const current: Ref<LinkedinProspectFull | undefined> = ref(undefined)
    const filters: Ref<ListLinkedinProspectsQuery> = ref({
      page: 1,
      perPage: 50,
      sortBy: 'createdAt',
      sortDir: 'desc',
    })
    const pagination: Ref<PaginationMeta | undefined> = ref(undefined)
    const isLoading: Ref<boolean> = ref(false)
    const isSyncingCache: Ref<boolean> = ref(false)
    const cacheLoaded: Ref<boolean> = ref(false)
    const fullCacheFallback: Ref<LinkedinProspectSummary[]> = shallowRef([])

    /**
     * Injecte un prospect compact dans les listes locales et synchronise le cache.
     * @param {LinkedinProspectSummary} prospect - Prospect synchronise.
     * @returns {void}
     */
    const upsertLocal: (prospect: LinkedinProspectSummary) => void = (prospect: LinkedinProspectSummary): void => {
      prospects.value = [
        prospect,
        ...prospects.value.filter((item: LinkedinProspectSummary): boolean => item.id !== prospect.id),
      ]
      const weekList: LinkedinProspectSummary[] = weekly.value
      const existsInWeekly: boolean = weekList.some((item: LinkedinProspectSummary): boolean => item.id === prospect.id)
      weekly.value = existsInWeekly
        ? weekList.map(
            (item: LinkedinProspectSummary): LinkedinProspectSummary => (item.id === prospect.id ? prospect : item),
          )
        : weekList
      if (!ProspectsCacheService.isAvailable()) {
        const existsIndex: number = fullCacheFallback.value.findIndex(
          (item: LinkedinProspectSummary): boolean => item.id === prospect.id,
        )
        if (existsIndex >= 0) {
          const next: LinkedinProspectSummary[] = fullCacheFallback.value.slice()
          next[existsIndex] = prospect
          fullCacheFallback.value = next
        } else if (cacheLoaded.value) {
          fullCacheFallback.value = [prospect, ...fullCacheFallback.value]
        }
      }
      void ProspectsCacheService.linkedinUpsert(prospect)
    }

    /**
     * Definit les filtres courants.
     * @param {ListLinkedinProspectsQuery} query - Filtres a fusionner.
     * @returns {void}
     */
    const setFilters: (query: ListLinkedinProspectsQuery) => void = (query: ListLinkedinProspectsQuery): void => {
      filters.value = mergeListQueryFilters(filters.value, query)
    }

    /**
     * Charge la liste paginee depuis l'API et synchronise le cache.
     * @param {ListLinkedinProspectsQuery | undefined} query - Filtres optionnels.
     * @returns {Promise<void>}
     */
    const fetchList: (query?: ListLinkedinProspectsQuery) => Promise<void> = async (
      query?: ListLinkedinProspectsQuery,
    ): Promise<void> => {
      isLoading.value = true
      try {
        if (query?.week !== undefined) {
          filters.value = {
            page: query.page ?? 1,
            perPage: query.perPage ?? filters.value.perPage ?? 50,
            sortBy: query.sortBy ?? 'createdAt',
            sortDir: query.sortDir ?? 'desc',
            week: query.week,
          }
        } else {
          setFilters(query ?? {})
        }
        const response: LinkedinProspectListResponse = await LinkedinProspectApiService.list(filters.value)
        prospects.value = response.data
        pagination.value = response.meta
        if (response.data.length > 0) {
          void ProspectsCacheService.linkedinUpsertMany(response.data)
        }
      } finally {
        isLoading.value = false
      }
    }

    /**
     * Charge la totalite des prospects dans le cache natif Rust (paginations en streaming).
     * Les donnees ne sont PAS gardees en memoire JS pour eviter les crashs de rendu.
     * En mode navigateur (cache indisponible), fallback : conserve une copie en
     * memoire JS pour permettre les aggregations en JS.
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
          await ProspectsCacheService.linkedinClear()
        }
        fullCacheFallback.value = []

        let page: number = 1
        let lastPage: number = 1
        let fetched: number = 0
        const buffer: LinkedinProspectSummary[] = []
        do {
          const response: LinkedinProspectListResponse = await LinkedinProspectApiService.list({
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
              await ProspectsCacheService.linkedinUpsertMany(response.data)
            }
          }
          page += 1
        } while (page <= lastPage)

        if (cacheAvailable && fetched > 0) {
          const cached: number = await ProspectsCacheService.linkedinCount()
          if (cached === 0) {
            console.error(
              `[linkedinProspects.store] cache Rust vide apres sync (${fetched} prospects pousses). Fallback JS active.`,
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
     * Charge les prospects de la semaine.
     * @param {string | undefined} week - Semaine ISO optionnelle.
     * @returns {Promise<void>}
     */
    const fetchWeekly: (week?: string) => Promise<void> = async (week?: string): Promise<void> => {
      isLoading.value = true
      try {
        const response: { data: LinkedinProspectSummary[] } | LinkedinProspectSummary[] =
          await LinkedinProspectApiService.weekly(week)
        let items: LinkedinProspectSummary[] = []
        if (Array.isArray(response)) {
          items = response
        } else if (Array.isArray(response.data)) {
          items = response.data
        }
        weekly.value = items
        if (items.length > 0) {
          void ProspectsCacheService.linkedinUpsertMany(items)
        }
      } finally {
        isLoading.value = false
      }
    }

    /**
     * Charge une fiche prospect.
     * @param {number} id - Identifiant prospect.
     * @returns {Promise<void>}
     */
    const fetchOne: (id: number) => Promise<void> = async (id: number): Promise<void> => {
      isLoading.value = true
      try {
        const response: LinkedinProspectResponse = await LinkedinProspectApiService.show(id)
        current.value = response.data
      } finally {
        isLoading.value = false
      }
    }

    /**
     * Enrichit un prospect depuis son URL LinkedIn.
     * @param {string} linkedinUrl - URL LinkedIn a analyser.
     * @returns {Promise<Partial<CreateLinkedinProspectPayload>>} Donnees detectees.
     */
    const enrich: (linkedinUrl: string) => Promise<Partial<CreateLinkedinProspectPayload>> = async (
      linkedinUrl: string,
    ): Promise<Partial<CreateLinkedinProspectPayload>> => {
      const response: LinkedinProspectEnrichmentResponse = await LinkedinProspectApiService.enrich(linkedinUrl)
      return response.data
    }

    /**
     * Cree un prospect puis recharge la liste locale.
     * @param {CreateLinkedinProspectPayload} payload - Donnees prospect.
     * @returns {Promise<void>}
     */
    const create: (payload: CreateLinkedinProspectPayload) => Promise<void> = async (
      payload: CreateLinkedinProspectPayload,
    ): Promise<void> => {
      const response: { data: LinkedinProspectSummary } = await LinkedinProspectApiService.create(payload)
      upsertLocal(response.data)
    }

    /**
     * Met a jour un prospect.
     * @param {number} id - Identifiant prospect.
     * @param {UpdateLinkedinProspectPayload} payload - Donnees partielles.
     * @param {{ refreshCurrent?: boolean } | undefined} options - Options de synchronisation locale.
     * @param {boolean} [options.refreshCurrent] - Met a jour la fiche courante.
     * @returns {Promise<void>}
     */
    const update: (
      id: number,
      payload: UpdateLinkedinProspectPayload,
      options?: { refreshCurrent?: boolean },
    ) => Promise<void> = async (
      id: number,
      payload: UpdateLinkedinProspectPayload,
      options?: { refreshCurrent?: boolean },
    ): Promise<void> => {
      const response: LinkedinProspectResponse = await LinkedinProspectApiService.update(id, payload)
      upsertLocal(response.data)
      if (options?.refreshCurrent && current.value?.id === id) {
        current.value = response.data
      }
    }

    /**
     * Rafraichit un prospect depuis n8n.
     * @param {number} id - Identifiant prospect.
     * @returns {Promise<void>}
     */
    const refresh: (id: number) => Promise<void> = async (id: number): Promise<void> => {
      const response: { data: LinkedinProspectSummary } = await LinkedinProspectApiService.refresh(id)
      upsertLocal(response.data)
      if (current.value?.id === id) {
        await fetchOne(id)
      }
    }

    /**
     * Supprime un prospect localement et cote API.
     * @param {number} id - Identifiant prospect.
     * @returns {Promise<void>}
     */
    const destroy: (id: number) => Promise<void> = async (id: number): Promise<void> => {
      await LinkedinProspectApiService.destroy(id)
      prospects.value = prospects.value.filter((item: LinkedinProspectSummary): boolean => item.id !== id)
      weekly.value = weekly.value.filter((item: LinkedinProspectSummary): boolean => item.id !== id)
      if (!ProspectsCacheService.isAvailable()) {
        fullCacheFallback.value = fullCacheFallback.value.filter(
          (item: LinkedinProspectSummary): boolean => item.id !== id,
        )
      }
      void ProspectsCacheService.linkedinRemove(id)
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
      const response: { affected: number } = await LinkedinProspectApiService.bulkAction({
        ids: uniqueIds,
        action,
      })
      const idSet: Set<number> = new Set(uniqueIds)

      if (action === ProspectBulkAction.DELETE) {
        prospects.value = prospects.value.filter((item: LinkedinProspectSummary): boolean => !idSet.has(item.id))
        weekly.value = weekly.value.filter((item: LinkedinProspectSummary): boolean => !idSet.has(item.id))
        if (!ProspectsCacheService.isAvailable()) {
          fullCacheFallback.value = fullCacheFallback.value.filter(
            (item: LinkedinProspectSummary): boolean => !idSet.has(item.id),
          )
        }
        for (const id of uniqueIds) {
          void ProspectsCacheService.linkedinRemove(id)
        }
        if (current.value && idSet.has(current.value.id)) {
          current.value = undefined
        }
        return response.affected
      }

      const isFavorite: boolean = action === ProspectBulkAction.FAVORITE
      /**
       * Met a jour le flag favori sur les prospects selectionnes.
       * @param {LinkedinProspectSummary[]} list - Liste a parcourir.
       * @returns {LinkedinProspectSummary[]} Liste mise a jour.
       */
      const patchList: (list: LinkedinProspectSummary[]) => LinkedinProspectSummary[] = (
        list: LinkedinProspectSummary[],
      ): LinkedinProspectSummary[] =>
        list.map(
          (item: LinkedinProspectSummary): LinkedinProspectSummary =>
            idSet.has(item.id) ? { ...item, isFavorite } : item,
        )

      prospects.value = patchList(prospects.value)
      weekly.value = patchList(weekly.value)
      if (!ProspectsCacheService.isAvailable()) {
        fullCacheFallback.value = patchList(fullCacheFallback.value)
      } else {
        const updated: LinkedinProspectSummary[] = prospects.value.filter((item: LinkedinProspectSummary): boolean =>
          idSet.has(item.id),
        )
        if (updated.length > 0) {
          void ProspectsCacheService.linkedinUpsertMany(updated)
        }
      }
      if (current.value && idSet.has(current.value.id)) {
        current.value = { ...current.value, isFavorite }
      }
      return response.affected
    }

    /**
     * Marque une action rapide.
     * @param {number} id - Identifiant prospect.
     * @param {MarkLinkedinActionPayload} payload - Action rapide.
     * @returns {Promise<void>}
     */
    const markAction: (id: number, payload: MarkLinkedinActionPayload) => Promise<void> = async (
      id: number,
      payload: MarkLinkedinActionPayload,
    ): Promise<void> => {
      const response: { data: LinkedinProspectSummary } = await LinkedinProspectApiService.markAction(id, payload)
      upsertLocal(response.data)
    }

    /**
     * Retourne les appels d'un jour (zone Paris) via cache natif.
     * Fallback JS si cache indisponible.
     * @param {string} dateIso - YYYY-MM-DD.
     * @returns {Promise<LinkedinCallEvent[]>} Evenements ordonnes par heure.
     */
    const aggregateCallsByDay: (dateIso: string) => Promise<LinkedinCallEvent[]> = async (
      dateIso: string,
    ): Promise<LinkedinCallEvent[]> => {
      if (ProspectsCacheService.isAvailable()) {
        const cacheResult: LinkedinCallEvent[] = await ProspectsCacheService.linkedinCallsByDay(dateIso)
        if (cacheResult.length > 0 || fullCacheFallback.value.length === 0) {
          return cacheResult
        }
      }
      const result: LinkedinCallEvent[] = []
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
      return result.sort((a: LinkedinCallEvent, b: LinkedinCallEvent): number => a.dateIso.localeCompare(b.dateIso))
    }

    /**
     * Retourne les prospects avec une echeance dans l'horizon.
     * Fallback JS si cache indisponible.
     * @param {number} horizonDays - Nombre de jours.
     * @returns {Promise<LinkedinProspectSummary[]>} Prospects ordonnes par echeance.
     */
    const aggregateTasksDue: (horizonDays: number) => Promise<LinkedinProspectSummary[]> = async (
      horizonDays: number,
    ): Promise<LinkedinProspectSummary[]> => {
      const nowIso: string = new Date().toISOString()
      if (ProspectsCacheService.isAvailable()) {
        const cacheResult: LinkedinProspectSummary[] = await ProspectsCacheService.linkedinTasksDue(horizonDays, nowIso)
        if (cacheResult.length > 0 || fullCacheFallback.value.length === 0) {
          return cacheResult
        }
      }
      const now: number = Date.now()
      const horizon: number = now + horizonDays * 86_400_000
      return fullCacheFallback.value
        .filter((p: LinkedinProspectSummary): boolean => {
          if (!p.nextActionAt) return false
          return new Date(p.nextActionAt).getTime() <= horizon
        })
        .sort((a: LinkedinProspectSummary, b: LinkedinProspectSummary): number => {
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
      isSyncingCache,
      cacheLoaded,
      fetchList,
      fetchWeekly,
      fetchOne,
      enrich,
      create,
      update,
      refresh,
      destroy,
      bulkAction,
      markAction,
      setFilters,
      ensureCacheLoaded,
      aggregateCallsByDay,
      aggregateTasksDue,
    }
  },
)
