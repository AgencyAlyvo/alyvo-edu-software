<template>
  <main class="grid gap-6">
    <header class="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
      <div>
        <h1 class="text-2xl font-semibold text-white">Comptes gérés</h1>
        <p class="mt-1 text-sm text-[#9ba3bd]">{{ store.accounts.length }} compte(s) affiché(s).</p>
      </div>
      <div class="flex flex-wrap gap-3">
        <UButton
          label="Ajouter un compte manuellement"
          icon="i-heroicons-pencil-square"
          :class="secondaryButtonClass"
          class="h-11"
          @click="manualCreateOpen = true"
        />
        <UButton
          label="Créer des comptes Outlook"
          icon="i-heroicons-plus"
          :class="primaryButtonClass"
          class="h-11"
          to="/home/accounts/create-outlook"
        />
      </div>
    </header>

    <ManagedAccountCreateModal v-model="manualCreateOpen" @created="onManualAccountCreated" />

    <ManagedAccountsFilters @submit="onFilterSubmit" />

    <UAlert v-if="store.error" color="error" variant="soft" :title="store.error" />

    <ManagedAccountsList
      :accounts="store.accounts"
      :loading="store.loading"
      :outlook-password-draft="editOutlookPassword"
      :cursor-password-draft="editCursorPassword"
      :school-password-draft="editSchoolPassword"
      :deleting-id="deletingId"
      @update:outlook-password-draft="onOutlookPasswordDraftUpdate"
      @update:cursor-password-draft="onCursorPasswordDraftUpdate"
      @update:school-password-draft="onSchoolPasswordDraftUpdate"
      @save-outlook-password="saveOutlookPassword"
      @save-cursor-password="saveCursorPassword"
      @save-school-password="saveSchoolPassword"
      @toggle-school="toggleSchool"
      @toggle-school-request="toggleSchoolRequest"
      @toggle-cursor="toggleCursor"
      @toggle-cursor-sheerid-request="toggleCursorSheeridRequest"
      @delete="removeAccount"
    />
  </main>
</template>

<script lang="ts" setup>
import type { Ref } from 'vue'

import type { ManagedAccountFilter } from '#src-core/types/payload/managed-accounts.types'
import type { ManagedAccount } from '#src-core/types/response/managed-accounts.types'

import ManagedAccountCreateModal from '#src-nuxt/app/components/accounts/ManagedAccountCreateModal.vue'
import ManagedAccountsFilters from '#src-nuxt/app/components/accounts/ManagedAccountsFilters.vue'
import ManagedAccountsList from '#src-nuxt/app/components/accounts/ManagedAccountsList.vue'
import { useAlyvoDarkUi } from '#src-nuxt/app/composables/useAlyvoDarkUi'
import { useManagedAccountsStore } from '#src-nuxt/app/stores/managedAccounts.store'

definePageMeta({ layout: 'home' })

const store: ReturnType<typeof useManagedAccountsStore> = useManagedAccountsStore()
const { primaryButtonClass, secondaryButtonClass } = useAlyvoDarkUi()

const manualCreateOpen: Ref<boolean> = ref(false)

const editOutlookPassword: Ref<Record<number, string>> = ref({})
const editCursorPassword: Ref<Record<number, string>> = ref({})
const editSchoolPassword: Ref<Record<number, string>> = ref({})
const deletingId: Ref<number | null> = ref(null)

/**
 * Rafraichit les brouillons apres creation manuelle.
 * @returns {void}
 */
const onManualAccountCreated: () => void = (): void => {
  syncEditFields()
}

/**
 * Applique le filtre depuis le formulaire.
 * @param {ManagedAccountFilter} filter - Filtre selectionne.
 * @returns {Promise<void>}
 */
const onFilterSubmit: (filter: ManagedAccountFilter) => Promise<void> = async (
  filter: ManagedAccountFilter,
): Promise<void> => {
  await store.setFilter(filter)
  syncEditFields()
}

/**
 * Synchronise les brouillons de mots de passe avec la liste.
 * @returns {void}
 */
const syncEditFields: () => void = (): void => {
  const nextOutlookPassword: Record<number, string> = {}
  const nextCursorPassword: Record<number, string> = {}
  const nextSchoolPassword: Record<number, string> = {}

  for (const account of store.accounts) {
    nextOutlookPassword[account.id] = account.outlookEmailPassword ?? ''
    nextCursorPassword[account.id] = account.cursorPassword ?? ''
    nextSchoolPassword[account.id] = account.schoolEmailPassword ?? ''
  }

  editOutlookPassword.value = nextOutlookPassword
  editCursorPassword.value = nextCursorPassword
  editSchoolPassword.value = nextSchoolPassword
}

/**
 * Met a jour le brouillon mot de passe Outlook.
 * @param {number} accountId - Identifiant du compte.
 * @param {string} value - Valeur saisie.
 * @returns {void}
 */
const onOutlookPasswordDraftUpdate: (accountId: number, value: string) => void = (
  accountId: number,
  value: string,
): void => {
  editOutlookPassword.value = {
    ...editOutlookPassword.value,
    [accountId]: value,
  }
}

/**
 * Met a jour le brouillon mot de passe email ecole.
 * @param {number} accountId - Identifiant du compte.
 * @param {string} value - Valeur saisie.
 * @returns {void}
 */
