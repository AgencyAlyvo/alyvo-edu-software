<template>
  <UModal v-model:open="isOpen" :ui="modalUiWide">
    <template #content>
      <div class="bg-[radial-gradient(circle_at_top_right,rgba(154,101,213,0.18),transparent_34%),#071022] p-6">
        <div class="mb-5 flex items-center justify-between">
          <div>
            <p class="text-xs font-semibold tracking-[0.2em] text-[#9a65d5] uppercase">COMPTES GÉRÉS</p>
            <h3 class="mt-1 text-xl font-semibold text-white">Ajouter un compte manuellement</h3>
          </div>
          <UButton
            icon="i-heroicons-x-mark"
            size="sm"
            color="neutral"
            variant="ghost"
            class="text-[#9ba3bd] hover:bg-[#111c3f] hover:text-white"
            @click="isOpen = false"
          />
        </div>

        <form class="flex flex-col gap-5" @submit.prevent="handleSubmit">
          <section class="grid gap-3 md:grid-cols-2">
            <p class="text-sm font-medium text-[#9ba3bd] md:col-span-2">Outlook</p>
            <UFormField label="Email Outlook *" :ui="fieldUi" class="md:col-span-2">
              <UInput
                v-model="form.outlookEmail"
                type="email"
                required
                placeholder="prenom.nom@outlook.com"
                variant="none"
                :ui="inputUi"
              />
            </UFormField>
            <UFormField label="Prénom Outlook" :ui="fieldUi">
              <UInput v-model="form.outlookFirstName" variant="none" :ui="inputUi" />
            </UFormField>
            <UFormField label="Nom Outlook" :ui="fieldUi">
              <UInput v-model="form.outlookLastName" variant="none" :ui="inputUi" />
            </UFormField>
            <UFormField label="MDP Email Outlook" :ui="fieldUi">
              <UInput v-model="form.outlookEmailPassword" type="text" variant="none" :ui="inputUi" />
            </UFormField>
            <UFormField label="Date de naissance" :ui="fieldUi">
              <UInput v-model="form.birthday" type="date" variant="none" :ui="inputUi" />
            </UFormField>
          </section>

          <section class="grid gap-3 md:grid-cols-2">
            <p class="text-sm font-medium text-[#9ba3bd] md:col-span-2">École</p>
            <UFormField label="Email école (.edu)" :ui="fieldUi" class="md:col-span-2">
              <UInput
                v-model="form.schoolEmail"
                type="email"
                placeholder="identifiant@mail.broward.edu"
                variant="none"
                :ui="inputUi"
              />
            </UFormField>
            <UFormField label="MDP Email Cursor" :ui="fieldUi">
              <UInput v-model="form.cursorPassword" type="text" variant="none" :ui="inputUi" />
            </UFormField>
            <UFormField label="Student ID" :ui="fieldUi">
              <UInput v-model="form.studentId" placeholder="A26030270" variant="none" :ui="inputUi" />
            </UFormField>
            <UFormField label="Mot de passe email école" :ui="fieldUi">
              <UInput v-model="form.schoolEmailPassword" type="text" variant="none" :ui="inputUi" />
            </UFormField>
          </section>

          <section class="grid gap-4">
            <p class="text-sm font-medium text-[#9ba3bd]">Statuts</p>
            <p class="text-xs text-[#626d90]">
              Cochez un statut puis choisissez une date (optionnel — la date du jour est utilisée si le champ reste
              vide).
            </p>

            <div
              v-for="statusField in statusFields"
              :key="statusField.key"
              class="grid gap-2 rounded-md border border-[#1a2747] bg-[#0b1433]/50 p-3 sm:grid-cols-[minmax(0,1fr)_minmax(0,14rem)] sm:items-center"
            >
              <label class="inline-flex cursor-pointer items-center gap-2 text-sm text-[#c7d0ea]">
                <input v-model="form[statusField.enabledKey]" type="checkbox" :class="checkboxClass" />
                {{ statusField.label }}
              </label>
              <UFormField :label="statusField.dateLabel" :ui="fieldUi">
                <UInput
                  v-model="form[statusField.dateKey]"
                  type="datetime-local"
                  variant="none"
                  :ui="inputUi"
                  :disabled="!form[statusField.enabledKey]"
                />
              </UFormField>
            </div>
          </section>

          <p v-if="errorMessage" class="text-xs text-red-400">{{ errorMessage }}</p>

          <div class="mt-2 flex justify-end gap-3 border-t border-[#2f3d67] pt-5">
            <UButton
              variant="ghost"
              label="Annuler"
              class="rounded-md px-4 py-2 font-semibold text-[#c7d0ea] hover:bg-[#111c3f] hover:text-white"
              @click="isOpen = false"
            />
            <UButton
              type="submit"
              label="Ajouter le compte"
              :loading="submitting"
              :class="primaryButtonClass"
              class="h-11 px-5"
            />
          </div>
        </form>
      </div>
    </template>
  </UModal>
