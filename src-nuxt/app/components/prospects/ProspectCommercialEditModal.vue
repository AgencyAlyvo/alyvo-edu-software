<template>
  <UModal v-model:open="isOpen" :ui="modalUi">
    <template #content>
      <div class="bg-[radial-gradient(circle_at_top_right,rgba(154,101,213,0.18),transparent_34%),#071022] p-6">
        <div class="mb-5 flex items-center justify-between">
          <div>
            <p class="text-xs font-semibold tracking-[0.2em] text-[#9a65d5] uppercase">LINKEDIN</p>
            <h3 class="mt-1 text-xl font-semibold text-white">Suivi commercial</h3>
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

        <form class="flex flex-col gap-4" @submit.prevent="handleSubmit">
          <div class="grid gap-3 md:grid-cols-2">
            <UFormField label="Statut" :ui="fieldUi">
              <USelect v-model="form.status" :items="statusItems" variant="none" :ui="selectUi" />
            </UFormField>

            <UFormField label="Montant proposition (EUR)" :ui="fieldUi">
              <UInput
                v-model="form.proposalAmount"
                type="number"
                min="0"
                step="0.01"
                variant="none"
                :ui="inputUi"
                placeholder="0"
              />
            </UFormField>

            <UFormField label="Date appel decouverte" :ui="fieldUi">
              <div class="flex gap-2">
                <UInputDate
                  v-model="form.discoveryCallAt"
                  granularity="minute"
                  :hour-cycle="24"
                  variant="none"
                  class="min-w-0 flex-1"
                  :ui="dateFieldUi"
                />
                <UButton
                  type="button"
                  icon="i-heroicons-x-mark"
                  aria-label="Vider la date appel decouverte"
                  color="neutral"
                  variant="ghost"
                  class="h-11 rounded-md border border-[#2f3d67] px-3 text-[#9ba3bd] hover:bg-[#111c3f] hover:text-white"
                  @click="form.discoveryCallAt = null"
                />
              </div>
            </UFormField>

            <UFormField label="Date appel de vente" :ui="fieldUi">
              <div class="flex gap-2">
                <UInputDate
                  v-model="form.salesCallAt"
                  granularity="minute"
                  :hour-cycle="24"
                  variant="none"
                  class="min-w-0 flex-1"
                  :ui="dateFieldUi"
                />
                <UButton
                  type="button"
                  icon="i-heroicons-x-mark"
                  aria-label="Vider la date appel de vente"
                  color="neutral"
                  variant="ghost"
                  class="h-11 rounded-md border border-[#2f3d67] px-3 text-[#9ba3bd] hover:bg-[#111c3f] hover:text-white"
                  @click="form.salesCallAt = null"
                />
              </div>
            </UFormField>

            <UFormField label="Montant signe (EUR)" :ui="fieldUi">
              <UInput
                v-model="form.signedAmount"
                type="number"
                min="0"
                step="0.01"
                variant="none"
                :ui="inputUi"
                placeholder="0"
              />
            </UFormField>

            <UFormField label="Date proposition envoyee" :ui="fieldUi">
              <div class="flex gap-2">
                <UInputDate
                  v-model="form.proposalSentAt"
                  granularity="minute"
                  :hour-cycle="24"
                  variant="none"
                  class="min-w-0 flex-1"
                  :ui="dateFieldUi"
                />
                <UButton
                  type="button"
                  icon="i-heroicons-x-mark"
                  aria-label="Vider la date proposition envoyee"
                  color="neutral"
                  variant="ghost"
                  class="h-11 rounded-md border border-[#2f3d67] px-3 text-[#9ba3bd] hover:bg-[#111c3f] hover:text-white"
                  @click="form.proposalSentAt = null"
                />
              </div>
            </UFormField>

            <UFormField label="Date signature" :ui="fieldUi">
              <div class="flex gap-2">
                <UInputDate
                  v-model="form.signedAt"
                  granularity="minute"
                  :hour-cycle="24"
                  variant="none"
                  class="min-w-0 flex-1"
                  :ui="dateFieldUi"
                />
                <UButton
                  type="button"
                  icon="i-heroicons-x-mark"
                  aria-label="Vider la date signature"
                  color="neutral"
                  variant="ghost"
                  class="h-11 rounded-md border border-[#2f3d67] px-3 text-[#9ba3bd] hover:bg-[#111c3f] hover:text-white"
                  @click="form.signedAt = null"
                />
              </div>
            </UFormField>

            <UFormField v-if="showLossReason" label="Motif de perte" :ui="fieldUi" class="md:col-span-2">
              <textarea
                v-model="form.lossReason"
                rows="2"
                :class="textareaClass"
                placeholder="Pourquoi le prospect refuse ou n'est pas interesse..."
              />
            </UFormField>

            <UFormField label="Notes" :ui="fieldUi" class="md:col-span-2">
              <textarea
                v-model="form.identifiedNeed"
                rows="3"
                :class="textareaClass"
                placeholder="Notes commerciales..."
              />
            </UFormField>
          </div>

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
              label="Enregistrer"
              :loading="submitting"
              class="rounded-md bg-[linear-gradient(135deg,#102766_0%,#7446a6_100%)] px-5 py-2 font-semibold text-white shadow-[0_14px_30px_rgba(5,9,23,0.35)] transition hover:bg-[linear-gradient(135deg,#17337c_0%,#9a65d5_100%)] disabled:brightness-[0.72]"
            />
          </div>
        </form>
      </div>
    </template>
  </UModal>
