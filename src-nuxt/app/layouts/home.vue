<template>
  <div class="flex h-screen flex-col bg-[#0f172a] text-slate-200">
    <!-- Barre de fenêtre Tauri avec le logo Alyvo centré. -->
    <WindowBar>
      <img class="h-5 select-none" src="/logo-alyvo.png" alt="Alyvo" draggable="false" />
    </WindowBar>

    <main class="flex h-full flex-1 overflow-hidden">
      <SideBarLeft />

      <!-- Zone de contenu centrale, marges ajustées selon la largeur de la fenêtre. -->
      <div
        class="flex-grow overflow-x-hidden overflow-y-auto p-10 pr-[104px] transition-all duration-300"
        :class="{
          'ml-[64px]': windowWidth < 1280,
          'ml-[260px]': windowWidth >= 1280,
        }"
      >
        <!-- Navigation historique retour / avance. -->
        <div class="mb-5 flex items-center gap-1">
          <UTooltip text="Page précédente">
            <UButton
              icon="i-heroicons-arrow-left"
              size="sm"
              color="neutral"
              variant="ghost"
              :disabled="!canGoBack"
              class="text-[#9ba3bd] hover:bg-[#111c3f] hover:text-white disabled:opacity-30"
              @click="router.back()"
            />
          </UTooltip>
          <UTooltip text="Page suivante">
            <UButton
              icon="i-heroicons-arrow-right"
              size="sm"
              color="neutral"
              variant="ghost"
              :disabled="!canGoForward"
              class="text-[#9ba3bd] hover:bg-[#111c3f] hover:text-white disabled:opacity-30"
              @click="router.forward()"
            />
          </UTooltip>
        </div>

        <slot />
      </div>

      <SideBarRight />
    </main>
  </div>
</template>

<script lang="ts" setup>
import { onMounted, onUnmounted, ref, watch } from 'vue'
import type { Ref } from 'vue'

import SideBarLeft from '#src-nuxt/app/components/navigations/SideBarLeft.vue'
import SideBarRight from '#src-nuxt/app/components/navigations/SideBarRight.vue'

// Largeur courante de la fenêtre pour adapter les marges du contenu central.
const windowWidth: Ref<number> = ref(window.innerWidth)
const router: ReturnType<typeof useRouter> = useRouter()
const route: ReturnType<typeof useRoute> = useRoute()
const canGoBack: Ref<boolean> = ref(false)
const canGoForward: Ref<boolean> = ref(false)

/**
 * Met à jour les flags retour/avance depuis l'état History API.
 */
const updateHistory: () => void = (): void => {
  canGoBack.value = !!window.history.state?.back
  canGoForward.value = !!window.history.state?.forward
}

watch(() => route.path, updateHistory, { immediate: true })

/**
 * Gère le redimensionnement de la fenêtre.
 */
const handleResize: () => void = (): void => {
  windowWidth.value = window.innerWidth
}

onMounted((): void => {
  windowWidth.value = window.innerWidth
  window.addEventListener('resize', handleResize)
})

onUnmounted((): void => {
  window.removeEventListener('resize', handleResize)
})
</script>
