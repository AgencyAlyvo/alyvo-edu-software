<template>
  <main class="grid max-w-4xl gap-6">
    <header>
      <h1 class="text-2xl font-semibold text-white">Créer des comptes Outlook</h1>
      <div class="mt-1 space-y-2 text-sm text-[#9ba3bd]">
        <p>
          Lance l'automatisation nodriver (Google Chrome ou Chromium requis sur ce PC). Parallélisme configurable dans
          <RouterLink to="/home/settings" class="text-[#9a65d5] underline">Paramètres</RouterLink>
          ; le journal en bas affiche chaque étape en direct.
        </p>
        <ul class="list-inside list-disc space-y-1 pl-1">
          <li>
            <span class="text-[#c5cce0]">Déroulement</span> — pour chaque compte : exclusion des prénoms/noms déjà en
            base, préparation réseau (VPN + flush DNS tous les 2 comptes si Windscribe est configuré), inscription
            automatique sur signup.live.com (email, mot de passe, date de naissance, nom, CAPTCHA), fermeture de Chrome
            avant le compte suivant du même lot.
          </li>
          <li>
            <span class="text-[#c5cce0]">Enregistrement en base</span> — après une inscription Microsoft réussie, l'API
            enregistre le compte géré avec : <span class="text-[#c5cce0]">email Outlook</span>,
            <span class="text-[#c5cce0]">prénom</span>, <span class="text-[#c5cce0]">nom</span>,
            <span class="text-[#c5cce0]">mot de passe Outlook</span>
            et
            <span class="text-[#c5cce0]">date d'anniversaire</span>
            (celle saisie dans le formulaire ci-dessous). Les champs école / Cursor restent vides ; vous pourrez les
            compléter sur la liste des comptes.
          </li>
          <li>
            <span class="text-[#c5cce0]">Prénom et nom</span> — tirés au hasard dans une base locale de
            <span class="text-[#c5cce0]">5&nbsp;000 prénoms</span> et
            <span class="text-[#c5cce0]">5&nbsp;000 noms de famille</span> courants aux États-Unis.
          </li>
          <li>
            <span class="text-[#c5cce0]">Mot de passe</span> — généré automatiquement (règles Outlook : 8 caractères
            minimum, majuscules, minuscules, chiffres et symboles). Un mot de passe
            <span class="text-[#c5cce0]">différent à chaque compte</span> : Microsoft refuse souvent les mots de passe
            trop proches ou réutilisés à la suite sur la même session («&nbsp;Ce mot de passe a été utilisé trop
            souvent&nbsp;») ; l'application en génère donc un nouveau à chaque création.
          </li>
          <li>
            <span class="text-[#c5cce0]">VPN Windscribe</span> — tous les 2 comptes (dès le 1<sup>er</sup>) : à
            configurer dans
            <RouterLink to="/home/settings" class="text-[#9a65d5] underline">Paramètres</RouterLink>
            (chemin vers windscribe-cli.exe et pays de connexion).
          </li>
          <li>
            <span class="text-[#c5cce0]">Inscription manuelle</span> — bouton
            <span class="text-[#c5cce0]">Générer profil manuellement</span> dans le formulaire : prénom, nom, email
            et mot de passe suggérés (mêmes règles que nodriver). Inscrivez-vous vous-même sur Outlook, puis cochez et
            enregistrez en base.
          </li>
        </ul>
      </div>
    </header>

    <UAlert v-if="!isTauri" color="warning" variant="soft" title="Disponible uniquement dans l'application desktop" />

    <form class="grid gap-4 rounded-lg border border-[#2f3d67] bg-[#0b1433]/70 p-4" @submit.prevent="runCreation">
      <AlyvoListFilterField
        label="Nombre de comptes Outlook"
        hint="Chaque compte est traité l'un après l'autre via nodriver."
      >
        <UInput
          :model-value="accountCountInput"
          type="number"
          min="1"
          placeholder="Ex. 3"
          icon="i-heroicons-hashtag"
          variant="none"
          :ui="inputUi"
          :disabled="running"
          class="max-w-[200px]"
          @update:model-value="onAccountCountChange"
        />
      </AlyvoListFilterField>

      <AlyvoListFilterField label="Date d'anniversaire Outlook" :hint="birthdayHint">
        <UInput
          :model-value="birthday"
          type="date"
          variant="none"
          :ui="inputUi"
          :disabled="running"
          class="max-w-[220px]"
          @update:model-value="onBirthdayChange"
        />
      </AlyvoListFilterField>

      <div class="border-t border-[#2f3d67] pt-4">
        <AlyvoListFilterField
          label="Inscription manuelle"
          hint="Génère 10 profils (prénom, nom, email, mot de passe) à utiliser sur signup.live.com sans nodriver."
        >
          <UButton
            type="button"
            icon="i-heroicons-user-plus"
            label="Générer profil manuellement"
            variant="soft"
            :disabled="running || savingDrafts || !birthday.trim()"
            class="h-11 max-w-sm justify-center"
            @click="generateManualDrafts"
          />
        </AlyvoListFilterField>
      </div>

      <div class="grid gap-2 border-t border-[#2f3d67] pt-4 sm:grid-cols-[1fr_auto]">
        <UButton
          type="submit"
          icon="i-heroicons-sparkles"
          :label="running ? `Création en cours (${progressCurrent}/${resolvedAccountCount})…` : 'Lancer la création'"
          :loading="running && !stopping"
          :disabled="!isTauri || running || !isFormValid"
          :class="primaryButtonClass"
          class="h-11 justify-center"
        />
        <UButton
          v-if="running"
          type="button"
          icon="i-heroicons-stop-circle"
          color="error"
          variant="soft"
          :label="stopping ? 'Arrêt en cours…' : 'Arrêter'"
          :loading="stopping"
          :disabled="stopping"
          class="h-11 justify-center"
          @click="stopCreation"
        />
      </div>
    </form>

    <section v-if="showExecutionJournal" class="grid gap-2 rounded-lg border border-[#2f3d67] bg-[#050917] p-3">
      <p class="text-sm font-medium text-white">
        Journal sidecar (Python)
        <span v-if="running" class="font-normal text-[#9ba3bd]"> — en cours…</span>
      </p>
      <div
        ref="journalEl"
        class="max-h-80 overflow-y-auto font-mono text-xs leading-relaxed whitespace-pre-wrap text-[#9ba3bd]"
      >
        <p
          v-for="(entry, index) in logs"
          :key="index"
          class="font-mono text-xs leading-relaxed whitespace-pre-wrap"
          :class="journalEntryClass(entry.level)"
        >
          {{ formatJournalLine(entry) }}
        </p>
        <p v-if="logs.length === 0" class="text-[#6b7280]">En attente des logs…</p>
      </div>
    </section>

    <section
      v-if="draftProfiles.length > 0"
      class="overflow-hidden rounded-lg border border-[#2f3d67] bg-[#0b1433]/70"
    >
      <div class="border-b border-[#2f3d67] px-4 py-3">
        <p class="text-sm font-medium text-white">Profils pour inscription manuelle ({{ draftProfiles.length }})</p>
        <p class="mt-1 text-xs text-[#9ba3bd]">
          Inscrivez-vous sur signup.live.com, ajustez l'email ou le mot de passe si besoin, puis cochez et enregistrez
          en base les comptes créés.
        </p>
      </div>
      <div class="max-h-[28rem] overflow-y-auto">
        <div
          v-for="draft in draftProfiles"
          :key="draft.id"
          class="grid gap-3 border-b border-[#1a2747] px-4 py-3 text-sm last:border-b-0 md:grid-cols-[auto_1fr]"
        >
          <label class="flex items-start gap-2 pt-1">
            <input
              v-model="draft.selected"
              type="checkbox"
              :disabled="draft.saved || savingDrafts"
              :class="checkboxClass"
            />
            <span class="sr-only">Sélectionner {{ draft.firstName }} {{ draft.lastName }}</span>
          </label>
          <div class="grid gap-2">
            <div class="flex flex-wrap items-baseline gap-x-3 gap-y-1">
              <span class="font-medium text-white">{{ draft.firstName }} {{ draft.lastName }}</span>
              <span class="text-xs text-[#9ba3bd]">{{ formatBirthdayLabel(draft.birthday) }}</span>
              <span
                v-if="draft.saved"
                class="rounded bg-emerald-500/15 px-2 py-0.5 text-xs font-medium text-emerald-300"
              >
                Enregistré
              </span>
            </div>
            <UInput
              v-model="draft.email"
              type="email"
              variant="none"
              :ui="inputUi"
              :disabled="draft.saved || savingDrafts"
              placeholder="email@outlook.com"
            />
            <UInput
              v-model="draft.password"
              type="text"
              variant="none"
              :ui="inputUi"
              :disabled="draft.saved || savingDrafts"
              placeholder="Mot de passe Outlook"
            />
          </div>
        </div>
      </div>
      <div class="flex flex-wrap items-center gap-3 border-t border-[#2f3d67] px-4 py-3">
        <UButton
          type="button"
          icon="i-heroicons-cloud-arrow-up"
          :label="savingDrafts ? 'Enregistrement…' : 'Enregistrer la sélection'"
          :loading="savingDrafts"
          :disabled="savingDrafts || selectedDraftCount === 0"
          :class="primaryButtonClass"
          @click="saveSelectedDrafts"
        />
        <span class="text-xs text-[#9ba3bd]">{{ selectedDraftCount }} profil(s) sélectionné(s)</span>
      </div>
    </section>

    <UAlert
      v-if="draftMessage"
      color="success"
      variant="soft"
      title="Profils enregistrés"
      :description="draftMessage"
    />

    <div v-if="createdAccounts.length > 0" class="overflow-hidden rounded-lg border border-[#2f3d67] bg-[#0b1433]/70">
      <div class="border-b border-[#2f3d67] px-4 py-3 text-sm font-medium text-white">
        Comptes créés ({{ createdAccounts.length }})
      </div>
      <div class="max-h-48 overflow-y-auto">
        <div
          v-for="(entry, index) in createdAccounts"
          :key="`${entry.email}-${index}`"
          class="border-b border-[#1a2747] px-4 py-3 text-sm last:border-b-0"
        >
          <p class="font-medium text-white">{{ entry.email }}</p>
          <p class="mt-1 text-xs text-[#9ba3bd]">{{ entry.firstName }} {{ entry.lastName }}</p>
          <p class="mt-1 text-xs break-all text-[#9ba3bd]">Mot de passe : {{ entry.password }}</p>
        </div>
      </div>
    </div>

    <UAlert
      v-if="errorMessage"
      color="error"
      variant="soft"
      title="Échec de la création Outlook"
      :description="errorMessage"
      :ui="{ description: 'whitespace-pre-wrap text-xs leading-relaxed' }"
    />
  </main>
