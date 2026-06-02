<template>
  <div class="relative flex h-9 items-center justify-between bg-black text-center select-none" data-tauri-drag-region>
    <div class="w-[96px]"></div>

    <!-- Slot centré pour le contenu (logo sur /home). pointer-events-none pour laisser le drag fonctionner. -->
    <div
      class="pointer-events-none absolute left-1/2 flex h-full -translate-x-1/2 items-center justify-center"
      data-tauri-drag-region
    >
      <slot></slot>
    </div>

    <!-- Boutons de contrôle de la fenêtre. -->
    <div v-if="appWindow" class="flex h-full flex-shrink-0 items-center space-x-1">
      <!-- Bouton de minimisation. -->
      <button
        id="titlebar-minimize"
        class="titlebar-button flex h-full w-8 items-center justify-center text-[#85868a] hover:bg-gray-800 hover:text-white"
        type="button"
        aria-label="Minimiser"
        @click="btnMinimizeWindow"
      >
        <UIcon name="i-heroicons-minus" class="h-[17px] w-[17px]" />
      </button>

      <!-- Bouton de maximisation, masqué sur les pages login et signup. -->
      <button
        v-if="!isAuthRoute"
        id="titlebar-maximize"
        class="titlebar-button flex h-full w-8 items-center justify-center text-[#85868a] hover:bg-gray-800 hover:text-white"
        type="button"
        aria-label="Agrandir"
        @click="btnMaximizeWindow"
      >
        <UIcon name="i-heroicons-stop" class="h-[13px] w-[13px]" />
      </button>

      <!-- Bouton de fermeture. -->
      <button
        id="titlebar-close"
        class="titlebar-button ml-1 flex h-full w-8 items-center justify-center text-[#85868a] hover:bg-gray-800 hover:text-white"
        type="button"
        aria-label="Fermer"
        @click="btnCloseWindow"
      >
        <UIcon name="i-heroicons-x-mark" class="h-[17px] w-[17px]" />
      </button>
    </div>
  </div>
</template>

<script lang="ts" setup>
import { computed } from 'vue'
import type { ComputedRef } from 'vue'

import type { Window as TauriWindow } from '@tauri-apps/api/window'
import { getCurrentWindow } from '@tauri-apps/api/window'

/**
 * Recupere la fenetre Tauri quand l'app tourne dans le shell desktop.
 * @returns {TauriWindow | undefined} Fenetre Tauri ou undefined dans un navigateur web.
 */
const resolveAppWindow: () => TauriWindow | undefined = (): TauriWindow | undefined => {
  if (!import.meta.client || !('__TAURI_INTERNALS__' in window)) {
    return undefined
  }

  try {
    return getCurrentWindow()
  } catch {
    return undefined
  }
}

const appWindow: TauriWindow | undefined = resolveAppWindow()
const route: ReturnType<typeof useRoute> = useRoute()

// Vrai sur les pages d'authentification où le bouton maximize ne doit pas apparaître.
const isAuthRoute: ComputedRef<boolean> = computed((): boolean => route.path === '/login' || route.path === '/signup')

/**
 * Minimise la fenetre.
 * @returns {Promise<void>} Promesse résolue après minimisation.
 */
const btnMinimizeWindow: () => Promise<void> = async (): Promise<void> => {
  await appWindow?.minimize()
}

/**
 * Bascule la fenetre entre maximise et restaure.
 * @returns {Promise<void>} Promesse résolue après le basculement.
 */
const btnMaximizeWindow: () => Promise<void> = async (): Promise<void> => {
  await appWindow?.toggleMaximize()
}

/**
 * Cache la fenetre.
 * @returns {Promise<void>} Promesse résolue après masquage.
 */
const btnCloseWindow: () => Promise<void> = async (): Promise<void> => {
  await appWindow?.hide()
}
</script>
