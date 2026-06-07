<template>
  <main class="grid max-w-2xl gap-6">
    <header>
      <h1 class="text-2xl font-semibold text-white">Inscription Broward</h1>
      <div class="mt-1 space-y-2 text-sm text-[#9ba3bd]">
        <p>
          Inscrit sur le portail Broward College les comptes Outlook
          <span class="text-[#c5cce0]">déjà en base</span> (prénom, nom, date de naissance, email personnel). Les
          comptes sont traités <span class="text-[#c5cce0]">un par un</span>.
        </p>
        <ul class="list-inside list-disc space-y-1 pl-1">
          <li>
            <span class="text-[#c5cce0]">Éligibilité</span> — Outlook complet et « Demande envoyée à l'école » = Non ({{
              eligibleCount
            }}
            compte(s) disponible(s)).
          </li>
          <li>
            <span class="text-[#c5cce0]">CapSolver</span> — reCAPTCHA v2 résolu automatiquement ;
            <RouterLink to="/home/settings" class="text-[#9a65d5] underline">clé API dans Paramètres</RouterLink>.
          </li>
          <li>
            <span class="text-[#c5cce0]">VPN</span> — tous les 2 comptes (comme Outlook) si Windscribe est configuré.
          </li>
          <li>
            <span class="text-[#c5cce0]">Après succès</span> — le compte est marqué « Demande envoyée à l'école » en
            base.
          </li>
        </ul>
      </div>
    </header>

    <UAlert v-if="!isTauri" color="warning" variant="soft" title="Disponible uniquement dans l'application desktop" />

    <UAlert
      v-else-if="!desktopSettingsStore.isCapSolverConfigured"
      color="warning"
      variant="soft"
      title="Clé API CapSolver requise"
    >
      <template #description>
        <p class="text-sm">
          Renseignez votre clé CapSolver dans
          <RouterLink to="/home/settings" class="text-[#9a65d5] underline">Paramètres</RouterLink>.
        </p>
      </template>
    </UAlert>

    <form class="grid gap-4 rounded-lg border border-[#2f3d67] bg-[#0b1433]/70 p-4" @submit.prevent="runEnrollment">
      <AlyvoListFilterField
        label="Nombre de comptes à inscrire"
        :hint="`Maximum ${eligibleCount} compte(s) éligible(s) actuellement.`"
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

      <div class="grid gap-2 sm:grid-cols-[1fr_auto]">
        <UButton
          type="submit"
          icon="i-heroicons-academic-cap"
          :label="
            running
              ? `Inscription en cours (${progressCurrent}/${resolvedAccountCount})…`
              : 'Lancer l\'inscription Broward'
          "
          :loading="running && !stopping"
          :disabled="!isTauri || running || store.loading || !isFormValid"
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
          @click="stopEnrollment"
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

    <div v-if="enrolledAccounts.length > 0" class="overflow-hidden rounded-lg border border-[#2f3d67] bg-[#0b1433]/70">
      <div class="border-b border-[#2f3d67] px-4 py-3 text-sm font-medium text-white">
        Inscriptions réussies ({{ enrolledAccounts.length }})
      </div>
      <div class="max-h-48 overflow-y-auto">
        <div
          v-for="(entry, index) in enrolledAccounts"
          :key="`${entry.accountId}-${index}`"
          class="border-b border-[#1a2747] px-4 py-3 text-sm last:border-b-0"
        >
          <p class="font-medium text-white">{{ entry.email }}</p>
          <p class="mt-1 text-xs text-[#9ba3bd]">{{ entry.firstName }} {{ entry.lastName }} — #{{ entry.accountId }}</p>
        </div>
      </div>
    </div>

    <UAlert
      v-if="errorMessage"
      color="error"
      variant="soft"
      title="Échec de l'inscription Broward"
      :description="errorMessage"
      :ui="{ description: 'whitespace-pre-wrap text-xs leading-relaxed' }"
    />
  </main>
</template>

<script lang="ts" setup>
import type { ComputedRef, Ref } from 'vue'

import { OUTLOOK_ACCOUNTS_PER_VPN_ROTATION } from '#src-core/constants/desktop-settings.constants'
import {
  BrowardEnrollmentSidecarService,
  BrowardSidecarError,
  BrowardSidecarStoppedError,
} from '#src-core/services/BrowardEnrollmentSidecarService'
import { OutlookBatchVpnService } from '#src-core/services/OutlookBatchVpnService'
import { JOURNAL_LINE_INDENT, type JournalLine, type JournalLineLevel } from '#src-core/types/journal-line.types'
import type { BrowardSidecarResult } from '#src-core/types/response/broward-sidecar.types'
import type { ManagedAccount } from '#src-core/types/response/managed-accounts.types'
import { listBrowardEligibleAccounts, toBrowardBirthdayIso } from '#src-core/utils/broward-eligible-accounts'
import { formatErrorMessage } from '#src-core/utils/format-error-message'