</template>

<script lang="ts" setup>
import type { Ref } from 'vue'
import type { CalendarDateTime } from '@internationalized/date'
import {
  buildLinkedinStatusSelectItems,
  linkedinLossReasonStatuses,
  linkedinRelanceOnlyStatuses,
} from '#src-core/constants/linkedinSelectableStatuses'
import { LinkedinProspectStatus } from '#src-core/types/enums/linkedin.enums'
import type { UpdateLinkedinProspectPayload } from '#src-core/types/payload/linkedin.types'
import type { LinkedinProspectFull } from '#src-core/types/response/linkedin.types'
import { useLinkedinProspectsStore } from '#src-nuxt/app/stores/linkedinProspects.store'
import { calendarParisToUtcIso, utcIsoToCalendarParis } from '#src-nuxt/app/utils/parisTime'

/**
 * Props de la modale suivi commercial.
 */
type ProspectCommercialEditModalProps = {
  prospect: LinkedinProspectFull
}

/**
 * Item de select statut.
 */
type StatusItem = {
  label: string
  value: LinkedinProspectStatus
}

/**
 * Formulaire suivi commercial.
 */
type CommercialForm = {
  status: LinkedinProspectStatus
  discoveryCallAt: CalendarDateTime | null
  salesCallAt: CalendarDateTime | null
  proposalSentAt: CalendarDateTime | null
  signedAt: CalendarDateTime | null
  proposalAmount: string
  signedAmount: string
  identifiedNeed: string
  lossReason: string
}

const props: ProspectCommercialEditModalProps = defineProps<ProspectCommercialEditModalProps>()
const isOpen: Ref<boolean> = defineModel<boolean>({ default: false })
const store: ReturnType<typeof useLinkedinProspectsStore> = useLinkedinProspectsStore()
const toast: ReturnType<typeof useToast> = useToast()
const submitting: Ref<boolean> = ref(false)
const errorMessage: Ref<string> = ref('')

const relanceLegacyStatuses: LinkedinProspectStatus[] = linkedinRelanceOnlyStatuses

/** Configuration UI de la modale. */
type ModalUiConfig = { overlay: string; content: string; close: string }
const modalUi: ModalUiConfig = {
  overlay: 'bg-[#020617]/80 backdrop-blur-sm',
  content:
    'max-h-[calc(100vh-2rem)] w-[calc(100vw-2rem)] max-w-2xl overflow-y-auto rounded-lg border border-[#2f3d67] bg-[#071022] text-white shadow-[0_24px_80px_rgba(0,0,0,0.45)] ring-0 divide-y-0',
  close: 'text-[#9ba3bd] hover:text-white hover:bg-[#111c3f]',
} as const

