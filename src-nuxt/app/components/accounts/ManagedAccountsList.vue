<template>
  <div class="overflow-hidden rounded-lg border border-[#2f3d67] bg-[#0b1433]/70">
    <div v-if="loading" class="px-4 py-8 text-center text-sm text-[#9ba3bd]">Chargement…</div>

    <div v-else-if="accounts.length === 0" class="px-4 py-8 text-center text-sm text-[#9ba3bd]">
      Aucun compte pour ce filtre.
    </div>

    <div v-else class="max-h-[70vh] overflow-auto">
      <table class="w-full min-w-[2650px] border-collapse text-sm text-[#dfe6ff]">
        <thead class="sticky top-0 z-[1] bg-[#0f1a38]">
          <tr class="border-b border-[#2f3d67] text-left text-xs font-medium tracking-wide text-[#9ba3bd] uppercase">
            <th class="px-3 py-3 whitespace-nowrap">#</th>
            <th class="px-3 py-3 whitespace-nowrap">Email Outlook</th>
            <th class="px-3 py-3 whitespace-nowrap">Prénom Outlook</th>
            <th class="px-3 py-3 whitespace-nowrap">Nom Outlook</th>
            <th class="px-3 py-3 whitespace-nowrap">MDP Email Outlook</th>
            <th class="px-3 py-3 whitespace-nowrap">Date d'anniversaire Outlook</th>
            <th class="px-3 py-3 whitespace-nowrap">MDP Email Cursor</th>
            <th class="px-3 py-3 whitespace-nowrap">Student ID</th>
            <th class="px-3 py-3 whitespace-nowrap">Email école</th>
            <th class="px-3 py-3 whitespace-nowrap">MDP email école</th>
            <th class="px-3 py-3 whitespace-nowrap">Email école activé</th>
            <th class="px-3 py-3 whitespace-nowrap">Activé le (école)</th>
            <th class="px-3 py-3 whitespace-nowrap">Demande envoyée à l'école</th>
            <th class="px-3 py-3 whitespace-nowrap">Envoyée le (demande école)</th>
            <th class="px-3 py-3 whitespace-nowrap">Compte Cursor activé</th>
            <th class="px-3 py-3 whitespace-nowrap">Activé le (Cursor)</th>
            <th class="px-3 py-3 whitespace-nowrap">Demande envoyée Cursor SheerID</th>
            <th class="px-3 py-3 whitespace-nowrap">Envoyée le (SheerID)</th>
            <th class="px-3 py-3 whitespace-nowrap">Créé le</th>
            <th class="px-3 py-3 whitespace-nowrap">Modifié le</th>
            <th class="px-3 py-3 text-right whitespace-nowrap"></th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="account in accounts"
            :key="account.id"
            class="border-b border-[#1a2747] transition-colors hover:bg-[#111c35]"
          >
            <td class="px-3 py-3 font-medium whitespace-nowrap text-white">#{{ account.id }}</td>

            <td class="min-w-[180px] px-3 py-3">
              <span class="block truncate">{{ account.outlookEmail || '—' }}</span>
            </td>

            <td class="min-w-[120px] px-3 py-3">
              <span class="block truncate">{{ account.outlookFirstName || '—' }}</span>
            </td>

            <td class="min-w-[120px] px-3 py-3">
              <span class="block truncate">{{ account.outlookLastName || '—' }}</span>
            </td>

            <td class="min-w-[140px] px-3 py-3">
              <UInput
                :model-value="outlookPasswordDraft[account.id] ?? ''"
                type="text"
                placeholder="Mot de passe"
                variant="none"
                :ui="inputUi"
                @update:model-value="(value) => setOutlookPasswordDraft(account.id, String(value))"
                @blur="() => emitSaveOutlookPassword(account)"
              />
            </td>

            <td class="min-w-[150px] px-3 py-3">
              <span class="text-sm whitespace-nowrap text-[#dfe6ff]">{{ account.birthday || '—' }}</span>
            </td>

            <td class="min-w-[140px] px-3 py-3">
              <UInput
                :model-value="cursorPasswordDraft[account.id] ?? ''"
                type="text"
                placeholder="Mot de passe"
                variant="none"
                :ui="inputUi"
                @update:model-value="(value) => setCursorPasswordDraft(account.id, String(value))"
                @blur="() => emitSaveCursorPassword(account)"
              />
            </td>

            <td class="min-w-[120px] px-3 py-3">
              <span class="block truncate font-mono text-xs">{{ account.studentId || '—' }}</span>
            </td>

            <td class="min-w-[180px] px-3 py-3">
              <span class="block truncate">{{ account.schoolEmail || '—' }}</span>
            </td>

            <td class="min-w-[140px] px-3 py-3">
              <UInput
                :model-value="schoolPasswordDraft[account.id] ?? ''"
                type="text"
                placeholder="Mot de passe"
                variant="none"
                :ui="inputUi"
                @update:model-value="(value) => setSchoolPasswordDraft(account.id, String(value))"
                @blur="() => emitSaveSchoolPassword(account)"
              />
            </td>

            <td class="px-3 py-3 whitespace-nowrap">
              <label class="inline-flex cursor-pointer items-center gap-2 text-xs text-[#9ba3bd]">
                <input
                  type="checkbox"
                  :checked="account.schoolEmailActivated"
                  :class="checkboxClass"
                  @change="emitToggleSchool(account, ($event.target as HTMLInputElement).checked)"
                />
                <span>{{ account.schoolEmailActivated ? 'Oui' : 'Non' }}</span>
              </label>
            </td>

            <td class="px-3 py-3 text-xs whitespace-nowrap text-[#9ba3bd]">
              {{ formatIsoDateTime(account.schoolEmailActivatedAt) }}
            </td>

            <td class="px-3 py-3 whitespace-nowrap">
              <label class="inline-flex cursor-pointer items-center gap-2 text-xs text-[#9ba3bd]">
                <input
                  type="checkbox"
                  :checked="account.schoolRequestSent"
                  :class="checkboxClass"
                  @change="emitToggleSchoolRequest(account, ($event.target as HTMLInputElement).checked)"
                />
                <span>{{ account.schoolRequestSent ? 'Oui' : 'Non' }}</span>
              </label>
            </td>

            <td class="px-3 py-3 text-xs whitespace-nowrap text-[#9ba3bd]">
              {{ formatIsoDateTime(account.schoolRequestSentAt) }}
            </td>

            <td class="px-3 py-3 whitespace-nowrap">
              <label class="inline-flex cursor-pointer items-center gap-2 text-xs text-[#9ba3bd]">
                <input
                  type="checkbox"
                  :checked="account.cursorAccountActivated"
                  :class="checkboxClass"
                  @change="emitToggleCursor(account, ($event.target as HTMLInputElement).checked)"
                />
                <span>{{ account.cursorAccountActivated ? 'Oui' : 'Non' }}</span>
              </label>
            </td>

            <td class="px-3 py-3 text-xs whitespace-nowrap text-[#9ba3bd]">
              {{ formatIsoDateTime(account.cursorAccountActivatedAt) }}
            </td>

            <td class="px-3 py-3 whitespace-nowrap">
              <label class="inline-flex cursor-pointer items-center gap-2 text-xs text-[#9ba3bd]">
                <input
                  type="checkbox"
                  :checked="account.cursorSheeridRequestSent"
                  :class="checkboxClass"
                  @change="emitToggleCursorSheeridRequest(account, ($event.target as HTMLInputElement).checked)"
                />
                <span>{{ account.cursorSheeridRequestSent ? 'Oui' : 'Non' }}</span>
              </label>
            </td>

            <td class="px-3 py-3 text-xs whitespace-nowrap text-[#9ba3bd]">
              {{ formatIsoDateTime(account.cursorSheeridRequestSentAt) }}
            </td>

            <td class="px-3 py-3 text-xs whitespace-nowrap text-[#9ba3bd]">
              {{ formatIsoDateTime(account.createdAt) }}
            </td>

            <td class="px-3 py-3 text-xs whitespace-nowrap text-[#9ba3bd]">
              {{ formatIsoDateTime(account.updatedAt) }}
            </td>

            <td class="px-3 py-3 text-right whitespace-nowrap">
              <UButton
                icon="i-heroicons-trash"
                variant="ghost"
                :class="iconGhostButtonClass"
                :loading="deletingId === account.id"
                aria-label="Supprimer le compte"
                @click="emitDelete(account.id)"
              />
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script lang="ts" setup>
import type { ManagedAccount } from '#src-core/types/response/managed-accounts.types'
import { formatIsoDateTime } from '#src-core/utils/date-format'