import AlyvoListFilterField from '#src-nuxt/app/components/ui/AlyvoListFilterField.vue'
import { useAlyvoDarkUi } from '#src-nuxt/app/composables/useAlyvoDarkUi'
import { useIsTauri } from '#src-nuxt/app/composables/useIsTauri'
import { useDesktopSettingsStore } from '#src-nuxt/app/stores/desktopSettings.store'
import { useManagedAccountsStore } from '#src-nuxt/app/stores/managedAccounts.store'

definePageMeta({ layout: 'home', middleware: 'fetch-all-managed-accounts' })

/**
 * Compte inscrit avec succes sur Broward.
 */
type BrowardEnrolledEntry = {
  accountId: number
  email: string
  firstName: string
  lastName: string
}

const { isTauri } = useIsTauri()

const MIN_ACCOUNT_COUNT: number = 1

const store: ReturnType<typeof useManagedAccountsStore> = useManagedAccountsStore()
const desktopSettingsStore: ReturnType<typeof useDesktopSettingsStore> = useDesktopSettingsStore()
const { inputUi, primaryButtonClass } = useAlyvoDarkUi()

const accountCountInput: Ref<string> = ref('1')
const running: Ref<boolean> = ref(false)
const stopping: Ref<boolean> = ref(false)
const stopRequested: Ref<boolean> = ref(false)
const progressCurrent: Ref<number> = ref(0)
const logs: Ref<JournalLine[]> = ref([])
const enrolledAccounts: Ref<BrowardEnrolledEntry[]> = ref([])
const errorMessage: Ref<string | null> = ref(null)
const journalEl: Ref<HTMLElement | null> = ref(null)

onMounted((): void => {
  desktopSettingsStore.load()
})

const eligibleAccounts: ComputedRef<ManagedAccount[]> = computed((): ManagedAccount[] => {
  return listBrowardEligibleAccounts(store.accounts)
})

const eligibleCount: ComputedRef<number> = computed((): number => eligibleAccounts.value.length)

const showExecutionJournal: ComputedRef<boolean> = computed((): boolean => {
  return running.value || logs.value.length > 0 || errorMessage.value !== null
})

const resolvedAccountCount: ComputedRef<number> = computed((): number => {
  const raw: string = accountCountInput.value.trim()
  const parsed: number = Number.parseInt(raw, 10)

  if (Number.isNaN(parsed) || parsed < MIN_ACCOUNT_COUNT) {
    return 0
  }

  return Math.min(parsed, eligibleCount.value)
})

const isFormValid: ComputedRef<boolean> = computed((): boolean => {
  return (
    desktopSettingsStore.isCapSolverConfigured &&
    resolvedAccountCount.value >= MIN_ACCOUNT_COUNT &&
    eligibleCount.value > 0
  )
})

/**
 * @param {string | number | null | undefined} value - Valeur saisie.
 * @returns {void}
 */
const onAccountCountChange: (value: string | number | null | undefined) => void = (
  value: string | number | null | undefined,
): void => {
  accountCountInput.value = value === null || value === undefined ? '' : String(value)
}

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
 * Indique si l'utilisateur a demande l'arret pendant une etape asynchrone.
 * @returns {boolean} True si la boucle doit s'interrompre.
 */
const isStopRequested: () => boolean = (): boolean => stopRequested.value

/**
 * @returns {Promise<void>}
 */
const stopEnrollment: () => Promise<void> = async (): Promise<void> => {
  if (!running.value || stopping.value) {
    return
  }

  stopRequested.value = true
  stopping.value = true
  appendStepLog('Arret demande — fermeture du sidecar Broward en cours...')

  const killed: boolean = await BrowardEnrollmentSidecarService.stopCurrentEnrollment()

  if (!killed) {
    appendSubLog("Aucun sidecar actif pour l'instant ; la file s'arretera apres l'etape en cours.")
  }
}

/**
 * @returns {Promise<void>}
 */
