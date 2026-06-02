<template>
  <section class="rounded-lg border border-[#2f3d67] bg-[#0b1433]/70 p-5">
    <div class="flex items-center justify-between">
      <div>
        <p class="text-xs font-semibold tracking-[0.2em] text-[#9a65d5] uppercase">SCORES SITE WEB</p>
        <h3 class="mt-1 text-lg font-semibold text-white">Audit Lighthouse</h3>
      </div>
      <UButton
        v-if="prospect.website"
        icon="i-heroicons-sparkles"
        size="sm"
        label="Re-scanner"
        :loading="loading"
        :class="primaryButtonClass"
        @click="$emit('refresh')"
      />
    </div>

    <p v-if="!prospect.website" class="mt-3 text-sm text-[#9ba3bd]">
      Aucun site web renseigne. Ajoute un site web a la fiche puis declenche un enrichissement.
    </p>

    <p v-else-if="!prospect.lighthouseFetchedAt" class="mt-3 text-sm text-[#9ba3bd]">
      Aucun audit Lighthouse encore realise. Clique sur "Re-scanner" pour lancer l'analyse.
    </p>

    <div v-else class="mt-4 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
      <div v-for="row in scoreRows" :key="row.label" class="rounded-md border border-[#1a2747] bg-[#071022] p-3">
        <p class="text-xs text-[#9ba3bd]">{{ row.label }}</p>
        <p class="mt-1 text-2xl font-bold text-white">{{ row.score !== null ? row.score : '-' }}</p>
        <div class="mt-2 h-1.5 w-full overflow-hidden rounded-full bg-[#1a2747]">
          <div
            class="h-full"
            :class="scoreBarColor(row.score)"
            :style="{ width: row.score !== null ? `${row.score}%` : '0%' }"
          />
        </div>
      </div>
    </div>

    <p v-if="prospect.lighthouseFetchedAt" class="mt-4 text-xs text-[#69759b]">
      Dernier audit : {{ formatDate(prospect.lighthouseFetchedAt) }}
    </p>
  </section>
</template>

<script lang="ts" setup>
import type { ComputedRef } from 'vue'
import type { LocalBusinessProspectFull } from '#src-core/types/response/local-business.types'
import { useAlyvoDarkUi } from '#src-nuxt/app/composables/useAlyvoDarkUi'

/**
 * Props du bloc SEO business local.
 */
type LocalBusinessSeoCardProps = {
  prospect: LocalBusinessProspectFull
  loading?: boolean
}

/**
 * Evenements du bloc SEO.
 */
type LocalBusinessSeoCardEmits = {
  refresh: []
}

const props: LocalBusinessSeoCardProps = defineProps<LocalBusinessSeoCardProps>()

defineEmits<LocalBusinessSeoCardEmits>()

const { primaryButtonClass } = useAlyvoDarkUi()

/**
 * Ligne de score Lighthouse.
 */
type ScoreRow = { label: string; score: number | null }

const scoreRows: ComputedRef<ScoreRow[]> = computed((): ScoreRow[] => [
  { label: 'SEO', score: props.prospect.seoScore },
  { label: 'Performance', score: props.prospect.performanceScore },
  { label: 'Accessibilite', score: props.prospect.accessibilityScore },
  { label: 'Bonnes pratiques', score: props.prospect.bestPracticesScore },
])

/**
 * Couleur de la barre de progression selon le score.
 * @param {number | null} score - Score 0-100.
 * @returns {string} Classes Tailwind.
 */
const scoreBarColor: (score: number | null) => string = (score: number | null): string => {
  if (score === null) return 'bg-slate-700'
  if (score >= 80) return 'bg-emerald-500'
  if (score >= 50) return 'bg-amber-500'
  return 'bg-red-500'
}

/**
 * Formate une date ISO en chaine francaise lisible.
 * @param {string} iso - Date ISO.
 * @returns {string} Date formatee.
 */
const formatDate: (iso: string) => string = (iso: string): string =>
  new Intl.DateTimeFormat('fr-FR', {
    dateStyle: 'medium',
    timeStyle: 'short',
  }).format(new Date(iso))
</script>
