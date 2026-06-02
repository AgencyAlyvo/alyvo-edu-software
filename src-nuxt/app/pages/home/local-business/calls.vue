<template>
  <main class="grid gap-6">
    <header class="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
      <div>
        <p class="text-xs font-semibold tracking-[0.2em] text-[#9a65d5] uppercase">BUSINESS LOCAUX</p>
        <h1 class="mt-2 text-2xl font-semibold text-white">Rendez-vous appels Business</h1>
        <p class="mt-1 text-sm text-[#9ba3bd]">{{ selectedDayLabel }} - {{ formattedDate }}</p>
      </div>

      <div class="flex items-center gap-2">
        <UButton
          icon="i-heroicons-chevron-left"
          size="sm"
          color="neutral"
          variant="ghost"
          :class="iconGhostButtonClass"
          aria-label="Jour precedent"
          @click="prevDay"
        />
        <UButton
          :label="todayButtonLabel"
          size="sm"
          color="neutral"
          variant="outline"
          :disabled="isTodaySelected"
          class="border-[#51618d] bg-[#111c3f] text-white shadow-sm shadow-black/20 hover:border-[#7b8ab8] hover:bg-[#16234a] disabled:border-[#2f3d67] disabled:bg-[#0b1433] disabled:text-[#9ba3bd]"
          @click="goToToday"
        />
        <UButton
          icon="i-heroicons-chevron-right"
          size="sm"
          color="neutral"
          variant="ghost"
          :class="iconGhostButtonClass"
          aria-label="Jour suivant"
          @click="nextDay"
        />
      </div>
    </header>

    <div class="grid gap-4 md:grid-cols-3">
      <div class="rounded-lg border border-[#2f3d67] bg-[#0b1433]/70 p-4">
        <p class="text-xs text-[#9ba3bd] uppercase">Total appels</p>
        <p class="mt-2 text-3xl font-bold text-white">{{ allCalls.length }}</p>
      </div>
      <div class="rounded-lg border border-[#2f3d67] bg-[#0b1433]/70 p-4">
        <p class="text-xs text-sky-400 uppercase">Appels decouverte</p>
        <p class="mt-2 text-3xl font-bold text-white">{{ discoveryCallsCount }}</p>
      </div>
      <div class="rounded-lg border border-[#2f3d67] bg-[#0b1433]/70 p-4">
        <p class="text-xs text-[#c7a8f2] uppercase">Appels de vente</p>
        <p class="mt-2 text-3xl font-bold text-white">{{ salesCallsCount }}</p>
      </div>
    </div>

    <section
      v-if="!isBusy && allCalls.length === 0"
      class="rounded-lg border border-[#2f3d67] bg-[#0b1433]/70 py-16 text-center"
    >
      <UIcon name="i-heroicons-calendar" class="mx-auto mb-3 h-10 w-10 text-[#2f3d67]" />
      <p class="text-sm font-medium text-[#8f9abc]">Aucun rendez-vous ce jour</p>
    </section>

    <section v-else class="overflow-hidden rounded-lg border border-[#2f3d67] bg-[#0b1433]/70">
      <div class="border-b border-[#2f3d67] px-4 py-3">
        <p class="text-sm font-semibold text-white">Appels du jour</p>
        <p class="text-xs text-[#9ba3bd]">{{ allCalls.length }} rendez-vous pour {{ selectedDayLabelLower }}</p>
      </div>

      <div class="grid gap-3 p-4 sm:grid-cols-2 lg:grid-cols-3">
        <NuxtLink
          v-for="call in allCalls"
          :key="`${call.prospect.id}-${call.callType}-summary`"
          :to="`/home/local-business/${call.prospect.id}`"
          class="rounded-lg border p-4 transition hover:-translate-y-0.5 hover:border-white/40 hover:bg-white/[0.03]"
          :class="getCallCardClasses(call.callType)"
        >
          <div class="flex items-start gap-3">
            <div
              class="flex h-9 w-9 shrink-0 items-center justify-center rounded-md"
              :class="getCallIconBoxClasses(call.callType)"
            >
              <UIcon :name="getCallIcon(call.callType)" class="h-4 w-4" :class="getCallIconClasses(call.callType)" />
            </div>
            <div class="min-w-0 flex-1">
              <div class="flex items-center justify-between gap-3">
                <p class="truncate text-sm font-semibold text-white">{{ call.prospect.name }}</p>
                <span class="shrink-0 text-xs font-semibold text-[#c7d0ea]">
                  {{ call.timeLabel || 'Journee' }}
                </span>
              </div>
              <p class="mt-1 text-xs font-semibold uppercase" :class="getCallTextClasses(call.callType)">
                {{ getCallTypeLabel(call.callType) }}
              </p>
              <p class="mt-2 text-xs text-[#9ba3bd]">{{ getProspectSubtitle(call.prospect) }}</p>
              <p v-if="call.prospect.city || call.prospect.region" class="mt-1 text-xs text-[#69759b]">
                {{ [call.prospect.city, call.prospect.region].filter(Boolean).join(', ') }}
              </p>
            </div>
          </div>
        </NuxtLink>
      </div>
    </section>
  </main>
