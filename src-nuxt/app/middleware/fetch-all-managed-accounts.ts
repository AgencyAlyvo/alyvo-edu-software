import { useManagedAccountsStore } from '#src-nuxt/app/stores/managedAccounts.store'

/**
 * Recharge tous les comptes geres (sans filtre) avant les pages d'automatisation.
 */
export default defineNuxtRouteMiddleware(async (): Promise<void> => {
  const store: ReturnType<typeof useManagedAccountsStore> = useManagedAccountsStore()

  await store.fetchAllAccounts()
})