</template>

<script lang="ts" setup>
import type { ComputedRef, Ref } from 'vue'

import { OutlookBatchVpnService } from '#src-core/services/OutlookBatchVpnService'
import {
  OutlookCreatorSidecarService,
  OutlookSidecarError,
  OutlookSidecarStoppedError,
} from '#src-core/services/OutlookCreatorSidecarService'
import type { OutlookDraftProfile } from '#src-core/types/outlook-draft-profile.types'
import type { OutlookSidecarResult } from '#src-core/types/response/outlook-sidecar.types'
import { JOURNAL_LINE_INDENT, type JournalLine, type JournalLineLevel } from '#src-core/types/journal-line.types'
import { formatIsoDate } from '#src-core/utils/date-format'
import { formatErrorMessage } from '#src-core/utils/format-error-message'
import { generateOutlookDraftProfiles } from '#src-core/utils/generate-outlook-draft-profiles'
import { createAsyncMutex } from '#src-core/utils/async-mutex'
import { generateOutlookPassword } from '#src-core/utils/generate-outlook-password'
import {
  collectUsedOutlookNamePairs,
  outlookNamePairKey,
  registerUsedOutlookNamePair,
  type OutlookNamePair,
} from '#src-core/utils/outlook-account-names'
import type { ConcurrentPoolWorkerResult } from '#src-core/utils/run-concurrent-pool'
import { runConcurrentPool } from '#src-core/utils/run-concurrent-pool'
import {
  acquireSidecarWaveSlot,
  releaseSidecarWaveSlot,
  resetSidecarWaveCoordinator,
} from '#src-core/utils/sidecar-wave-coordinator'
import { prepareSidecarWaveNetwork } from '#src-core/utils/sidecar-wave-network'
import { randomUsFullName } from '#src-core/utils/us-outlook-names'

