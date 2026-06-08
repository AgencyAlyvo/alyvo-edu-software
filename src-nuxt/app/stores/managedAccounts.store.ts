import { defineStore } from 'pinia'
import type { Ref } from 'vue'

import { ManagedAccountsApiService } from '#src-core/services/ManagedAccountsApiService'
import type {
  CreateManagedAccountPayload,
  ManagedAccountFilter,
  UpdateManagedAccountPayload,
  UploadMybcScreenshotsPayload,
} from '#src-core/types/payload/managed-accounts.types'
import type { ManagedAccount } from '#src-core/types/response/managed-accounts.types'

import { useAuthStore } from './auth.store'

/**
 *
 */
type ManagedAccountsStore = {
  accounts: ManagedAccount[]
  filter: ManagedAccountFilter
  loading: boolean
  error: string | null
  fetchAccounts: () => Promise<void>
  fetchAllAccounts: () => Promise<void>
  setFilter: (nextFilter: ManagedAccountFilter) => Promise<void>
  createAccount: (payload: CreateManagedAccountPayload) => Promise<ManagedAccount>
  updateAccount: (id: number, payload: UpdateManagedAccountPayload) => Promise<ManagedAccount>
  uploadMybcScreenshots: (id: number, payload: UploadMybcScreenshotsPayload) => Promise<ManagedAccount>
  deleteMybcScreenshot: (
    id: number,
    kind: 'student-home' | 'prospect-menu' | 'registration-status',
  ) => Promise<ManagedAccount>
  deleteAccount: (id: number) => Promise<void>
}

/**
 *
 */
type ManagedAccountsStoreSetup = {
  accounts: Ref<ManagedAccount[]>
  filter: Ref<ManagedAccountFilter>
  loading: Ref<boolean>
  error: Ref<string | null>
  fetchAccounts: () => Promise<void>
  fetchAllAccounts: () => Promise<void>
  setFilter: (nextFilter: ManagedAccountFilter) => Promise<void>
  createAccount: (payload: CreateManagedAccountPayload) => Promise<ManagedAccount>
  updateAccount: (id: number, payload: UpdateManagedAccountPayload) => Promise<ManagedAccount>
  uploadMybcScreenshots: (id: number, payload: UploadMybcScreenshotsPayload) => Promise<ManagedAccount>
  deleteMybcScreenshot: (
    id: number,
    kind: 'student-home' | 'prospect-menu' | 'registration-status',
  ) => Promise<ManagedAccount>
  deleteAccount: (id: number) => Promise<void>
}

/**
 *
 */
type UseManagedAccountsStore = () => ManagedAccountsStore

