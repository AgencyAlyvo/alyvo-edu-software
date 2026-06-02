<template>
  <main class="grid gap-6">
    <template v-if="store.current">
      <header class="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
        <div>
          <p class="text-xs font-semibold tracking-[0.2em] text-[#9a65d5] uppercase">BUSINESS LOCAL</p>
          <h1 class="mt-2 text-2xl font-semibold text-white">Fiche business</h1>
        </div>
        <div class="flex gap-2">
          <UButton
            icon="i-heroicons-sparkles"
            label="Enrichir"
            :loading="store.isEnriching"
            :class="primaryButtonClass"
            @click="enrich"
          />
          <UButton
            icon="i-heroicons-arrow-left"
            label="Retour"
            variant="ghost"
            color="neutral"
            :class="ghostButtonClass"
            @click="$router.back()"
          />
        </div>
      </header>

      <div class="grid gap-6">
        <LocalBusinessDetailInfo :prospect="store.current" />

        <LocalBusinessSeoCard :prospect="store.current" :loading="store.isEnriching" @refresh="enrich" />

        <section v-if="store.current.actions.length > 0" class="rounded-lg border border-[#2f3d67] bg-[#0b1433]/70 p-5">
          <h3 class="mb-4 text-lg font-semibold text-white">Historique</h3>
          <ul class="grid gap-3">
            <li
              v-for="action in store.current.actions"
              :key="action.id"
              class="flex items-start gap-3 rounded-md border border-[#1a2747] bg-[#071022] p-3 text-sm"
            >
              <UIcon name="i-heroicons-clock" class="mt-0.5 h-4 w-4 text-[#9a65d5]" />
              <div class="flex-1">
                <p class="font-medium text-white">{{ actionLabel(action.actionType) }}</p>
                <p v-if="action.content" class="mt-1 text-xs text-[#c7d0ea]">{{ action.content }}</p>
                <p class="mt-1 text-xs text-[#69759b]">{{ formatDate(action.occurredAt) }}</p>
              </div>
            </li>
          </ul>
        </section>
      </div>
    </template>
    <EmptyState v-else title="Business introuvable" description="La fiche n'a pas pu etre chargee." />
  </main>
</template>

<script lang="ts" setup>
import { localBusinessActionTypeLabels } from '#src-core/constants/localBusinessSelectableStatuses'
import type { ProspectActionType } from '#src-core/types/enums/linkedin.enums'
import { useAlyvoDarkUi } from '#src-nuxt/app/composables/useAlyvoDarkUi'
import { useLocalBusinessProspectsStore } from '#src-nuxt/app/stores/localBusinessProspects.store'

definePageMeta({ layout: 'home' })

const store: ReturnType<typeof useLocalBusinessProspectsStore> = useLocalBusinessProspectsStore()
const toast: ReturnType<typeof useToast> = useToast()
const route: ReturnType<typeof useRoute> = useRoute()
const { primaryButtonClass, ghostButtonClass } = useAlyvoDarkUi()

/**
 * Lance l'enrichissement n8n du business courant.
 * @returns {Promise<void>}
 */
const enrich: () => Promise<void> = async (): Promise<void> => {
  if (!store.current) return
  try {
    await store.enrich(store.current.id)
    toast.add({
      title: 'Enrichissement effectue',
      description: 'Scores Lighthouse et emails mis a jour.',
      color: 'success',
      duration: 3000,
    })
  } catch (err) {
    toast.add({
      title: "Echec de l'enrichissement",
      description: (err as Error).message,
      color: 'error',
      duration: 5000,
    })
  }
}

/**
 * Formate une date ISO pour affichage dans la timeline.
 * @param {string} iso - Date ISO.
 * @returns {string} Date formatee en francais.
 */
const formatDate: (iso: string) => string = (iso: string): string =>
  new Intl.DateTimeFormat('fr-FR', { dateStyle: 'medium', timeStyle: 'short' }).format(new Date(iso))

/**
 * Retourne le libelle francais d'un type d'action prospect.
 * @param {string} type - Type d'action technique.
 * @returns {string} Libelle affichable.
 */
const actionLabel: (type: string) => string = (type: string): string =>
  localBusinessActionTypeLabels[type as ProspectActionType] ?? type

onMounted((): void => {
  void store.fetchOne(Number(route.params.id))
})
</script>
