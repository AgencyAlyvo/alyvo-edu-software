<template>
  <main class="grid max-w-2xl gap-6">
    <header>
      <h1 class="text-2xl font-semibold text-white">Paramètres</h1>
      <p class="mt-1 text-sm text-[#9ba3bd]">
        Configuration locale de l'application desktop (stockée sur cet ordinateur).
      </p>
    </header>

    <UAlert v-if="!isTauri" color="warning" variant="soft" title="Disponible uniquement dans l'application desktop" />

    <form class="grid gap-4 rounded-lg border border-[#2f3d67] bg-[#0b1433]/70 p-4" @submit.prevent="onSave">
      <AlyvoListFilterField
        label="Chemin windscribe-cli.exe"
        hint="Avant chaque lot de 2 comptes : connexion VPN, flush DNS, puis Chrome (Windscribe doit être installé et connecté)."
      >
        <div class="flex flex-col gap-2 sm:flex-row sm:items-center">
          <UInput
            v-model="settingsStore.windscribeCliPath"
            type="text"
            placeholder="C:\Program Files\Windscribe\windscribe-cli.exe"
            variant="none"
            :ui="inputUi"
            :disabled="!isTauri"
            class="min-w-0 flex-1 font-mono text-xs"
          />
          <UButton
            type="button"
            label="Parcourir…"
            icon="i-heroicons-folder-open"
            variant="outline"
            :disabled="!isTauri"
            class="shrink-0"
            @click="onBrowseWindscribeCli"
          />
        </div>
      </AlyvoListFilterField>

      <AlyvoListFilterField
        label="Localisation Windscribe"
        hint="Argument passé à « connect » (ex. US, Toronto, best)."
      >
        <UInput
          v-model="settingsStore.windscribeLocation"
          type="text"
          placeholder="US"
          variant="none"
          :ui="inputUi"
          :disabled="!isTauri"
          class="max-w-[200px]"
        />
      </AlyvoListFilterField>

      <AlyvoListFilterField
        label="Clé API CapSolver"
        hint="Résolution reCAPTCHA v2 sur le portail Broward. Obtenez une clé sur capsolver.com (stockée uniquement sur cet ordinateur)."
      >
        <div class="flex flex-col gap-2 sm:flex-row sm:items-center">
          <UInput
            v-model="settingsStore.capsolverApiKey"
            :type="showCapSolverKey ? 'text' : 'password'"
            placeholder="CAP-XXXXXXXXXXXXXXXX"
            variant="none"
            :ui="inputUi"
            :disabled="!isTauri"
            class="min-w-0 flex-1 font-mono text-xs"
          />
          <UButton
            type="button"
            :icon="showCapSolverKey ? 'i-heroicons-eye-slash' : 'i-heroicons-eye'"
            variant="outline"
            :disabled="!isTauri"
            class="shrink-0"
            aria-label="Afficher ou masquer la clé API"
            @click="showCapSolverKey = !showCapSolverKey"
          />
        </div>
      </AlyvoListFilterField>

      <div class="flex flex-wrap gap-2">
        <UButton
          type="submit"
          icon="i-heroicons-check"
          label="Enregistrer"
          :disabled="!isTauri"
          :class="primaryButtonClass"
        />
        <UButton
          type="button"
          label="Valeurs par défaut"
          variant="ghost"
          :disabled="!isTauri"
          @click="settingsStore.resetToDefaults()"
        />
      </div>

      <UAlert
        v-if="settingsStore.savedMessage"
        color="success"
        variant="soft"
        :title="settingsStore.savedMessage"
        @click="settingsStore.savedMessage = null"
      />
    </form>

    <section class="rounded-lg border border-[#2f3d67] bg-[#050917] p-4 text-sm text-[#9ba3bd]">
      <h2 class="mb-2 font-medium text-white">Inscription Broward (CapSolver)</h2>
      <p>
        La clé API est transmise au sidecar via une variable d'environnement locale (jamais envoyée au serveur Alyvo).
        Consultez votre solde sur le
        <a href="https://www.capsolver.com/" target="_blank" rel="noopener noreferrer" class="text-[#9a65d5] underline"
          >tableau de bord CapSolver</a
        >.
      </p>
    </section>

    <section class="rounded-lg border border-[#2f3d67] bg-[#050917] p-4 text-sm text-[#9ba3bd]">
      <h2 class="mb-2 font-medium text-white">Création Outlook par lots de 2</h2>
      <p>Avant chaque lot de 2 comptes (y compris le premier), l'application exécute automatiquement :</p>
      <ol class="mt-2 list-inside list-decimal space-y-1 pl-1">
        <li>Fermeture de Chrome (à partir du 3<sup>e</sup> compte)</li>
        <li><span class="text-[#c5cce0]">windscribe-cli connect « localisation »</span></li>
        <li><span class="text-[#c5cce0]">ipconfig /flushdns</span> (avant l'ouverture de Chrome)</li>
        <li>Lancement de nodriver / Chrome pour les 2 comptes du lot</li>
      </ol>
    </section>
  </main>
</template>

<script lang="ts" setup>
import type { Ref } from 'vue'

import { open } from '@tauri-apps/plugin-dialog'

import AlyvoListFilterField from '#src-nuxt/app/components/ui/AlyvoListFilterField.vue'
import { useAlyvoDarkUi } from '#src-nuxt/app/composables/useAlyvoDarkUi'
import { useIsTauri } from '#src-nuxt/app/composables/useIsTauri'
import { useDesktopSettingsStore } from '#src-nuxt/app/stores/desktopSettings.store'

definePageMeta({ layout: 'home' })

const { isTauri } = useIsTauri()
const settingsStore: ReturnType<typeof useDesktopSettingsStore> = useDesktopSettingsStore()
const { inputUi, primaryButtonClass } = useAlyvoDarkUi()
const showCapSolverKey: Ref<boolean> = ref(false)

onMounted((): void => {
  settingsStore.load()
})

/**
 * Ouvre un dialogue pour choisir windscribe-cli.exe.
 */
const onBrowseWindscribeCli: () => Promise<void> = async (): Promise<void> => {
  if (!isTauri.value) {
    return
  }

  const selected: string | string[] | null = await open({
    multiple: false,
    filters: [{ name: 'Executable Windows', extensions: ['exe'] }],
    title: 'Sélectionner windscribe-cli.exe',
  })

  if (typeof selected === 'string' && selected.length > 0) {
    settingsStore.windscribeCliPath = selected
  }
}

/**
 * Persiste les parametres desktop.
 */
const onSave: () => void = (): void => {
  settingsStore.save()
}
</script>