/** Configuration UI des champs. */
type FieldUiConfig = { label: string; container: string }
const fieldUi: FieldUiConfig = {
  label: 'text-[#c7d0ea] font-medium',
  container: 'mt-1.5',
} as const

/** Configuration UI des inputs. */
type InputUiConfig = { base: string }
const inputUi: InputUiConfig = {
  base: 'h-11 rounded-md border border-[#2f3d67] bg-[rgba(5,9,23,0.86)] px-3 text-[#f7f8ff] placeholder:text-[#626d90] shadow-[0_10px_24px_rgba(0,0,0,0.18)] outline-none transition hover:border-[#485780] focus:border-[#9a65d5] focus:shadow-[0_0_0_1px_rgba(154,101,213,0.28),0_10px_24px_rgba(0,0,0,0.18)]',
} as const

/** Configuration UI du select de statut. */
type SelectUiConfig = {
  base: string
  trailingIcon: string
  content: string
  viewport: string
  item: string
  itemWrapper: string
  itemLabel: string
  itemTrailingIcon: string
}
const selectUi: SelectUiConfig = {
  base: 'h-11 w-full cursor-pointer rounded-md border border-[#2f3d67] bg-[rgba(5,9,23,0.86)] px-3 text-[#f7f8ff] shadow-[0_10px_24px_rgba(0,0,0,0.18)] outline-none transition hover:border-[#485780] focus:border-[#9a65d5]',
  trailingIcon: 'text-[#9ba3bd]',
  content:
    'max-h-60 w-(--reka-select-trigger-width) rounded-md border border-[#2f3d67] bg-[#071022] shadow-[0_18px_48px_rgba(0,0,0,0.35)] ring-0 origin-(--reka-select-content-transform-origin)',
  viewport: 'relative divide-y divide-[#152247] scroll-py-1 overflow-y-auto flex-1',
  item: 'group relative flex w-full items-start gap-1.5 rounded-md p-1.5 text-sm !text-[#c7d0ea] outline-none transition-colors hover:bg-[#111c3f] hover:!text-white data-[highlighted]:bg-[#111c3f] data-[highlighted]:!text-white data-[state=checked]:bg-[#16234f] data-[state=checked]:!text-white',
  itemWrapper: 'min-w-0 flex-1 !text-current',
  itemLabel: '!text-current group-data-[highlighted]:!text-white group-data-[state=checked]:!text-white',
  itemTrailingIcon: 'text-[#9a65d5] group-data-[highlighted]:text-[#c7a8f2] group-data-[state=checked]:text-[#c7a8f2]',
} as const

/** Configuration UI des champs date. */
type DateFieldUiConfig = { base: string; segment: string }
const dateFieldUi: DateFieldUiConfig = {
  base: 'h-11 w-full rounded-md border border-[#2f3d67] bg-[rgba(5,9,23,0.86)] px-3 shadow-[0_10px_24px_rgba(0,0,0,0.18)] transition hover:border-[#485780]',
  segment: 'text-[#f7f8ff] data-placeholder:text-[#626d90] focus:bg-[#1a2747] rounded px-0.5',
} as const

const textareaClass: string =
  'min-h-20 w-full resize-y rounded-md border border-[#2f3d67] bg-[rgba(5,9,23,0.86)] px-3 py-2 text-sm text-[#f7f8ff] shadow-[0_10px_24px_rgba(0,0,0,0.18)] outline-none transition hover:border-[#485780] focus:border-[#9a65d5] focus:shadow-[0_0_0_1px_rgba(154,101,213,0.28),0_10px_24px_rgba(0,0,0,0.18)]'

const statusItems: StatusItem[] = buildLinkedinStatusSelectItems()

/**
 * Normalise un statut legacy de relance pour le select.
 * @param {LinkedinProspectStatus} status - Statut courant.
 * @returns {LinkedinProspectStatus} Statut affiche.
 */