import AlyvoListFilterField from '#src-nuxt/app/components/ui/AlyvoListFilterField.vue'
import { useAlyvoDarkUi } from '#src-nuxt/app/composables/useAlyvoDarkUi'
import { useIsTauri } from '#src-nuxt/app/composables/useIsTauri'
import { useDesktopSettingsStore } from '#src-nuxt/app/stores/desktopSettings.store'
import { useManagedAccountsStore } from '#src-nuxt/app/stores/managedAccounts.store'

definePageMeta({ layout: 'home' })

const { isTauri } = useIsTauri()

onMounted((): void => {
  desktopSettingsStore.load()
})

const MIN_ACCOUNT_COUNT: number = 1
const RECENT_PASSWORD_HISTORY_SIZE: number = 25

const store: ReturnType<typeof useManagedAccountsStore> = useManagedAccountsStore()
const desktopSettingsStore: ReturnType<typeof useDesktopSettingsStore> = useDesktopSettingsStore()
const { inputUi, primaryButtonClass, checkboxClass } = useAlyvoDarkUi()

const MANUAL_DRAFT_COUNT: number = 10

const accountCountInput: Ref<string> = ref('1')
const birthday: Ref<string> = ref('')
const draftProfiles: Ref<OutlookDraftProfile[]> = ref([])
const savingDrafts: Ref<boolean> = ref(false)
const draftMessage: Ref<string | null> = ref(null)
const running: Ref<boolean> = ref(false)
const stopping: Ref<boolean> = ref(false)
const stopRequested: Ref<boolean> = ref(false)
const progressCurrent: Ref<number> = ref(0)
const logs: Ref<JournalLine[]> = ref([])
const createdAccounts: Ref<OutlookSidecarResult[]> = ref([])
const errorMessage: Ref<string | null> = ref(null)
const journalEl: Ref<HTMLElement | null> = ref(null)