</template>

<script lang="ts" setup>
import type { ComputedRef, Ref } from 'vue'

import type { CreateManagedAccountPayload } from '#src-core/types/payload/managed-accounts.types'

import { useAlyvoDarkUi } from '#src-nuxt/app/composables/useAlyvoDarkUi'
import { useAlyvoEditModalUi } from '#src-nuxt/app/composables/useAlyvoEditModalUi'
import { useManagedAccountsStore } from '#src-nuxt/app/stores/managedAccounts.store'

/**
 *
 */
type StatusEnabledKey =
  | 'schoolEmailActivated'
  | 'schoolRequestSent'
  | 'cursorAccountActivated'
  | 'cursorSheeridRequestSent'

/**
 *
 */
type StatusDateKey =
  | 'schoolEmailActivatedAt'
  | 'schoolRequestSentAt'
  | 'cursorAccountActivatedAt'
  | 'cursorSheeridRequestSentAt'

/**
 *
 */
type StatusFieldConfig = {
  key: StatusDateKey
  enabledKey: StatusEnabledKey
  dateKey: StatusDateKey
  label: string
  dateLabel: string
}

/**
 * Champs du formulaire de creation manuelle.
 */
type ManualAccountForm = {
  outlookEmail: string
  outlookFirstName: string
  outlookLastName: string
  outlookEmailPassword: string
  birthday: string
  schoolEmail: string
  cursorPassword: string
  studentId: string
  schoolEmailPassword: string
  schoolEmailActivated: boolean
  schoolRequestSent: boolean
  cursorAccountActivated: boolean
  cursorSheeridRequestSent: boolean
  schoolEmailActivatedAt: string
  schoolRequestSentAt: string
  cursorAccountActivatedAt: string
  cursorSheeridRequestSentAt: string
}

/**
 *
 */
type ManagedAccountCreateModalEmits = {
  created: []
}

/**
 *
 */
type ManagedAccountCreateModalEmit = {
  (event: 'created'): void
}

const isOpen: Ref<boolean> = defineModel<boolean>({ default: false })
const emit: ManagedAccountCreateModalEmit = defineEmits<ManagedAccountCreateModalEmits>()

const store: ReturnType<typeof useManagedAccountsStore> = useManagedAccountsStore()
const toast: ReturnType<typeof useToast> = useToast()
const { modalUi, fieldUi, inputUi } = useAlyvoEditModalUi()
const { primaryButtonClass, checkboxClass } = useAlyvoDarkUi()

const modalUiWide: ComputedRef<typeof modalUi> = computed(() => ({
  ...modalUi,
  content: modalUi.content.replace('max-w-2xl', 'max-w-3xl'),
}))

const statusFields: StatusFieldConfig[] = [
  {
    key: 'schoolEmailActivatedAt',
    enabledKey: 'schoolEmailActivated',
    dateKey: 'schoolEmailActivatedAt',
    label: 'Email école activé',
    dateLabel: 'Activé le',
  },
  {
    key: 'schoolRequestSentAt',
    enabledKey: 'schoolRequestSent',
    dateKey: 'schoolRequestSentAt',
    label: "Demande envoyée à l'école",
    dateLabel: 'Envoyée le',
  },
  {
    key: 'cursorAccountActivatedAt',
    enabledKey: 'cursorAccountActivated',
    dateKey: 'cursorAccountActivatedAt',
    label: 'Compte Cursor activé',
    dateLabel: 'Activé le',
  },
  {
    key: 'cursorSheeridRequestSentAt',
    enabledKey: 'cursorSheeridRequestSent',
    dateKey: 'cursorSheeridRequestSentAt',
    label: 'Demande Cursor SheerID envoyée',
    dateLabel: 'Envoyée le',
  },
]

const submitting: Ref<boolean> = ref(false)
const errorMessage: Ref<string> = ref('')

/**
 * Valeurs vides du formulaire.
 * @returns {ManualAccountForm} Formulaire initial.
 */
const emptyForm: () => ManualAccountForm = (): ManualAccountForm => ({
  outlookEmail: '',
  outlookFirstName: '',
  outlookLastName: '',
  outlookEmailPassword: '',
  birthday: '',
  schoolEmail: '',
  cursorPassword: '',
  studentId: '',
  schoolEmailPassword: '',
  schoolEmailActivated: false,
  schoolRequestSent: false,
  cursorAccountActivated: false,
  cursorSheeridRequestSent: false,
  schoolEmailActivatedAt: '',
  schoolRequestSentAt: '',
  cursorAccountActivatedAt: '',
  cursorSheeridRequestSentAt: '',
})

const form: Ref<ManualAccountForm> = ref(emptyForm())

watch(isOpen, (open: boolean): void => {
  if (open) {
    form.value = emptyForm()
    errorMessage.value = ''
  }
})

/**
 * Retourne une chaine trimmee ou null si vide.
 * @param {string} value - Valeur saisie.
 * @returns {string | null} Valeur normalisee.
 */
