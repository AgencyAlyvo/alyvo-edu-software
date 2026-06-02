<template>
  <section class="grid gap-4 rounded-lg border border-[#2f3d67] bg-[#0b1433]/70 p-5 md:grid-cols-3">
    <div class="flex items-start justify-between md:col-span-3">
      <p class="text-xs font-semibold tracking-[0.16em] text-[#9a65d5] uppercase">Suivi commercial</p>
      <UTooltip text="Modifier">
        <UButton
          icon="i-heroicons-pencil-square"
          size="sm"
          color="neutral"
          variant="ghost"
          class="text-[#9ba3bd] hover:bg-[#111c3f] hover:text-white"
          @click="editOpen = true"
        />
      </UTooltip>
    </div>

    <div>
      <p class="text-xs text-[#9ba3bd] uppercase">Statut</p>
      <div class="mt-1">
        <StatusBadge :status="prospect.status" />
      </div>
    </div>

    <div v-for="item in trackingItems" :key="item.label" :class="item.wide ? 'md:col-span-3' : undefined">
      <p class="text-xs text-[#9ba3bd] uppercase">{{ item.label }}</p>
      <p :class="['mt-1 text-sm break-words text-white', item.multiline ? 'whitespace-pre-line' : '']">
        {{ item.value || '-' }}
      </p>
    </div>

    <LocalBusinessCommercialEditModal v-model="editOpen" :prospect="prospect" />
  </section>
</template>

<script lang="ts" setup>
import type { Ref } from 'vue'
import { LocalBusinessContactChannel } from '#src-core/types/enums/local-business.enums'
import type { LocalBusinessProspectFull } from '#src-core/types/response/local-business.types'
import { formatParisDate } from '#src-nuxt/app/utils/parisTime'

/**
 * Props du bloc suivi commercial business local.
 */
type LocalBusinessCommercialTrackingProps = {
  prospect: LocalBusinessProspectFull
}

/**
 * Item affiche dans la fiche.
 */
type TrackingItem = {
  label: string
  value: string | null
  multiline?: boolean
  wide?: boolean
}

const props: LocalBusinessCommercialTrackingProps = defineProps<LocalBusinessCommercialTrackingProps>()
const editOpen: Ref<boolean> = ref(false)

/**
 * Libelle lisible du canal de prospection.
 * @param {string | null} channel - Valeur technique.
 * @returns {string | null} Libelle ou valeur brute.
 */
const formatContactChannel: (channel: string | null) => string | null = (channel: string | null): string | null => {
  if (!channel) {
    return null
  }

  const labels: Record<LocalBusinessContactChannel, string> = {
    [LocalBusinessContactChannel.EMAIL]: 'Email',
    [LocalBusinessContactChannel.PHONE]: 'Telephone',
    [LocalBusinessContactChannel.WEBSITE_FORM]: 'Formulaire site web',
    [LocalBusinessContactChannel.FACEBOOK]: 'Facebook',
  }

  if (channel in labels) {
    return labels[channel as LocalBusinessContactChannel]
  }

  return channel
}

/**
 * Formate une date ISO en format long francais avec l'heure en fuseau Paris.
 * @param {string | null} iso - ISO date string.
 * @returns {string | null} Date formatee ou null si absente.
 */
const formatDate: (iso: string | null) => string | null = (iso: string | null): string | null =>
  formatParisDate(iso, {
    day: '2-digit',
    month: 'long',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })

const trackingItems: ComputedRef<TrackingItem[]> = computed((): TrackingItem[] => {
  const channel: string | null = formatContactChannel(props.prospect.contactChannel)

  const items: TrackingItem[] = [
    { label: 'Canal de prospection', value: channel },
    { label: 'Date appel decouverte', value: formatDate(props.prospect.discoveryCallAt) },
    { label: 'Date appel de vente', value: formatDate(props.prospect.salesCallAt) },
    { label: 'Date proposition envoyee', value: formatDate(props.prospect.proposalSentAt) },
    { label: 'Date signature', value: formatDate(props.prospect.signedAt) },
    {
      label: 'Montant proposition',
      value: props.prospect.proposalAmount != null ? `${props.prospect.proposalAmount} EUR` : null,
    },
    {
      label: 'Montant signe',
      value: props.prospect.signedAmount != null ? `${props.prospect.signedAmount} EUR` : null,
    },
  ]

  if (props.prospect.lossReason) {
    items.push({
      label: 'Motif de perte',
      value: props.prospect.lossReason,
      multiline: true,
      wide: true,
    })
  }

  items.push({
    label: 'Notes',
    value: props.prospect.notes,
    multiline: true,
    wide: true,
  })

  return items
})
</script>