const normalizeStatusForSelect: (status: LinkedinProspectStatus) => LinkedinProspectStatus = (
  status: LinkedinProspectStatus,
): LinkedinProspectStatus => {
  if (relanceLegacyStatuses.includes(status)) {
    return LinkedinProspectStatus.MESSAGE_1_ENVOYE
  }

  return status
}

/**
 * Construit le formulaire depuis le prospect courant.
 * @returns {CommercialForm} Valeurs initiales.
 */
const buildForm: () => CommercialForm = (): CommercialForm => ({
  status: normalizeStatusForSelect(props.prospect.status),
  discoveryCallAt: utcIsoToCalendarParis(props.prospect.discoveryCallAt),
  salesCallAt: utcIsoToCalendarParis(props.prospect.salesCallAt),
  proposalSentAt: utcIsoToCalendarParis(props.prospect.proposalSentAt),
  signedAt: utcIsoToCalendarParis(props.prospect.signedAt),
  proposalAmount: props.prospect.proposalAmount != null ? String(props.prospect.proposalAmount) : '',
  signedAmount: props.prospect.signedAmount != null ? String(props.prospect.signedAmount) : '',
  identifiedNeed: props.prospect.identifiedNeed ?? '',
  lossReason: props.prospect.lossReason ?? '',
})

const form: Ref<CommercialForm> = ref(buildForm()) as unknown as Ref<CommercialForm>

const showLossReason: ComputedRef<boolean> = computed((): boolean =>
  linkedinLossReasonStatuses.includes(form.value.status),
)

/**
 * Retourne un montant numerique ou null si vide.
 * @param {string | number | null | undefined} value - Valeur saisie.
 * @returns {number | null} Montant ou null.
 */
const toNullableAmount: (value: string | number | null | undefined) => number | null = (
  value: string | number | null | undefined,
): number | null => {
  if (value === null || value === undefined) {
    return null
  }

  if (typeof value === 'number') {
    return Number.isFinite(value) ? value : null
  }

  const trimmed: string = value.trim()
  if (!trimmed) {
    return null
  }

  const numberValue: number = Number(trimmed)
  return Number.isFinite(numberValue) ? numberValue : null
}

/**
 * Normalise un texte optionnel.
 * @param {string | null | undefined} value - Valeur saisie.
 * @returns {string | null} Texte trimme ou null.
 */
const toNullableText: (value: string | null | undefined) => string | null = (
  value: string | null | undefined,
): string | null => {
  if (value == null) {
    return null
  }

  const trimmed: string = String(value).trim()
  return trimmed || null
}

watch(isOpen, (open: boolean): void => {
  if (open) {
    form.value = buildForm()
    errorMessage.value = ''
  }
})

/**
 * Enregistre le suivi commercial.
 * @returns {Promise<void>}
 */
const handleSubmit: () => Promise<void> = async (): Promise<void> => {
  errorMessage.value = ''
  submitting.value = true

  try {
    const payload: UpdateLinkedinProspectPayload = {
      status: form.value.status,
      discoveryCallAt: calendarParisToUtcIso(form.value.discoveryCallAt),
      salesCallAt: calendarParisToUtcIso(form.value.salesCallAt),
      proposalSentAt: calendarParisToUtcIso(form.value.proposalSentAt),
      signedAt: calendarParisToUtcIso(form.value.signedAt),
      proposalAmount: toNullableAmount(form.value.proposalAmount),
      signedAmount: toNullableAmount(form.value.signedAmount),
      identifiedNeed: toNullableText(form.value.identifiedNeed),
      lossReason: showLossReason.value ? toNullableText(form.value.lossReason) : null,
    }

    await store.update(props.prospect.id, payload, { refreshCurrent: true })
    toast.add({ title: 'Suivi commercial mis a jour', color: 'success', duration: 3000 })
    isOpen.value = false
  } catch (error: unknown) {
    errorMessage.value = (error as { message?: string }).message ?? 'Une erreur est survenue.'
  } finally {
    submitting.value = false
  }
}
</script>
