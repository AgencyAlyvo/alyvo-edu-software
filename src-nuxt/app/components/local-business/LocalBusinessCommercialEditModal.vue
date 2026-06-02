<template>
  <UModal v-model:open="isOpen" :ui="modalUi">
    <template #content>
      <div class="bg-[radial-gradient(circle_at_top_right,rgba(154,101,213,0.18),transparent_34%),#071022] p-6">
        <div class="mb-5 flex items-center justify-between">
          <div>
            <p class="text-xs font-semibold tracking-[0.2em] text-[#9a65d5] uppercase">BUSINESS LOCAL</p>
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

            <UFormField label="Canal de prospection" :ui="fieldUi">
              <USelect v-model="form.contactChannel" :items="channelItems" variant="none" :ui="selectUi" />
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
              <textarea v-model="form.notes" rows="3" :class="textareaClass" placeholder="Notes commerciales..." />
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
  buildLocalBusinessStatusSelectItems,
  localBusinessLossReasonStatuses,
  type LocalBusinessStatusSelectItem,
} from '#src-core/constants/localBusinessSelectableStatuses'
import { LocalBusinessContactChannel, type LocalBusinessStatus } from '#src-core/types/enums/local-business.enums'
import type { UpdateLocalBusinessProspectPayload } from '#src-core/types/payload/local-business.types'
import type { LocalBusinessProspectFull } from '#src-core/types/response/local-business.types'
import { useAlyvoEditModalUi } from '#src-nuxt/app/composables/useAlyvoEditModalUi'
import { useLocalBusinessProspectsStore } from '#src-nuxt/app/stores/localBusinessProspects.store'
import { calendarParisToUtcIso, utcIsoToCalendarParis } from '#src-nuxt/app/utils/parisTime'

/**
 * Props de la modale suivi commercial business local.
 */
type LocalBusinessCommercialEditModalProps = {
  prospect: LocalBusinessProspectFull
}

const NONE_CHANNEL: string = '__none__'

/**
 * Item de select canal.
 */
type ChannelItem = {
  label: string
  value: string
}

/**
 * Formulaire suivi commercial.
 */
type CommercialForm = {
  status: LocalBusinessStatus
  contactChannel: string
  discoveryCallAt: CalendarDateTime | null
  salesCallAt: CalendarDateTime | null
  proposalSentAt: CalendarDateTime | null
  signedAt: CalendarDateTime | null
  proposalAmount: string
  signedAmount: string
  notes: string
  lossReason: string
}

const props: LocalBusinessCommercialEditModalProps = defineProps<LocalBusinessCommercialEditModalProps>()
const isOpen: Ref<boolean> = defineModel<boolean>({ default: false })
const store: ReturnType<typeof useLocalBusinessProspectsStore> = useLocalBusinessProspectsStore()
const toast: ReturnType<typeof useToast> = useToast()
const { modalUi, fieldUi, inputUi, selectUi, dateFieldUi, textareaClass } = useAlyvoEditModalUi()
const submitting: Ref<boolean> = ref(false)
const errorMessage: Ref<string> = ref('')

const statusItems: LocalBusinessStatusSelectItem[] = buildLocalBusinessStatusSelectItems()
const channelItems: ChannelItem[] = [
  { label: 'Non defini', value: NONE_CHANNEL },
  ...Object.values(LocalBusinessContactChannel).map(
    (channel: LocalBusinessContactChannel): ChannelItem => ({
      label:
        channel === LocalBusinessContactChannel.EMAIL
          ? 'Email'
          : channel === LocalBusinessContactChannel.PHONE
            ? 'Telephone'
            : channel === LocalBusinessContactChannel.WEBSITE_FORM
              ? 'Formulaire site web'
              : 'Facebook',
      value: channel,
    }),
  ),
]

/**
 * Construit le formulaire depuis le prospect courant.
 * @returns {CommercialForm} Valeurs initiales.
 */
const buildForm: () => CommercialForm = (): CommercialForm => ({
  status: props.prospect.status,
  contactChannel: props.prospect.contactChannel ?? NONE_CHANNEL,
  discoveryCallAt: utcIsoToCalendarParis(props.prospect.discoveryCallAt),
  salesCallAt: utcIsoToCalendarParis(props.prospect.salesCallAt),
  proposalSentAt: utcIsoToCalendarParis(props.prospect.proposalSentAt),
  signedAt: utcIsoToCalendarParis(props.prospect.signedAt),
  proposalAmount: props.prospect.proposalAmount != null ? String(props.prospect.proposalAmount) : '',
  signedAmount: props.prospect.signedAmount != null ? String(props.prospect.signedAmount) : '',
  notes: props.prospect.notes ?? '',
  lossReason: props.prospect.lossReason ?? '',
})

const form: Ref<CommercialForm> = ref(buildForm()) as unknown as Ref<CommercialForm>

const showLossReason: ComputedRef<boolean> = computed((): boolean =>
  localBusinessLossReasonStatuses.includes(form.value.status),
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
    const contactChannel: LocalBusinessContactChannel | null =
      !form.value.contactChannel || form.value.contactChannel === NONE_CHANNEL
        ? null
        : (form.value.contactChannel as LocalBusinessContactChannel)

    const payload: UpdateLocalBusinessProspectPayload = {
      status: form.value.status,
      contactChannel,
      discoveryCallAt: calendarParisToUtcIso(form.value.discoveryCallAt),
      salesCallAt: calendarParisToUtcIso(form.value.salesCallAt),
      proposalSentAt: calendarParisToUtcIso(form.value.proposalSentAt),
      signedAt: calendarParisToUtcIso(form.value.signedAt),
      proposalAmount: toNullableAmount(form.value.proposalAmount),
      signedAmount: toNullableAmount(form.value.signedAmount),
      notes: toNullableText(form.value.notes),
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