import { useAlyvoDarkUi } from '#src-nuxt/app/composables/useAlyvoDarkUi'

/**
 *
 */
type ManagedAccountsListProps = {
  accounts: ManagedAccount[]
  loading: boolean
  outlookPasswordDraft: Record<number, string>
  cursorPasswordDraft: Record<number, string>
  schoolPasswordDraft: Record<number, string>
  deletingId: number | null
}

/**
 *
 */
type ManagedAccountsListEmits = {
  'update:outlookPasswordDraft': [accountId: number, value: string]
  'update:cursorPasswordDraft': [accountId: number, value: string]
  'update:schoolPasswordDraft': [accountId: number, value: string]
  saveOutlookPassword: [account: ManagedAccount]
  saveCursorPassword: [account: ManagedAccount]
  saveSchoolPassword: [account: ManagedAccount]
  toggleSchool: [account: ManagedAccount, activated: boolean]
  toggleSchoolRequest: [account: ManagedAccount, sent: boolean]
  toggleCursor: [account: ManagedAccount, activated: boolean]
  toggleCursorSheeridRequest: [account: ManagedAccount, sent: boolean]
  delete: [id: number]
}

/**
 *
 */
type ManagedAccountsListEmit = {
  (event: 'update:outlookPasswordDraft', accountId: number, value: string): void
  (event: 'update:cursorPasswordDraft', accountId: number, value: string): void
  (event: 'update:schoolPasswordDraft', accountId: number, value: string): void
  (event: 'saveOutlookPassword', account: ManagedAccount): void
  (event: 'saveCursorPassword', account: ManagedAccount): void
  (event: 'saveSchoolPassword', account: ManagedAccount): void
  (event: 'toggleSchool', account: ManagedAccount, activated: boolean): void
  (event: 'toggleSchoolRequest', account: ManagedAccount, sent: boolean): void
  (event: 'toggleCursor', account: ManagedAccount, activated: boolean): void
  (event: 'toggleCursorSheeridRequest', account: ManagedAccount, sent: boolean): void
  (event: 'delete', id: number): void
}