</template>

<script lang="ts" setup>
import type { ComputedRef, Ref } from 'vue'
import type { LocalBusinessCallEvent } from '#src-core/services/ProspectsCacheService'
import { useAlyvoDarkUi } from '#src-nuxt/app/composables/useAlyvoDarkUi'
import { useLocalBusinessProspectsStore } from '#src-nuxt/app/stores/localBusinessProspects.store'
import { PARIS_TIME_ZONE, getParisDateParts, isSameDayInParis } from '#src-nuxt/app/utils/parisTime'

definePageMeta({ layout: 'home' })

/**
 * Type d'appel.
 */
type CallType = 'discovery' | 'sales'

const store: ReturnType<typeof useLocalBusinessProspectsStore> = useLocalBusinessProspectsStore()
const { iconGhostButtonClass } = useAlyvoDarkUi()
const selectedDate: Ref<Date> = ref(new Date())
const allCalls: Ref<LocalBusinessCallEvent[]> = ref([])

/**
 * Verifie si deux dates correspondent au meme jour calendaire en fuseau Paris.
 * @param {Date} a - Premiere date.
 * @param {Date} b - Deuxieme date.
 * @returns {boolean} True si meme jour.
 */
const isSameDay: (a: Date, b: Date) => boolean = (a: Date, b: Date): boolean => isSameDayInParis(a, b)

/**
 * Calcule l'ecart en jours.
 * @param {Date} date - Date selectionnee.
 * @returns {number} Ecart en jours.
 */
const getDayOffsetFromToday: (date: Date) => number = (date: Date): number => {
  const selectedParts: { year: number; month: number; day: number } = getParisDateParts(date)
  const todayParts: { year: number; month: number; day: number } = getParisDateParts(new Date())
  const selectedUtc: number = Date.UTC(selectedParts.year, selectedParts.month - 1, selectedParts.day)
  const todayUtc: number = Date.UTC(todayParts.year, todayParts.month - 1, todayParts.day)
  return Math.round((selectedUtc - todayUtc) / 86_400_000)
}

/**
 * Construit la cle date YYYY-MM-DD pour la zone Paris.
 * @param {Date} date - Date.
 * @returns {string} YYYY-MM-DD.
 */
const toParisDateKey: (date: Date) => string = (date: Date): string => {
  const parts: { year: number; month: number; day: number } = getParisDateParts(date)
  return `${parts.year}-${String(parts.month).padStart(2, '0')}-${String(parts.day).padStart(2, '0')}`
}

const formattedDate: ComputedRef<string> = computed((): string =>
  new Intl.DateTimeFormat('fr-FR', {
    timeZone: PARIS_TIME_ZONE,
    weekday: 'long',
    day: 'numeric',
    month: 'long',
    year: 'numeric',
  }).format(selectedDate.value),
)

const isTodaySelected: ComputedRef<boolean> = computed((): boolean => isSameDay(selectedDate.value, new Date()))

const selectedDayLabel: ComputedRef<string> = computed((): string => {
  const offset: number = getDayOffsetFromToday(selectedDate.value)
  if (offset === 0) return "Aujourd'hui"
  if (offset === -1) return 'Hier'
  if (offset === 1) return 'Demain'
  return new Intl.DateTimeFormat('fr-FR', {
    timeZone: PARIS_TIME_ZONE,
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
  }).format(selectedDate.value)
})

