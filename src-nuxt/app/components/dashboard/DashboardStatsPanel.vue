<template>
  <section class="grid gap-10">
    <article v-for="section in sections" :key="section.title" class="grid gap-4">
      <div class="flex items-start gap-3">
        <UIcon :name="section.icon" class="mt-1 h-4 w-4 shrink-0 text-[#9a65d5]" />
        <div>
          <h2 class="text-base leading-tight font-semibold text-white">{{ section.title }}</h2>
          <p class="mt-1 text-xs text-[#9ba3bd]">{{ section.description }}</p>
        </div>
      </div>

      <div class="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <div
          v-for="metric in section.metrics"
          :key="metric.label"
          class="min-h-[88px] rounded-md border border-[#2f3d67] bg-[#0b1433]/70 p-4"
        >
          <div class="flex items-start justify-between gap-3">
            <div class="min-w-0">
              <p class="text-xs font-medium text-[#9fb0d0]">{{ metric.label }}</p>
              <p class="mt-4 text-2xl leading-none font-semibold text-white">{{ formatMetric(metric) }}</p>
            </div>
            <UIcon :name="metric.icon" class="h-4 w-4 shrink-0 text-[#9a65d5]" />
          </div>
        </div>
      </div>
    </article>
  </section>
</template>

<script lang="ts" setup>
import type { LinkedinStats } from '#src-core/types/response/stats.types'

/**
 * Props du panneau stats dashboard.
 */
type DashboardStatsPanelProps = {
  stats?: LinkedinStats
  periodLabel?: string
  loading?: boolean
}

/**
 * Metrique affichee dans une carte du dashboard.
 */
type DashboardMetric = {
  label: string
  value: number
  unit?: 'count' | 'percent' | 'currency'
  icon: string
}

/**
 * Section metier du dashboard LinkedIn.
 */
type DashboardStatsSection = {
  title: string
  description: string
  icon: string
  metrics: DashboardMetric[]
}

const props: DashboardStatsPanelProps = defineProps<DashboardStatsPanelProps>()

/**
 * Prefixe des descriptions selon la periode selectionnee.
 */
const periodPrefix: ComputedRef<string> = computed((): string => {
  if (!props.periodLabel || props.periodLabel === 'Depuis le debut') {
    return 'Suivi cumule'
  }

  return `Periode : ${props.periodLabel}`
})

/**
 * Recupere une statistique en protegeant l'affichage avant le chargement API.
 * @param {keyof LinkedinStats} key - Cle de statistique.
 * @returns {number} Valeur numerique.
 */
const valueOf: (key: keyof LinkedinStats) => number = (key: keyof LinkedinStats): number => props.stats?.[key] ?? 0

const sections: ComputedRef<DashboardStatsSection[]> = computed((): DashboardStatsSection[] => [
  {
    title: 'Acquisition',
    description: `${periodPrefix.value} des invitations envoyees, acceptees et de leur taux d acceptation.`,
    icon: 'i-heroicons-user-plus',
    metrics: [
      {
        label: 'Invitations envoyees',
        value: valueOf('invitationsSent'),
        icon: 'i-heroicons-user-plus',
      },
      {
        label: 'Invitations acceptees',
        value: valueOf('invitationsAccepted'),
        icon: 'i-heroicons-check-circle',
      },
      {
        label: "Taux d'acceptation",
        value: valueOf('acceptanceRate'),
        unit: 'percent',
        icon: 'i-heroicons-chart-bar',
      },
    ],
  },
  {
    title: 'Engagement',
    description: `${periodPrefix.value} des messages, reponses negatives, reponses positives et taux associes.`,
    icon: 'i-heroicons-chat-bubble-left-right',
    metrics: [
      {
        label: 'Messages envoyes',
        value: valueOf('messagesSent'),
        icon: 'i-heroicons-paper-airplane',
      },
      {
        label: 'Reponses negatives',
        value: valueOf('negativeReplies'),
        icon: 'i-heroicons-hand-thumb-down',
      },
      {
        label: 'Reponses positives',
        value: valueOf('positiveReplies'),
        icon: 'i-heroicons-hand-thumb-up',
      },
      {
        label: 'Taux de reponse',
        value: valueOf('replyRate'),
        unit: 'percent',
        icon: 'i-heroicons-chart-bar',
      },
      {
        label: 'Taux de reponse positive',
        value: valueOf('positiveReplyRate'),
        unit: 'percent',
        icon: 'i-heroicons-sparkles',
      },
    ],
  },
  {
    title: 'Rendez-vous',
    description: `${periodPrefix.value} des appels decouverte et appels de vente realises.`,
    icon: 'i-heroicons-calendar-days',
    metrics: [
      {
        label: 'Appels decouverte faits',
        value: valueOf('discoveryCallsDone'),
        icon: 'i-heroicons-phone',
      },
      {
        label: 'Appels de vente faits',
        value: valueOf('salesCallsDone'),
        icon: 'i-heroicons-phone-arrow-up-right',
      },
    ],
  },
  {
    title: 'Ventes',
    description: `${periodPrefix.value} des propositions envoyees, acceptees, refusees et du chiffre d'affaires propose ou signe.`,
    icon: 'i-heroicons-banknotes',
    metrics: [
      {
        label: 'Propositions envoyees',
        value: valueOf('proposalsSent'),
        icon: 'i-heroicons-document-text',
      },
      {
        label: 'Propositions acceptees',
        value: valueOf('proposalsAccepted'),
        icon: 'i-heroicons-trophy',
      },
      {
        label: 'Propositions refusees',
        value: valueOf('proposalsRefused'),
        icon: 'i-heroicons-x-circle',
      },
      {
        label: "Taux d'acceptation proposition",
        value: valueOf('closingRate'),
        unit: 'percent',
        icon: 'i-heroicons-chart-bar',
      },
      {
        label: 'CA propose',
        value: valueOf('totalProposalAmount'),
        unit: 'currency',
        icon: 'i-heroicons-currency-euro',
      },
      {
        label: 'CA signe',
        value: valueOf('totalSignedAmount'),
        unit: 'currency',
        icon: 'i-heroicons-banknotes',
      },
    ],
  },
])

/**
 * Formate une metrique pour la carte.
 * @param {DashboardMetric} metric - Metrique a formatter.
 * @returns {string} Valeur lisible.
 */
const formatMetric: (metric: DashboardMetric) => string = (metric: DashboardMetric): string => {
  if (metric.unit === 'percent') {
    return `${metric.value.toFixed(1)} %`
  }

  if (metric.unit === 'currency') {
    return new Intl.NumberFormat('fr-FR', {
      style: 'currency',
      currency: 'EUR',
      maximumFractionDigits: 0,
    }).format(metric.value)
  }

  return new Intl.NumberFormat('fr-FR').format(metric.value)
}
</script>