/**
 * Affiche le journal Python des le lancement (pas seulement apres erreur).
 */
const showExecutionJournal: ComputedRef<boolean> = computed((): boolean => {
  return running.value || logs.value.length > 0 || errorMessage.value !== null
})

const birthdayHint: string = "Date de naissance utilisée pour remplir le formulaire Microsoft lors de l'inscription."

/**
 * Fait defiler le journal vers le bas apres ajout d'une ligne.
 * @returns {void}
 */
const scrollJournal: () => void = (): void => {
  nextTick(() => {
    const container: HTMLElement | null = journalEl.value

    if (container !== null) {
      container.scrollTop = container.scrollHeight
    }
  })
}

/**
 * Ajoute une ligne au journal si le texte n'est pas vide.
 * @param {string} text - Message a afficher.
 * @param {JournalLineLevel} level - Niveau d'indentation visuelle.
 * @returns {void}
 */
const appendJournal: (text: string, level: JournalLineLevel) => void = (
  text: string,
  level: JournalLineLevel,
): void => {
  const trimmed: string = text.trim()

  if (trimmed.length === 0) {
    return
  }

  logs.value.push({ text: trimmed, level })
  scrollJournal()
}

/**
 * Journal niveau compte (titre de lot).
 * @param {string} text - Message a afficher.
 * @returns {void}
 */