const selectedDayLabelLower: ComputedRef<string> = computed((): string => selectedDayLabel.value.toLowerCase())
const todayButtonLabel: ComputedRef<string> = computed((): string =>
  isTodaySelected.value ? "Aujourd'hui" : "Retour aujourd'hui",
)

const discoveryCallsCount: ComputedRef<number> = computed(
  (): number => allCalls.value.filter((c: LocalBusinessCallEvent): boolean => c.callType === 'discovery').length,
)
const salesCallsCount: ComputedRef<number> = computed(
  (): number => allCalls.value.filter((c: LocalBusinessCallEvent): boolean => c.callType === 'sales').length,
)

const isBusy: ComputedRef<boolean> = computed((): boolean => store.isSyncingCache || store.isLoading)

/**
 * Recharge les appels du jour selectionne.
 * @returns {Promise<void>}
 */
const refreshCalls: () => Promise<void> = async (): Promise<void> => {
  const key: string = toParisDateKey(selectedDate.value)
  allCalls.value = await store.aggregateCallsByDay(key)
}

watch(selectedDate, (): void => {
  void refreshCalls()
})

/**
 * Retourne le libelle d'un type d'appel.
 * @param {CallType} type - Type d'appel.
 * @returns {string} Libelle.
 */
const getCallTypeLabel: (type: CallType) => string = (type: CallType): string =>
  type === 'discovery' ? 'Appel decouverte' : 'Appel de vente'

/**
 * Retourne l'icone d'un type d'appel.
 * @param {CallType} type - Type d'appel.
 * @returns {string} Nom de l'icone.
 */
const getCallIcon: (type: CallType) => string = (type: CallType): string =>
  type === 'discovery' ? 'i-heroicons-phone' : 'i-heroicons-currency-euro'

/**
 * Classes de la carte.
 * @param {CallType} type - Type d'appel.
 * @returns {string} Classes CSS.
 */
const getCallCardClasses: (type: CallType) => string = (type: CallType): string =>
  type === 'discovery' ? 'border-sky-500/40 bg-sky-500/10' : 'border-[#9a65d5]/40 bg-[#9a65d5]/10'

/**
 * Classes du bloc icone.
 * @param {CallType} type - Type d'appel.
 * @returns {string} Classes CSS.
 */
const getCallIconBoxClasses: (type: CallType) => string = (type: CallType): string =>
  type === 'discovery' ? 'bg-sky-500/20' : 'bg-[#9a65d5]/20'

/**
 * Classes de l'icone.
 * @param {CallType} type - Type d'appel.
 * @returns {string} Classes CSS.
 */
const getCallIconClasses: (type: CallType) => string = (type: CallType): string =>
  type === 'discovery' ? 'text-sky-400' : 'text-[#c7a8f2]'

/**
 * Classes du libelle.
 * @param {CallType} type - Type d'appel.
 * @returns {string} Classes CSS.
 */
const getCallTextClasses: (type: CallType) => string = (type: CallType): string =>
  type === 'discovery' ? 'text-sky-300' : 'text-[#c7a8f2]'

/**
 * Construit la ligne de contexte d'un business local.
 * @param {LocalBusinessCallEvent['prospect']} prospect - Prospect.
 * @returns {string} Contexte categorie et sous-categorie.
 */
const getProspectSubtitle: (prospect: LocalBusinessCallEvent['prospect']) => string = (
  prospect: LocalBusinessCallEvent['prospect'],
): string =>
  [prospect.subcategory, prospect.category].filter(Boolean).join(' - ') || 'Informations business a completer'

/**
 * Navigue vers la date du jour.
 * @returns {void}
 */
const goToToday: () => void = (): void => {
  selectedDate.value = new Date()
}

/**
 * Navigue vers le jour precedent.
 * @returns {void}
 */
const prevDay: () => void = (): void => {
  const date: Date = new Date(selectedDate.value)
  date.setDate(date.getDate() - 1)
  selectedDate.value = date
}

/**
 * Navigue vers le jour suivant.
 * @returns {void}
 */
const nextDay: () => void = (): void => {
  const date: Date = new Date(selectedDate.value)
  date.setDate(date.getDate() + 1)
  selectedDate.value = date
}

onMounted(async (): Promise<void> => {
  await store.ensureCacheLoaded()
  await refreshCalls()
})
</script>