const onSchoolPasswordDraftUpdate: (accountId: number, value: string) => void = (
  accountId: number,
  value: string,
): void => {
  editSchoolPassword.value = {
    ...editSchoolPassword.value,
    [accountId]: value,
  }
}

/**
 * Met a jour le brouillon mot de passe Cursor.
 * @param {number} accountId - Identifiant du compte.
 * @param {string} value - Valeur saisie.
 * @returns {void}
 */
const onCursorPasswordDraftUpdate: (accountId: number, value: string) => void = (
  accountId: number,
  value: string,
): void => {
  editCursorPassword.value = {
    ...editCursorPassword.value,
    [accountId]: value,
  }
}

/**
 * Enregistre le mot de passe Outlook saisi.
 * @param {ManagedAccount} account - Compte a mettre a jour.
 * @returns {Promise<void>}
 */
const saveOutlookPassword: (account: ManagedAccount) => Promise<void> = async (
  account: ManagedAccount,
): Promise<void> => {
  const value: string = (editOutlookPassword.value[account.id] || '').trim()
  const current: string = (account.outlookEmailPassword || '').trim()

  if (value === current) {
    return
  }

  await store.updateAccount(account.id, {
    outlookEmailPassword: value.length > 0 ? value : null,
  })
}

/**
 * Enregistre le mot de passe email ecole saisi.
 * @param {ManagedAccount} account - Compte a mettre a jour.
 * @returns {Promise<void>}
 */
const saveSchoolPassword: (account: ManagedAccount) => Promise<void> = async (
  account: ManagedAccount,
): Promise<void> => {
  const value: string = (editSchoolPassword.value[account.id] || '').trim()
  const current: string = (account.schoolEmailPassword || '').trim()

  if (value === current) {
    return
  }

  await store.updateAccount(account.id, {
    schoolEmailPassword: value.length > 0 ? value : null,
  })
}

/**
 * Enregistre le mot de passe Cursor saisi.
 * @param {ManagedAccount} account - Compte a mettre a jour.
 * @returns {Promise<void>}
 */
const saveCursorPassword: (account: ManagedAccount) => Promise<void> = async (
  account: ManagedAccount,
): Promise<void> => {
  const value: string = (editCursorPassword.value[account.id] || '').trim()
  const current: string = (account.cursorPassword || '').trim()

  if (value === current) {
    return
  }

  await store.updateAccount(account.id, {
    cursorPassword: value.length > 0 ? value : null,
  })
}

/**
 * Bascule l'activation école.
 * @param {ManagedAccount} account - Compte concerne.
 * @param {boolean} activated - Nouvel etat souhaite.
 * @returns {Promise<void>}
 */
const toggleSchool: (account: ManagedAccount, activated: boolean) => Promise<void> = async (
  account: ManagedAccount,
  activated: boolean,
): Promise<void> => {
  if (account.schoolEmailActivated === activated) {
    return
  }

  await store.updateAccount(account.id, { schoolEmailActivated: activated })
}

/**
 * Bascule la demande envoyee a l'ecole.
 * @param {ManagedAccount} account - Compte concerne.
 * @param {boolean} sent - Nouvel etat souhaite.
 * @returns {Promise<void>}
 */
const toggleSchoolRequest: (account: ManagedAccount, sent: boolean) => Promise<void> = async (
  account: ManagedAccount,
  sent: boolean,
): Promise<void> => {
  if (account.schoolRequestSent === sent) {
    return
  }

  await store.updateAccount(account.id, { schoolRequestSent: sent })
}

/**
 * Bascule l'activation Cursor.
 * @param {ManagedAccount} account - Compte concerne.
 * @param {boolean} activated - Nouvel etat souhaite.
 * @returns {Promise<void>}
 */
const toggleCursor: (account: ManagedAccount, activated: boolean) => Promise<void> = async (
  account: ManagedAccount,
  activated: boolean,
): Promise<void> => {
  if (account.cursorAccountActivated === activated) {
    return
  }

  await store.updateAccount(account.id, { cursorAccountActivated: activated })
}

/**
 * Bascule la demande envoyee a Cursor SheerID.
 * @param {ManagedAccount} account - Compte concerne.
 * @param {boolean} sent - Nouvel etat souhaite.
 * @returns {Promise<void>}
 */
const toggleCursorSheeridRequest: (account: ManagedAccount, sent: boolean) => Promise<void> = async (
  account: ManagedAccount,
  sent: boolean,
): Promise<void> => {
  if (account.cursorSheeridRequestSent === sent) {
    return
  }

  await store.updateAccount(account.id, { cursorSheeridRequestSent: sent })
}

/**
 * Supprime un compte après confirmation.
 * @param {number} id - Identifiant du compte.
 * @returns {Promise<void>}
 */
const removeAccount: (id: number) => Promise<void> = async (id: number): Promise<void> => {
  if (!confirm('Supprimer ce compte ?')) {
    return
  }

  deletingId.value = id

  try {
    await store.deleteAccount(id)
    syncEditFields()
  } finally {
    deletingId.value = null
  }
}

onMounted(async (): Promise<void> => {
  await refreshAccountsList()
})

onActivated(async (): Promise<void> => {
  await refreshAccountsList()
})

/**
 * Recharge la liste selon le filtre actif (retour depuis une page d'automatisation).
 * @returns {Promise<void>}
 */
const refreshAccountsList: () => Promise<void> = async (): Promise<void> => {
  await store.fetchAccounts()
  syncEditFields()
}
</script>