const appendAccountLog: (text: string) => void = (text: string): void => appendJournal(text, 'account')

/**
 * Journal niveau etape (VPN, inscription, etc.).
 * @param {string} text - Message a afficher.
 * @returns {void}
 */
const appendStepLog: (text: string) => void = (text: string): void => appendJournal(text, 'step')

/**
 * Journal niveau sous-etape (detail Windscribe, DNS).
 * @param {string} text - Message a afficher.
 * @returns {void}
 */
const appendSubLog: (text: string) => void = (text: string): void => appendJournal(text, 'sub')

/**
 * Journal niveau sidecar (logs Python avec indentation source).
 * @param {string} text - Ligne stderr du sidecar.
 * @returns {void}
 */
const appendSidecarLog: (text: string) => void = (text: string): void => {
  const leadingSpaces: number = text.match(/^\s*/)?.[0]?.length ?? 0
  const content: string = text.trim()
  let level: JournalLineLevel = 'sidecar'

  if (leadingSpaces >= 4) {
    level = 'sidecarDeep'
  } else if (leadingSpaces >= 2) {
    level = 'sidecarDetail'
  }

  appendJournal(content, level)
}

/**
 * Affiche une ligne du journal avec indentation selon le niveau.
 * @param {JournalLine} entry - Entree du journal.
 * @returns {string} Texte prefixe par l'indentation du niveau.
 */
const formatJournalLine: (entry: JournalLine) => string = (entry: JournalLine): string => {
  return `${JOURNAL_LINE_INDENT[entry.level]}${entry.text}`
}

/**
 * Classes visuelles par niveau de log.
 * @param {JournalLineLevel} level - Niveau de la ligne.
 * @returns {string} Classes Tailwind pour le paragraphe.
 */
const journalEntryClass: (level: JournalLineLevel) => string = (level: JournalLineLevel): string => {
  switch (level) {
    case 'account':
      return 'font-semibold text-white'
    case 'step':
      return 'font-medium text-[#c5cce0]'
    case 'sub':
      return 'text-[#9ba3bd]'
    case 'sidecar':
    case 'sidecarDetail':
    case 'sidecarDeep':
      return 'text-[#8b93a8]'
    default:
      return 'text-[#9ba3bd]'
  }
}

/**
 * Nombre de comptes saisi (minimum 1).
 */
const resolvedAccountCount: ComputedRef<number> = computed((): number => {
  const raw: string = accountCountInput.value.trim()
  const parsed: number = Number.parseInt(raw, 10)

  if (Number.isNaN(parsed) || parsed < MIN_ACCOUNT_COUNT) {
    return 0
  }

  return parsed
})

/**
 * Indique si le formulaire est pret pour lancer la creation.
 */
const isFormValid: ComputedRef<boolean> = computed((): boolean => {
  return resolvedAccountCount.value >= MIN_ACCOUNT_COUNT && birthday.value.trim().length > 0
})

const selectedDraftCount: ComputedRef<number> = computed((): number => {
  return draftProfiles.value.filter((draft: OutlookDraftProfile) => draft.selected && !draft.saved).length
})

/**
 * Affiche la date de naissance au format jj/mm/aaaa.
 */
const formatBirthdayLabel: (value: string) => string = (value: string): string => formatIsoDate(value)

/**
 * Génère 10 profils Outlook pour inscription manuelle.
 */
