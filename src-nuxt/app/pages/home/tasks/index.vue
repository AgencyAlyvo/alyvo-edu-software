<template>
  <main class="grid gap-6">
    <header>
      <p class="text-xs font-semibold tracking-[0.2em] text-[#9a65d5] uppercase">LINKEDIN</p>
      <h1 class="mt-2 text-2xl font-semibold text-white">Relances LinkedIn</h1>
      <p class="mt-1 text-sm text-[#9ba3bd]">
        Relances calculees depuis la date du message 1 et vos delais (parametres LinkedIn).
      </p>
    </header>

    <TasksTable :relances="store.dueRelances" :loading="store.isLoading" />
  </main>
</template>

<script lang="ts" setup>
import { useTasksStore } from '#src-nuxt/app/stores/tasks.store'

definePageMeta({ layout: 'home' })

const store: ReturnType<typeof useTasksStore> = useTasksStore()

onMounted((): void => {
  void store.fetchDue()
})
</script>
