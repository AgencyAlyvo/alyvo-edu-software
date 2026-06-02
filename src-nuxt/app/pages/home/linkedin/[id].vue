<template>
  <main class="grid gap-6">
    <template v-if="store.current">
      <div class="grid gap-6">
        <ProspectDetailInfo :prospect="store.current" />
        <ProspectActionsTimeline :actions="store.current.actions" />
      </div>
    </template>
    <EmptyState v-else title="Prospect introuvable" description="La fiche n'a pas pu etre chargee." />
  </main>
</template>

<script lang="ts" setup>
import { useLinkedinProspectsStore } from '#src-nuxt/app/stores/linkedinProspects.store'

definePageMeta({ layout: 'home' })

const route: ReturnType<typeof useRoute> = useRoute()
const store: ReturnType<typeof useLinkedinProspectsStore> = useLinkedinProspectsStore()
const prospectId: ComputedRef<number> = computed((): number => Number(route.params.id))

/**
 * Charge la fiche.
 * @returns {Promise<void>}
 */
const loadPage: () => Promise<void> = async (): Promise<void> => {
  await store.fetchOne(prospectId.value)
}

onMounted((): void => {
  void loadPage()
})
</script>
