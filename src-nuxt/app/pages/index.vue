<template>
  <main class="flex h-screen flex-col items-center justify-center bg-[#060b12] px-8 text-white">
    <img class="mb-10 w-40 select-none" src="/logo-alyvo.png" alt="Alyvo" draggable="false" />

    <AutoUpdateLoader />

    <p class="mt-6 text-center font-sans text-lg font-medium">{{ updateStatus }}</p>

    <div v-if="updateAvailable" class="mt-5 h-3 w-72 overflow-hidden rounded-full bg-white/15">
      <div class="h-full bg-[#2fb7ff] transition-all duration-200" :style="{ width: `${downloadProgress}%` }"></div>
    </div>

    <p v-if="updateStatusDownload" class="mt-4 text-center font-sans text-sm text-white/75">
      {{ updateStatusDownload }}
    </p>
  </main>
</template>

<script lang="ts" setup>
import { relaunch } from '@tauri-apps/plugin-process'
import type { DownloadEvent, Update } from '@tauri-apps/plugin-updater'
import { check } from '@tauri-apps/plugin-updater'
import { onMounted, ref } from 'vue'
import type { Ref } from 'vue'

import { TauriWindowService } from '#src-core/services/TauriWindowService'
import { useWindowTransitionStore } from '#src-nuxt/app/stores/windowTransition.store'

/**
 * Runtime config public utile pour l'ecran d'auto-update.
 */
type PublicRuntimeConfig = {
  appEnv?: string
}

const runtimeConfig: ReturnType<typeof useRuntimeConfig> = useRuntimeConfig()
const publicRuntimeConfig: PublicRuntimeConfig = runtimeConfig.public
const appEnv: string = publicRuntimeConfig.appEnv || 'development'
const windowTransitionStore: ReturnType<typeof useWindowTransitionStore> = useWindowTransitionStore()

/* REFS */
const updateStatus: Ref<string> = ref('Checking for updates...')
const updateStatusDownload: Ref<string> = ref('')
const downloadProgress: Ref<number> = ref(0)
const updateAvailable: Ref<boolean> = ref(false)

/* DATA */
let contentLengthUpdate: number | undefined = undefined
let downloadedUpdateBytes: number = 0

/* METHODS */
/**
 * Configure la fenetre puis redirige vers la page de connexion.
 * @returns {Promise<void>}
 */
const goToLogin: () => Promise<void> = async (): Promise<void> => {
  windowTransitionStore.setLoading(true)

  try {
    await TauriWindowService.configureLoginWindow()
    await navigateTo('/login')
  } finally {
    windowTransitionStore.setLoading(false)
  }
}

/**
 * Met a jour l'etat d'affichage pendant le telechargement de l'update.
 * @param {DownloadEvent} downloadEvent - Evenement envoye par le plugin updater.
 * @returns {void}
 */
const updateDownloadProgress: (downloadEvent: DownloadEvent) => void = (downloadEvent: DownloadEvent): void => {
  switch (downloadEvent.event) {
    case 'Started':
      updateStatusDownload.value = 'Download started...'
      contentLengthUpdate = downloadEvent.data.contentLength
      downloadedUpdateBytes = 0
      downloadProgress.value = 0
      return
    case 'Progress': {
      downloadedUpdateBytes += downloadEvent.data.chunkLength

      if (!contentLengthUpdate) {
        updateStatusDownload.value = 'Download in progress...'
        return
      }

      const progressPercentage: number = (downloadedUpdateBytes / contentLengthUpdate) * 100
      updateDownloadProgressPercentage(progressPercentage)
      return
    }
    case 'Finished':
      updateStatusDownload.value = 'Download completed.'
      downloadProgress.value = 100
  }
}

/**
 * Normalise la progression et met a jour les textes de telechargement.
 * @param {number} progressPercentage - Pourcentage brut de progression.
 * @returns {void}
 */
const updateDownloadProgressPercentage: (progressPercentage: number) => void = (progressPercentage: number): void => {
  const normalizedProgress: number = Math.min(progressPercentage, 100)
  updateStatusDownload.value = `Download progress: ${normalizedProgress.toFixed(2)}%`
  downloadProgress.value = normalizedProgress
}

/**
 * Verifie, telecharge et installe une update desktop si elle existe.
 * @returns {Promise<void>}
 */
const autoUpdateApplication: () => Promise<void> = async (): Promise<void> => {
  if (appEnv === 'development') {
    updateStatus.value = 'Development mode.'
    await goToLogin()
    return
  }

  try {
    const update: Update | null = await check()

    if (update?.available) {
      updateAvailable.value = true
      updateStatus.value = `Update v${update.version} found.`

      await update.downloadAndInstall(updateDownloadProgress)
      await relaunch()
      return
    }

    updateStatus.value = 'Application already up to date.'
    await goToLogin()
  } catch (error) {
    console.error('Update error:', error)
    updateStatus.value = 'Error checking for updates.'
    updateStatusDownload.value = 'Please restart the application or try again later.'
  }
}

/* HOOKS */
onMounted(async (): Promise<void> => {
  await autoUpdateApplication()
})
</script>