const optionalString: (value: string) => string | null = (value: string): string | null => {
  const trimmed: string = value.trim()
  return trimmed.length > 0 ? trimmed : null
}

/**
 * Convertit une valeur datetime-local en ISO UTC pour l'API.
 * @param {string} value - Valeur `YYYY-MM-DDTHH:mm`.
 * @returns {string | null} Date ISO ou null si vide.
 */
const toIsoDateTime: (value: string) => string | null = (value: string): string | null => {
  const trimmed: string = value.trim()
  if (!trimmed) {
    return null
  }

  const parsed: Date = new Date(trimmed)
  if (Number.isNaN(parsed.getTime())) {
    return null
  }

  return parsed.toISOString()
}

/**
 * Retourne la date de statut si le flag est actif et la date saisie.
 * @param {boolean} enabled - Statut coche.
 * @param {string} localValue - Valeur datetime-local.
 * @returns {string | undefined} ISO ou undefined (date auto cote API).
 */
const optionalStatusDate: (enabled: boolean, localValue: string) => string | undefined = (
  enabled: boolean,
  localValue: string,
): string | undefined => {
  if (!enabled) {
    return undefined
  }

  const iso: string | null = toIsoDateTime(localValue)
  return iso ?? undefined
}

/**
 * Construit le payload API a partir du formulaire.
 * @returns {CreateManagedAccountPayload} Donnees de creation.
 */
const buildPayload: () => CreateManagedAccountPayload = (): CreateManagedAccountPayload => {
  const payload: CreateManagedAccountPayload = {
    outlookEmail: optionalString(form.value.outlookEmail),
    outlookFirstName: optionalString(form.value.outlookFirstName),
    outlookLastName: optionalString(form.value.outlookLastName),
    outlookEmailPassword: optionalString(form.value.outlookEmailPassword),
    birthday: optionalString(form.value.birthday),
    schoolEmail: optionalString(form.value.schoolEmail),
    cursorPassword: optionalString(form.value.cursorPassword),
    studentId: optionalString(form.value.studentId),
    schoolEmailPassword: optionalString(form.value.schoolEmailPassword),
    schoolEmailActivated: form.value.schoolEmailActivated,
    schoolRequestSent: form.value.schoolRequestSent,
    cursorAccountActivated: form.value.cursorAccountActivated,
    cursorSheeridRequestSent: form.value.cursorSheeridRequestSent,
  }

  const schoolEmailActivatedAt: string | undefined = optionalStatusDate(
    form.value.schoolEmailActivated,
    form.value.schoolEmailActivatedAt,
  )
  const schoolRequestSentAt: string | undefined = optionalStatusDate(
    form.value.schoolRequestSent,
    form.value.schoolRequestSentAt,
  )
  const cursorAccountActivatedAt: string | undefined = optionalStatusDate(
    form.value.cursorAccountActivated,
    form.value.cursorAccountActivatedAt,
  )
  const cursorSheeridRequestSentAt: string | undefined = optionalStatusDate(
    form.value.cursorSheeridRequestSent,
    form.value.cursorSheeridRequestSentAt,
  )

  if (schoolEmailActivatedAt) {
    payload.schoolEmailActivatedAt = schoolEmailActivatedAt
  }
  if (schoolRequestSentAt) {
    payload.schoolRequestSentAt = schoolRequestSentAt
  }
  if (cursorAccountActivatedAt) {
    payload.cursorAccountActivatedAt = cursorAccountActivatedAt
  }
  if (cursorSheeridRequestSentAt) {
    payload.cursorSheeridRequestSentAt = cursorSheeridRequestSentAt
  }

  return payload
}

/**
 * Soumet le formulaire de creation manuelle.
 * @returns {Promise<void>}
 */
const handleSubmit: () => Promise<void> = async (): Promise<void> => {
  errorMessage.value = ''

  const outlookEmail: string = form.value.outlookEmail.trim()
  if (!outlookEmail) {
    errorMessage.value = "L'email Outlook est obligatoire."
    return
  }

  const schoolEmail: string = form.value.schoolEmail.trim()
  if (schoolEmail && !/\.edu$/i.test(schoolEmail)) {
    errorMessage.value = "L'email école doit se terminer par .edu."
    return
  }

  for (const statusField of statusFields) {
    if (!form.value[statusField.enabledKey]) {
      continue
    }

    const localDate: string = form.value[statusField.dateKey].trim()
    if (localDate && !toIsoDateTime(localDate)) {
      errorMessage.value = `Date invalide pour « ${statusField.label} ».`
      return
    }
  }

  submitting.value = true

  try {
    await store.createAccount(buildPayload())
    toast.add({ title: 'Compte ajouté', color: 'success', duration: 3000 })
    isOpen.value = false
    emit('created')
  } catch (error: unknown) {
    errorMessage.value = error instanceof Error ? error.message : 'Impossible de créer le compte.'
  } finally {
    submitting.value = false
  }
}
</script>