defineProps<ManagedAccountsListProps>()
const emit: ManagedAccountsListEmit = defineEmits<ManagedAccountsListEmits>()

const { inputUi, checkboxClass, iconGhostButtonClass } = useAlyvoDarkUi()

/**
 * Propage la mise a jour du brouillon mot de passe Outlook.
 * @param {number} accountId - Identifiant du compte.
 * @param {string} value - Valeur saisie.
 * @returns {void}
 */
const setOutlookPasswordDraft: (accountId: number, value: string) => void = (
  accountId: number,
  value: string,
): void => {
  emit('update:outlookPasswordDraft', accountId, value)
}

/**
 * Propage la mise a jour du brouillon mot de passe email ecole.
 * @param {number} accountId - Identifiant du compte.
 * @param {string} value - Valeur saisie.
 * @returns {void}
 */
const setSchoolPasswordDraft: (accountId: number, value: string) => void = (accountId: number, value: string): void => {
  emit('update:schoolPasswordDraft', accountId, value)
}

/**
 * Propage la mise a jour du brouillon mot de passe Cursor.
 * @param {number} accountId - Identifiant du compte.
 * @param {string} value - Valeur saisie.
 * @returns {void}
 */
const setCursorPasswordDraft: (accountId: number, value: string) => void = (accountId: number, value: string): void => {
  emit('update:cursorPasswordDraft', accountId, value)
}

/**
 * Demande l'enregistrement du mot de passe Outlook au parent.
 * @param {ManagedAccount} account - Compte concerne.
 * @returns {void}
 */
const emitSaveOutlookPassword: (account: ManagedAccount) => void = (account: ManagedAccount): void => {
  emit('saveOutlookPassword', account)
}

/**
 * Demande l'enregistrement du mot de passe Cursor au parent.
 * @param {ManagedAccount} account - Compte concerne.
 * @returns {void}
 */
const emitSaveCursorPassword: (account: ManagedAccount) => void = (account: ManagedAccount): void => {
  emit('saveCursorPassword', account)
}

/**
 * Demande l'enregistrement du mot de passe email ecole au parent.
 * @param {ManagedAccount} account - Compte concerne.
 * @returns {void}
 */
const emitSaveSchoolPassword: (account: ManagedAccount) => void = (account: ManagedAccount): void => {
  emit('saveSchoolPassword', account)
}

/**
 * Bascule l'activation ecole via le parent.
 * @param {ManagedAccount} account - Compte concerne.
 * @param {boolean} activated - Nouvel etat souhaite.
 * @returns {void}
 */
const emitToggleSchool: (account: ManagedAccount, activated: boolean) => void = (
  account: ManagedAccount,
  activated: boolean,
): void => {
  emit('toggleSchool', account, activated)
}

/**
 * Bascule la demande ecole via le parent.
 * @param {ManagedAccount} account - Compte concerne.
 * @param {boolean} sent - Nouvel etat souhaite.
 * @returns {void}
 */
const emitToggleSchoolRequest: (account: ManagedAccount, sent: boolean) => void = (
  account: ManagedAccount,
  sent: boolean,
): void => {
  emit('toggleSchoolRequest', account, sent)
}

/**
 * Bascule l'activation Cursor via le parent.
 * @param {ManagedAccount} account - Compte concerne.
 * @param {boolean} activated - Nouvel etat souhaite.
 * @returns {void}
 */
const emitToggleCursor: (account: ManagedAccount, activated: boolean) => void = (
  account: ManagedAccount,
  activated: boolean,
): void => {
  emit('toggleCursor', account, activated)
}

/**
 * Bascule la demande Cursor SheerID via le parent.
 * @param {ManagedAccount} account - Compte concerne.
 * @param {boolean} sent - Nouvel etat souhaite.
 * @returns {void}
 */
const emitToggleCursorSheeridRequest: (account: ManagedAccount, sent: boolean) => void = (
  account: ManagedAccount,
  sent: boolean,
): void => {
  emit('toggleCursorSheeridRequest', account, sent)
}

/**
 * Demande la suppression du compte au parent.
 * @param {number} id - Identifiant du compte.
 * @returns {void}
 */
const emitDelete: (id: number) => void = (id: number): void => {
  emit('delete', id)
}
</script>