export const useManagedAccountsStore: UseManagedAccountsStore = defineStore(
  'managedAccounts',
  (): ManagedAccountsStoreSetup => {
    const accounts: Ref<ManagedAccount[]> = ref([])
    const filter: Ref<ManagedAccountFilter> = ref('all')
    const loading: Ref<boolean> = ref(false)
    const error: Ref<string | null> = ref(null)

    const authStore: ReturnType<typeof useAuthStore> = useAuthStore()

    /**
     *
     */
    const fetchAccounts: () => Promise<void> = async (): Promise<void> => {
      const token: string | undefined = authStore.authToken

      if (!token) {
        throw new Error('Not authenticated')
      }

      loading.value = true
      error.value = null

      try {
        accounts.value = await ManagedAccountsApiService.list(token, filter.value)
      } catch (fetchError: unknown) {
        error.value = fetchError instanceof Error ? fetchError.message : 'Failed to load accounts'
        throw fetchError
      } finally {
        loading.value = false
      }
    }

    /**
     * Recharge tous les comptes (ignore le filtre d'affichage de la liste).
     * Utilise par les pages d'automatisation Broward / Outlook.
     * @returns {Promise<void>}
     */
    const fetchAllAccounts: () => Promise<void> = async (): Promise<void> => {
      const token: string | undefined = authStore.authToken

      if (!token) {
        throw new Error('Not authenticated')
      }

      loading.value = true
      error.value = null

      try {
        accounts.value = await ManagedAccountsApiService.list(token, 'all')
      } catch (fetchError: unknown) {
        error.value = fetchError instanceof Error ? fetchError.message : 'Failed to load accounts'
        throw fetchError
      } finally {
        loading.value = false
      }
    }

    /**
     * Change le filtre de liste et recharge les comptes.
     * @param {ManagedAccountFilter} nextFilter - Nouveau filtre actif.
     * @returns {Promise<void>}
     */
    const setFilter: (nextFilter: ManagedAccountFilter) => Promise<void> = async (
      nextFilter: ManagedAccountFilter,
    ): Promise<void> => {
      filter.value = nextFilter
      await fetchAccounts()
    }

    /**
     * Cree un compte via l'API puis rafraichit la liste.
     * @param {CreateManagedAccountPayload} payload - Donnees du compte a creer.
     * @returns {Promise<ManagedAccount>} Compte cree.
     */
    const createAccount: (payload: CreateManagedAccountPayload) => Promise<ManagedAccount> = async (
      payload: CreateManagedAccountPayload,
    ): Promise<ManagedAccount> => {
      const token: string | undefined = authStore.authToken

      if (!token) {
        throw new Error('Not authenticated')
      }

      const account: ManagedAccount = await ManagedAccountsApiService.create(token, payload)
      await fetchAccounts()
      return account
    }

    /**
     * Met a jour un compte via l'API puis rafraichit la liste.
     * @param {number} id - Identifiant du compte.
     * @param {UpdateManagedAccountPayload} payload - Champs modifies.
     * @returns {Promise<ManagedAccount>} Compte mis a jour.
     */
    const updateAccount: (id: number, payload: UpdateManagedAccountPayload) => Promise<ManagedAccount> = async (
      id: number,
      payload: UpdateManagedAccountPayload,
    ): Promise<ManagedAccount> => {
      const token: string | undefined = authStore.authToken

      if (!token) {
        throw new Error('Not authenticated')
      }

      const account: ManagedAccount = await ManagedAccountsApiService.update(token, id, payload)
      await fetchAccounts()
      return account
    }

    /**
     * Envoie les captures myBC vers S3 puis rafraichit la liste.
     */
    const uploadMybcScreenshots: (
      id: number,
      payload: UploadMybcScreenshotsPayload,
    ) => Promise<ManagedAccount> = async (
      id: number,
      payload: UploadMybcScreenshotsPayload,
    ): Promise<ManagedAccount> => {
      const token: string | undefined = authStore.authToken

      if (!token) {
        throw new Error('Not authenticated')
      }

      const account: ManagedAccount = await ManagedAccountsApiService.uploadMybcScreenshots(token, id, payload)
      await fetchAccounts()
      return account
    }

    /**
     * Supprime une capture myBC (S3 + base) puis rafraichit la liste.
     */
    const deleteMybcScreenshot: (
      id: number,
      kind: 'student-home' | 'prospect-menu' | 'registration-status',
    ) => Promise<ManagedAccount> = async (
      id: number,
      kind: 'student-home' | 'prospect-menu' | 'registration-status',
    ): Promise<ManagedAccount> => {
      const token: string | undefined = authStore.authToken

      if (!token) {
        throw new Error('Not authenticated')
      }

      const account: ManagedAccount = await ManagedAccountsApiService.deleteMybcScreenshot(token, id, kind)
      await fetchAccounts()
      return account
    }

    /**
     * Supprime un compte via l'API puis rafraichit la liste.
     * @param {number} id - Identifiant du compte.
     * @returns {Promise<void>}
     */
    const deleteAccount: (id: number) => Promise<void> = async (id: number): Promise<void> => {
      const token: string | undefined = authStore.authToken

      if (!token) {
        throw new Error('Not authenticated')
      }

      await ManagedAccountsApiService.delete(token, id)
      await fetchAccounts()
    }

    return {
      accounts,
      filter,
      loading,
      error,
      fetchAccounts,
      fetchAllAccounts,
      setFilter,
      createAccount,
      updateAccount,
      uploadMybcScreenshots,
      deleteMybcScreenshot,
      deleteAccount,
    }
  },
)