const runEnrollment: () => Promise<void> = async (): Promise<void> => {
  if (!isFormValid.value) {
    errorMessage.value = 'Indiquez un nombre valide et configurez CapSolver dans Parametres.'

    return
  }

  running.value = true
  stopping.value = false
  stopRequested.value = false
  errorMessage.value = null
  enrolledAccounts.value = []
  logs.value = []
  progressCurrent.value = 0

  const total: number = resolvedAccountCount.value
  const targets: ManagedAccount[] = eligibleAccounts.value.slice(0, total)
  const capsolverKey: string = desktopSettingsStore.capsolverApiKey.trim()

  try {
    appendStepLog(`${targets.length} compte(s) a inscrire sur Broward (CapSolver + nodriver).`)

    for (let index: number = 0; index < targets.length; index += 1) {
      if (isStopRequested()) {
        appendStepLog('Inscription arretee avant le compte suivant.')
        break
      }

      const account: ManagedAccount = targets[index]!
      progressCurrent.value = index + 1

      const isStartOfVpnBatch: boolean = index % OUTLOOK_ACCOUNTS_PER_VPN_ROTATION === 0
      const batchNumber: number = Math.floor(index / OUTLOOK_ACCOUNTS_PER_VPN_ROTATION) + 1
      const accountInBatch: number = (index % OUTLOOK_ACCOUNTS_PER_VPN_ROTATION) + 1

      appendAccountLog(`=== Compte ${index + 1} / ${total} — #${account.id} ${account.outlookEmail} ===`)

      if (isStartOfVpnBatch) {
        if (desktopSettingsStore.isVpnRotationConfigured) {
          appendStepLog(
            `Reseau : Windscribe (${desktopSettingsStore.windscribeLocation}), flush DNS, puis Chrome (lot ${batchNumber}).`,
          )
          await OutlookBatchVpnService.prepareBeforeChrome({
            windscribeCliPath: desktopSettingsStore.windscribeCliPath,
            location: desktopSettingsStore.windscribeLocation,
            closeChromeFirst: index > 0,
            batchNumber,
            onLog: appendSubLog,
          })
        } else if (index === 0) {
          appendStepLog('Reseau : Windscribe non configure (voir Parametres).')
        }
      } else {
        appendStepLog(
          `Meme lot VPN (${accountInBatch}/${OUTLOOK_ACCOUNTS_PER_VPN_ROTATION}) : fermeture de Chrome avant relance.`,
        )
        await OutlookBatchVpnService.ensureChromeClosedBeforeSidecar(appendSubLog)
      }

      if (isStopRequested()) {
        appendStepLog('Inscription arretee avant le lancement du sidecar.')
        break
      }

      const firstName: string = account.outlookFirstName?.trim() ?? ''
      const lastName: string = account.outlookLastName?.trim() ?? ''
      const email: string = account.outlookEmail?.trim().toLowerCase() ?? ''
      const password: string = account.outlookEmailPassword?.trim() ?? ''
      const birthday: string = toBrowardBirthdayIso(account.birthday)

      appendSidecarLog(`Email : ${email}`)
      appendSidecarLog(`Prenom / Nom : ${firstName} ${lastName}`)
      appendSidecarLog(`Date de naissance : ${birthday}`)
      appendSidecarLog('Demarrage du sidecar Broward :')

      try {
        const result: BrowardSidecarResult = await BrowardEnrollmentSidecarService.enrollAccount(
          {
            accountId: account.id,
            firstName,
            lastName,
            birthday,
            email,
            password,
          },
          capsolverKey,
          appendSidecarLog,
        )

        await store.updateAccount(account.id, { schoolRequestSent: true })

        enrolledAccounts.value.push({
          accountId: result.accountId,
          email: result.email,
          firstName,
          lastName,
        })

        appendStepLog(`Compte #${account.id} inscrit — email ecole active : ${result.email}`)
      } catch (accountError: unknown) {
        if (accountError instanceof BrowardSidecarError) {
          for (const line of accountError.logLines) {
            const alreadyLogged: boolean = logs.value.some(
              (entry: JournalLine) =>
                entry.text === line.trim() &&
                (entry.level === 'sidecar' || entry.level === 'sidecarDetail' || entry.level === 'sidecarDeep'),
            )

            if (!alreadyLogged) {
              appendSidecarLog(line)
            }
          }
        }

        if (accountError instanceof BrowardSidecarStoppedError || isStopRequested()) {
          appendStepLog("Inscription arretee par l'utilisateur.")
          await OutlookBatchVpnService.closeChromeAfterManualStop(appendSubLog)
          break
        }

        const detail: string = formatErrorMessage(accountError)
        appendStepLog(`Echec sur le compte ${index + 1} / ${total} : ${detail}`)

        if (enrolledAccounts.value.length > 0) {
          errorMessage.value = `${enrolledAccounts.value.length} inscription(s) reussie(s) avant l'echec : ${detail}`
        } else {
          errorMessage.value = detail
        }

        break
      }
    }

    if (enrolledAccounts.value.length === total) {
      appendAccountLog(`Inscription terminee : ${enrolledAccounts.value.length} / ${total} compte(s).`)
    } else if (enrolledAccounts.value.length > 0) {
      appendAccountLog(`Inscription partielle : ${enrolledAccounts.value.length} / ${total} compte(s).`)
    } else if (isStopRequested()) {
      appendAccountLog('Inscription arretee : aucun compte enregistre sur ce lancement.')
    }
  } catch (error: unknown) {
    if (error instanceof BrowardSidecarStoppedError) {
      appendStepLog("Inscription arretee par l'utilisateur.")
      await OutlookBatchVpnService.closeChromeAfterManualStop(appendSubLog)
    } else if (error instanceof BrowardSidecarError) {
      errorMessage.value = error.message

      for (const line of error.logLines) {
        appendSidecarLog(line)
      }
    } else {
      errorMessage.value = formatErrorMessage(error)
    }
  } finally {
    running.value = false
    stopping.value = false
    progressCurrent.value = 0
    await store.fetchAllAccounts()
  }
}
</script>
