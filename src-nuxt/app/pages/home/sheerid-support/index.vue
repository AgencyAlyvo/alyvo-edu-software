<template>
  <main class="grid max-w-2xl gap-6">
    <header>
      <h1 class="text-2xl font-semibold text-white">Support SheerID</h1>
      <p class="mt-1 text-sm text-[#9ba3bd]">
        Copiez l'email et le message type pour contacter le support SheerID (verification statut etudiant /
        Cursor Student).
      </p>
    </header>

    <section class="grid gap-4 rounded-lg border border-[#2f3d67] bg-[#0b1433]/70 p-4">
      <div class="grid gap-2">
        <div class="flex items-center justify-between gap-3">
          <label class="text-sm font-medium text-[#c5cce0]">Email</label>
          <UButton
            type="button"
            label="Copier"
            icon="i-heroicons-clipboard-document"
            variant="outline"
            size="xs"
            :class="iconGhostButtonClass"
            @click="copyText(SHEERID_SUPPORT_EMAIL, 'email')"
          />
        </div>
        <p class="rounded-md border border-[#2f3d67] bg-[#050917]/60 px-3 py-2 font-mono text-sm text-white">
          {{ SHEERID_SUPPORT_EMAIL }}
        </p>
      </div>

      <div class="grid gap-2">
        <div class="flex items-center justify-between gap-3">
          <label class="text-sm font-medium text-[#c5cce0]">Message</label>
          <UButton
            type="button"
            label="Copier"
            icon="i-heroicons-clipboard-document"
            variant="outline"
            size="xs"
            :class="iconGhostButtonClass"
            @click="copyText(SHEERID_SUPPORT_MESSAGE, 'message')"
          />
        </div>
        <pre
          class="max-h-[320px] overflow-y-auto rounded-md border border-[#2f3d67] bg-[#050917]/60 px-3 py-2 text-sm leading-relaxed whitespace-pre-wrap text-[#d6daf0]"
        >{{ SHEERID_SUPPORT_MESSAGE }}</pre>
      </div>
    </section>
  </main>
</template>

<script lang="ts" setup>
import {
  SHEERID_SUPPORT_EMAIL,
  SHEERID_SUPPORT_MESSAGE,
} from '#src-core/constants/sheerid-support.constants'

definePageMeta({ layout: 'home' })

const toast: ReturnType<typeof useToast> = useToast()
const { iconGhostButtonClass } = useAlyvoDarkUi()

type CopyTarget = 'email' | 'message'

/**
 * Copie un texte dans le presse-papiers et affiche un toast.
 * @param {string} text - Contenu a copier.
 * @param {CopyTarget} target - Cible copiee (libelle du toast).
 * @returns {Promise<void>}
 */
const copyText: (text: string, target: CopyTarget) => Promise<void> = async (
  text: string,
  target: CopyTarget,
): Promise<void> => {
  try {
    await navigator.clipboard.writeText(text)

    const titleByTarget: Record<CopyTarget, string> = {
      email: 'Email copie',
      message: 'Message copie',
    }

    toast.add({ title: titleByTarget[target], color: 'success', duration: 2500 })
  } catch {
    toast.add({ title: 'Copie impossible', color: 'error', duration: 3000 })
  }
}
</script>