const generateManualDrafts: () => Promise<void> = async (): Promise<void> => {
  const birthDate: string = birthday.value.trim()

  if (!birthDate) {
    errorMessage.value = 'Indiquez une date de naissance avant de générer les profils.'

    return
  }

  errorMessage.value = null
  draftMessage.value = null

  try {
    await store.fetchAccounts()
    const usedNamePairs: OutlookNamePair[] = collectUsedOutlookNamePairs(store.accounts)
    draftProfiles.value = generateOutlookDraftProfiles(MANUAL_DRAFT_COUNT, birthDate, usedNamePairs)
    appendStepLog(`${MANUAL_DRAFT_COUNT} profil(s) manuel(s) généré(s) pour inscription Outlook.`)
  } catch (error: unknown) {
    errorMessage.value = formatErrorMessage(error)
  }
}

/**
 * Enregistre en base les profils manuels cochés.
 */
const saveSelectedDrafts: () => Promise<void> = async (): Promise<void> => {
  const targets: OutlookDraftProfile[] = draftProfiles.value.filter(
    (draft: OutlookDraftProfile) => draft.selected && !draft.saved,
  )

  if (targets.length === 0) {
    return
  }

  savingDrafts.value = true
  errorMessage.value = null
  draftMessage.value = null

  let savedCount: number = 0
  const failures: string[] = []

  try {
    await store.fetchAccounts()
    const existingEmails: Set<string> = new Set(
      store.accounts
        .map((account) => account.outlookEmail?.trim().toLowerCase())
        .filter((email): email is string => !!email),
    )

    for (const draft of targets) {
      const email: string = draft.email.trim().toLowerCase()
      const password: string = draft.password.trim()

      if (!email) {
        failures.push(`${draft.firstName} ${draft.lastName} : email vide`)
        continue
      }

      if (existingEmails.has(email)) {
        failures.push(`${email} : déjà en base`)
        continue
      }

      try {
        await store.createAccount({
          outlookEmail: email,
          outlookFirstName: draft.firstName,
          outlookLastName: draft.lastName,
          outlookEmailPassword: password.length > 0 ? password : null,
          birthday: draft.birthday,
        })
        draft.saved = true
        draft.selected = false
        existingEmails.add(email)
        savedCount += 1
      } catch (error: unknown) {
        failures.push(`${email} : ${formatErrorMessage(error)}`)
      }
    }

    if (savedCount > 0) {
      draftMessage.value = `${savedCount} compte(s) enregistré(s) en base.`
      appendStepLog(`Enregistrement manuel : ${savedCount} compte(s) sauvegardé(s).`)
    }

    if (failures.length > 0) {
      errorMessage.value = failures.join('\n')
    }
  } finally {
    savingDrafts.value = false
  }
}

/**
 * Met a jour le nombre de comptes (UInput type=number renvoie un number, pas une string).
 * @param {string | number | null | undefined} value - Valeur saisie.
 * @returns {void}
 */
const onAccountCountChange: (value: string | number | null | undefined) => void = (
  value: string | number | null | undefined,
): void => {
  accountCountInput.value = value === null || value === undefined ? '' : String(value)
}

/**
 * Met a jour la date de naissance (UInput type=date ne propage pas toujours v-model).
 * @param {string | number | null | undefined} value - Date saisie.
 * @returns {void}
 */
const onBirthdayChange: (value: string | number | null | undefined) => void = (
  value: string | number | null | undefined,
): void => {
  birthday.value = value === null || value === undefined ? '' : String(value)
}

/**
 * Indique si l'utilisateur a demande l'arret pendant une etape asynchrone.
 * @returns {boolean} True si la boucle doit s'interrompre.
 */
const isStopRequested: () => boolean = (): boolean => stopRequested.value

/**
 * Demande l'arret du sidecar en cours et bloque le lancement des comptes suivants.
 * @returns {Promise<void>}
 */
const stopCreation: () => Promise<void> = async (): Promise<void> => {
  if (!running.value || stopping.value) {
    return
  }

  stopRequested.value = true
  stopping.value = true
  appendStepLog('Arret demande — fermeture du sidecar Outlook en cours...')

  const killed: boolean = await OutlookCreatorSidecarService.stopCurrentCreation()

  if (!killed) {
    appendSubLog("Aucun sidecar actif pour l'instant ; la creation s'arretera apres l'etape en cours.")
  }
}

