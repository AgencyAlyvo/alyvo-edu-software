<template>
  <main class="grid gap-6">
    <header>
      <p class="text-xs font-semibold tracking-[0.2em] text-[#9a65d5] uppercase">BUSINESS LOCAUX</p>
      <h1 class="mt-2 text-2xl font-semibold text-white">Relances Business Locaux</h1>
      <p class="mt-1 text-sm text-[#9ba3bd]">
        Business avec une prochaine action a court terme (RDV, relance, signature).
      </p>
    </header>

    <section
      v-if="!isBusy && upcoming.length === 0"
      class="rounded-lg border border-[#2f3d67] bg-[#0b1433]/70 py-16 text-center"
    >
      <UIcon name="i-heroicons-check-circle" class="mx-auto mb-3 h-10 w-10 text-[#9a65d5]" />
      <p class="text-sm font-medium text-[#8f9abc]">Aucune action urgente</p>
    </section>

    <section v-else class="overflow-hidden rounded-lg border border-[#2f3d67] bg-[#0b1433]/70">
      <div class="overflow-x-auto">
        <table class="w-full min-w-[820px] text-left text-sm">
          <thead class="border-b border-[#2f3d67] text-xs text-[#9ba3bd] uppercase">
            <tr>
              <th class="px-4 py-3">Business</th>
              <th class="px-4 py-3">Statut</th>
              <th class="px-4 py-3">Prochaine action</th>
              <th class="px-4 py-3">Echeance</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="prospect in upcoming"
              :key="prospect.id"
              class="cursor-pointer border-b border-[#1a2747] text-[#dfe6ff] last:border-0 hover:bg-[#111c35]"
              @click="$router.push(`/home/local-business/${prospect.id}`)"
            >
              <td class="px-4 py-3 font-medium text-white">{{ prospect.name }}</td>
              <td class="px-4 py-3">
                <StatusBadge :status="prospect.status" />
              </td>
              <td class="px-4 py-3 text-[#c7d0ea]">{{ prospect.nextAction ?? '-' }}</td>
              <td class="px-4 py-3 text-[#c7d0ea]">
                {{ prospect.nextActionAt ? formatDate(prospect.nextActionAt) : '-' }}
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>
  </main>
</template>

<script lang="ts" setup>
import type { ComputedRef, Ref } from 'vue'
import type { LocalBusinessProspectSummary } from '#src-core/types/response/local-business.types'
import { useLocalBusinessProspectsStore } from '#src-nuxt/app/stores/localBusinessProspects.store'
import { formatParisDate } from '#src-nuxt/app/utils/parisTime'

definePageMeta({ layout: 'home' })

const store: ReturnType<typeof useLocalBusinessProspectsStore> = useLocalBusinessProspectsStore()
const upcoming: Ref<LocalBusinessProspectSummary[]> = ref([])

const isBusy: ComputedRef<boolean> = computed((): boolean => store.isSyncingCache || store.isLoading)

/**
 * Formate une date ISO en format court francais en fuseau Paris.
 * @param {string} iso - Date ISO.
 * @returns {string} Date formatee en format court.
 */
const formatDate: (iso: string) => string = (iso: string): string =>
  formatParisDate(iso, { dateStyle: 'medium' }) ?? '-'

/**
 * Recharge la liste via le cache Rust.
 * @returns {Promise<void>}
 */
const refresh: () => Promise<void> = async (): Promise<void> => {
  upcoming.value = await store.aggregateTasksDue(7)
}

onMounted(async (): Promise<void> => {
  await store.ensureCacheLoaded()
  await refresh()
})
</script>
