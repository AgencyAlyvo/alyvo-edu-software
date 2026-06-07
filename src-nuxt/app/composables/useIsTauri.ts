import type { Ref } from 'vue'

/**
 * Detecte si l'app tourne dans le shell Tauri (reactif apres montage client).
 * @returns {{ isTauri: Ref<boolean> }} Etat reactif de detection Tauri.
 */
export function useIsTauri(): { isTauri: Ref<boolean> } {
  const isTauri: Ref<boolean> = ref(false)

  onMounted((): void => {
    /**
     * Indique si l'environnement courant est le WebView Tauri.
     * @returns {boolean} True lorsque l'API interne Tauri est disponible.
     */
    const detectTauri: () => boolean = (): boolean => {
      return import.meta.client && '__TAURI_INTERNALS__' in window
    }

    isTauri.value = detectTauri()

    if (!isTauri.value) {
      nextTick((): void => {
        isTauri.value = detectTauri()
      })
    }
  })

  return { isTauri }
}
