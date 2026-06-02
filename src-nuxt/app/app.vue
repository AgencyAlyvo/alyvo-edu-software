<template>
  <UApp :locale="fr">
    <div>
      <Transition name="fade">
        <div
          v-if="windowTransitionStore.isLoading"
          class="fixed inset-0 z-50 flex items-center justify-center bg-[#060b12]"
        >
          <WindowTransitionLoader />
        </div>
      </Transition>

      <NuxtLayout>
        <NuxtPage />
      </NuxtLayout>
    </div>
  </UApp>
</template>

<script lang="ts" setup>
import { fr } from '@nuxt/ui/locale'
import { useWindowTransitionStore } from '#src-nuxt/app/stores/windowTransition.store'

const windowTransitionStore: ReturnType<typeof useWindowTransitionStore> = useWindowTransitionStore()
</script>

<style scoped>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.18s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
