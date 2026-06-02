<template>
  <UModal v-model:open="isOpen" :ui="modalUi">
    <template #content>
      <div class="bg-[radial-gradient(circle_at_top_right,rgba(154,101,213,0.18),transparent_34%),#071022] p-6">
        <div class="mb-5 flex items-start gap-3">
          <div class="rounded-md border border-red-400/30 bg-red-500/10 p-2">
            <UIcon name="i-heroicons-exclamation-triangle" class="h-5 w-5 text-red-300" />
          </div>
          <div>
            <p class="text-xs font-semibold tracking-[0.2em] text-[#9a65d5] uppercase">CONFIRMATION</p>
            <h3 class="mt-1 text-xl font-semibold text-white">{{ title }}</h3>
          </div>
        </div>
        <p class="mb-6 rounded-md border border-[#2f3d67] bg-[rgba(5,9,23,0.5)] p-4 text-sm text-[#c7d0ea]">
          {{ message }}
        </p>
        <div class="flex justify-end gap-3 border-t border-[#2f3d67] pt-5">
          <UButton
            variant="ghost"
            :label="cancelLabel"
            class="rounded-md px-4 py-2 font-semibold text-[#c7d0ea] hover:bg-[#111c3f] hover:text-white"
            @click="handleCancel"
          />
          <UButton
            color="error"
            :label="confirmLabel"
            :loading="loading"
            class="rounded-md border border-red-400/40 bg-red-500/15 px-5 py-2 font-semibold text-red-100 shadow-[0_14px_30px_rgba(5,9,23,0.35)] transition hover:bg-red-500/25 disabled:brightness-[0.72]"
            @click="handleConfirm"
          />
        </div>
      </div>
    </template>
  </UModal>
</template>

<script lang="ts" setup>
import type { Ref } from 'vue'

/**
 * Props du composant ConfirmDialog.
 */
type ConfirmDialogProps = {
  title?: string
  message: string
  confirmLabel?: string
  cancelLabel?: string
  loading?: boolean
}

/**
 * Evenements emis par le composant ConfirmDialog.
 */
type ConfirmDialogEmits = {
  confirm: []
  cancel: []
}

/**
 * Signature typee de l'emetteur ConfirmDialog.
 */
type ConfirmDialogEmit = ((event: 'cancel') => void) & ((event: 'confirm') => void)

/**
 * Configuration UI de la modale de confirmation.
 */
type ModalUiConfig = { overlay: string; content: string; close: string }
const modalUi: ModalUiConfig = {
  overlay: 'bg-[#020617]/80 backdrop-blur-sm',
  content:
    'w-[calc(100vw-2rem)] max-w-lg overflow-hidden rounded-lg border border-[#2f3d67] bg-[#071022] text-white shadow-[0_24px_80px_rgba(0,0,0,0.45)] ring-0 divide-y-0',
  close: 'text-[#9ba3bd] hover:text-white hover:bg-[#111c3f]',
} as const

withDefaults(defineProps<ConfirmDialogProps>(), {
  title: 'Confirmer',
  confirmLabel: 'Confirmer',
  cancelLabel: 'Annuler',
  loading: false,
})

const emit: ConfirmDialogEmit = defineEmits<ConfirmDialogEmits>()
const isOpen: Ref<boolean> = defineModel<boolean>({ default: false })

/**
 * Emet l'evenement confirm.
 * @returns {void}
 */
const handleConfirm: () => void = (): void => {
  emit('confirm')
}

/**
 * Emet l'evenement cancel.
 * @returns {void}
 */
const handleCancel: () => void = (): void => {
  isOpen.value = false
  emit('cancel')
}
</script>
