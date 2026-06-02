<template>
  <section class="rounded-lg border border-[#2f3d67] bg-[#0b1433]/70 p-5">
    <h2 class="mb-4 text-base font-semibold text-white">Timeline</h2>
    <div v-if="safeActions.length" class="grid gap-3">
      <div
        v-for="action in safeActions"
        :key="action.id"
        class="rounded-md border border-[#2f3d67] bg-[#060b12]/70 p-3"
      >
        <div class="flex items-center justify-between gap-3">
          <p class="text-sm font-medium text-white">{{ getActionTitle(action) }}</p>
          <span class="text-xs text-[#9ba3bd]">{{ formatDate(action.occurredAt) }}</span>
        </div>
        <p v-if="getActionDescription(action)" class="mt-2 text-sm text-[#cbd3eb]">
          {{ getActionDescription(action) }}
        </p>
      </div>
    </div>
    <EmptyState v-else title="Aucune action" description="La timeline se remplira avec les actions manuelles." />
  </section>
</template>

<script lang="ts" setup>
import {
  linkedinProspectActionTypeLabels,
  linkedinSelectableStatusLabels,
} from '#src-core/constants/linkedinSelectableStatuses'
import type { LinkedinProspectStatus } from '#src-core/types/enums/linkedin.enums'
import { ProspectActionType } from '#src-core/types/enums/linkedin.enums'
import type { ProspectAction } from '#src-core/types/response/actions.types'
import type { ComputedRef } from 'vue'
import { formatParisDate } from '#src-nuxt/app/utils/parisTime'

/**
 * Props de la timeline.
 */
type ProspectActionsTimelineProps = {
  actions?: ProspectAction[] | null
}

const props: ProspectActionsTimelineProps = defineProps<ProspectActionsTimelineProps>()

const safeActions: ComputedRef<ProspectAction[]> = computed((): ProspectAction[] =>
  Array.isArray(props.actions) ? props.actions : [],
)

/**
 * Formate une date en fuseau Paris.
 * @param {string} value - Date ISO.
 * @returns {string} Date lisible.
 */
const formatDate: (value?: string | null) => string = (value?: string | null): string =>
  formatParisDate(value, { dateStyle: 'short', timeStyle: 'short' }) ?? '-'

/**
 * Retourne le libelle d'un statut.
 * @param {string} status - Statut du prospect.
 * @returns {string} Libelle lisible du statut.
 */
const getStatusLabel: (status: string) => string = (status: string): string =>
  linkedinSelectableStatusLabels[status as LinkedinProspectStatus] ?? status

/**
 * Retourne le titre d'une action.
 * @param {ProspectAction} action - Action du prospect.
 * @returns {string} Titre affiche pour l'action.
 */
const getActionTitle: (action: ProspectAction) => string = (action: ProspectAction): string =>
  linkedinProspectActionTypeLabels[action.actionType] ?? action.actionType

/**
 * Retourne la description d'une action.
 * @param {ProspectAction} action - Action du prospect.
 * @returns {string} Description affichee pour l'action.
 */
const getActionDescription: (action: ProspectAction) => string = (action: ProspectAction): string => {
  if (action.actionType === ProspectActionType.STATUS_CHANGED && action.content) {
    const [from, to] = action.content.split(' -> ')
    if (from && to) {
      return `Le statut est passe de "${getStatusLabel(from)}" a "${getStatusLabel(to)}".`
    }
  }

  if (action.content) {
    return action.content
  }

  return ''
}
</script>