/**
 * Lance la creation de N comptes Outlook via le sidecar.
 */
const runCreation: () => Promise<void> = async (): Promise<void> => {
  if (!isFormValid.value) {
    errorMessage.value = 'Indiquez le nombre de comptes et une date de naissance.'

    return
  }

  running.value = true
  stopping.value = false
  stopRequested.value = false
  errorMessage.value = null
  createdAccounts.value = []
  logs.value = []
  progressCurrent.value = 0

  const total: number = resolvedAccountCount.value
  const birthDate: string = birthday.value.trim()
  const recentPasswords: string[] = []

  try {
    OutlookCreatorSidecarService.prepareBatch()
    resetSidecarWaveCoordinator()
    await store.fetchAccounts()
    const usedNamePairs: OutlookNamePair[] = collectUsedOutlookNamePairs(store.accounts)
    const usedNameKeys: Set<string> = new Set(
      usedNamePairs.map((pair: OutlookNamePair) => outlookNamePairKey(pair.firstName, pair.lastName)),
    )

    const maxConcurrent: number = desktopSettingsStore.outlookMaxConcurrentInstances
    const useFixedNames: boolean = maxConcurrent > 1
    const reservationMutex: ReturnType<typeof createAsyncMutex> = createAsyncMutex()
    const accountIndices: number[] = Array.from({ length: total }, (_unused: undefined, index: number) => index)

    appendStepLog(
      `Parallelisme : jusqu'a ${maxConcurrent} instance(s) Chrome (Parametres). ${usedNamePairs.length} combinaison(s) prenom/nom deja utilisee(s).`,
    )

    let abortAfterFailure: boolean = false

    await runConcurrentPool(
      accountIndices,
      maxConcurrent,
      isStopRequested,
      async (index: number): Promise<ConcurrentPoolWorkerResult> => {
        if (abortAfterFailure || isStopRequested()) {
          return 'abort'
        }

        appendAccountLog(`=== Compte ${index + 1} / ${total} ===`)

        await prepareSidecarWaveNetwork({
          index,
          maxConcurrent,
          isVpnConfigured: desktopSettingsStore.isVpnRotationConfigured,
          windscribeCliPath: desktopSettingsStore.windscribeCliPath,
          windscribeLocation: desktopSettingsStore.windscribeLocation,
          onStepLog: appendStepLog,
          onSubLog: appendSubLog,
        })

        if (isStopRequested()) {
          return 'abort'
        }

        acquireSidecarWaveSlot(maxConcurrent)

        try {
          try {
          appendStepLog(`Compte ${index + 1} — Inscription Outlook (nodriver / Chrome)`)

          let password: string = ''
          let firstName: string | undefined
          let lastName: string | undefined

          await reservationMutex(async (): Promise<void> => {
            password = generateOutlookPassword(recentPasswords)
            recentPasswords.push(password)

            if (recentPasswords.length > RECENT_PASSWORD_HISTORY_SIZE) {
              recentPasswords.shift()
            }

            if (useFixedNames) {
              const picked: { firstName: string; lastName: string } = randomUsFullName(usedNamePairs)
              firstName = picked.firstName
              lastName = picked.lastName
              registerUsedOutlookNamePair(usedNamePairs, usedNameKeys, firstName, lastName)
            }
          })

          appendSidecarLog(`[${index + 1}/${total}] Date de naissance : ${birthDate}`)
          appendSidecarLog(`[${index + 1}/${total}] Mot de passe (${password.length} caracteres) : ${password}`)
          if (firstName && lastName) {
            appendSidecarLog(`[${index + 1}/${total}] Prenom / Nom : ${firstName} ${lastName}`)
          }
          appendSidecarLog(`[${index + 1}/${total}] Demarrage du sidecar Outlook :`)

          const result: OutlookSidecarResult = await OutlookCreatorSidecarService.createOutlookAccount(
            {
              password,
              birthday: birthDate,
              usedNamePairs,
              firstName,
              lastName,
              skipDnsFlush: desktopSettingsStore.isVpnRotationConfigured,
              ...(maxConcurrent > 1
                ? { windowSlot: index % maxConcurrent, windowSlots: maxConcurrent }
                : {}),
            },
            (line: string) => appendSidecarLog(`[${index + 1}/${total}] ${line}`),
          )

          if (!useFixedNames) {
            registerUsedOutlookNamePair(usedNamePairs, usedNameKeys, result.firstName, result.lastName)
          }

          createdAccounts.value.push(result)
          await store.createAccount({
            outlookEmail: result.email,
            outlookFirstName: result.firstName,
            outlookLastName: result.lastName,
            outlookEmailPassword: result.password,
            birthday: birthDate,
          })
          appendSidecarLog(`[${index + 1}/${total}] Compte cree — ${result.email}`)
          appendStepLog(`Compte ${index + 1} enregistre : ${result.email}`)

          return 'done'
        } catch (accountError: unknown) {
          if (accountError instanceof OutlookSidecarStoppedError || isStopRequested()) {
            if (accountError instanceof OutlookSidecarStoppedError) {
              for (const line of accountError.logLines) {
                appendSidecarLog(`[${index + 1}/${total}] ${line}`)
              }
            }

            appendStepLog("Creation arretee par l'utilisateur.")
            await OutlookBatchVpnService.closeChromeAfterManualStop(appendSubLog)

            return 'abort'
          }

          const detail: string = formatErrorMessage(accountError)

          if (accountError instanceof OutlookSidecarError) {
            for (const line of accountError.logLines) {
              appendSidecarLog(`[${index + 1}/${total}] ${line}`)
            }
          }

          appendStepLog(`Echec sur le compte ${index + 1} / ${total} : ${detail}`)
          abortAfterFailure = true

          if (createdAccounts.value.length > 0) {
            errorMessage.value = `${createdAccounts.value.length} compte(s) cree(s) avant l'echec (compte ${index + 1}) : ${detail}`
          } else {
            errorMessage.value = detail
          }

          return 'abort'
        }
        } finally {
          releaseSidecarWaveSlot(maxConcurrent)
        }
      },
      (completed: number, poolTotal: number) => {
        progressCurrent.value = completed
        if (completed === poolTotal) {
          progressCurrent.value = poolTotal
        }
      },
    )

    if (createdAccounts.value.length === total) {
      appendAccountLog(`Creation terminee : ${createdAccounts.value.length} / ${total} compte(s) enregistre(s).`)
    } else if (createdAccounts.value.length > 0) {
      appendAccountLog(`Creation partielle : ${createdAccounts.value.length} / ${total} compte(s) enregistre(s).`)
    } else if (isStopRequested()) {
      appendAccountLog('Creation arretee : aucun compte enregistre sur ce lancement.')
    }
  } catch (error: unknown) {
    if (error instanceof OutlookSidecarStoppedError) {
      appendStepLog("Creation arretee par l'utilisateur.")
      await OutlookBatchVpnService.closeChromeAfterManualStop(appendSubLog)
    } else if (error instanceof OutlookSidecarError) {
      errorMessage.value = error.message

      for (const line of error.logLines) {
        const alreadyLogged: boolean = logs.value.some(
          (entry: JournalLine) =>
            entry.text === line.trim() &&
            (entry.level === 'sidecar' || entry.level === 'sidecarDetail' || entry.level === 'sidecarDeep'),
        )

        if (!alreadyLogged) {
          appendSidecarLog(line)
        }
      }
    } else {
      errorMessage.value = formatErrorMessage(error)
    }
  } finally {
    running.value = false
    stopping.value = false
    progressCurrent.value = 0
  }
}
</script>
