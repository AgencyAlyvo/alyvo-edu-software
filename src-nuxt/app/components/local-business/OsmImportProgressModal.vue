<template>
  <UModal v-model:open="isOpen" :dismissible="false" :ui="modalUi">
    <template #content>
      <div class="bg-[radial-gradient(circle_at_top_right,rgba(154,101,213,0.18),transparent_34%),#071022] p-6">
        <div class="mb-5 flex items-start gap-3">
          <div class="rounded-md border border-[#9a65d5]/40 bg-[#9a65d5]/10 p-2">
            <UIcon
              :name="done ? 'i-heroicons-check-circle' : 'i-heroicons-arrow-path'"
              class="h-5 w-5 text-[#c7a8f2]"
              :class="{ 'animate-spin': !done }"
            />
          </div>
          <div>
            <p class="text-xs font-semibold tracking-[0.2em] text-[#9a65d5] uppercase">IMPORT OSM</p>
            <h3 class="mt-1 text-xl font-semibold text-white">
              {{ done ? 'Import termine' : 'Import en cours...' }}
            </h3>
          </div>
        </div>

        <p class="mb-4 text-sm text-[#9ba3bd]">
          {{
            done
              ? 'Les business selectionnes ont ete traites.'
              : 'Ne ferme pas cette fenetre. L import peut prendre plusieurs minutes pour les grosses villes.'
          }}
        </p>

        <p v-if="!done" class="mb-3 text-xs text-[#9a65d5]">
          Verification des sites web et enrichissement Pages Jaunes en cours...
        </p>

        <div class="rounded-md border border-[#2f3d67] bg-[rgba(5,9,23,0.5)] p-4">
          <p class="text-center text-3xl font-semibold text-white tabular-nums">
            {{ progress.processed }}
            <span class="text-lg font-normal text-[#9ba3bd]">/ {{ progress.total }}</span>
          </p>
          <p class="mt-1 text-center text-xs text-[#9ba3bd]">business traites</p>

          <UProgress class="mt-4" :model-value="percent" color="primary" />

          <dl class="mt-4 grid grid-cols-3 gap-3 text-sm">
            <div class="rounded-md border border-[#2f3d67] bg-[#0b1433]/60 px-3 py-2">
              <dt class="text-xs text-[#9ba3bd]">Ajoutes</dt>
              <dd class="mt-0.5 text-lg font-semibold text-[#c7a8f2] tabular-nums">{{ progress.inserted }}</dd>
            </div>
            <div class="rounded-md border border-[#2f3d67] bg-[#0b1433]/60 px-3 py-2">
              <dt class="text-xs text-[#9ba3bd]">Enrichis (n8n)</dt>
              <dd class="mt-0.5 text-lg font-semibold text-[#9a65d5] tabular-nums">{{ progress.enriched }}</dd>
            </div>
            <div class="rounded-md border border-[#2f3d67] bg-[#0b1433]/60 px-3 py-2">
              <dt class="text-xs text-[#9ba3bd]">Ignores (doublons)</dt>
              <dd class="mt-0.5 text-lg font-semibold text-[#c7d0ea] tabular-nums">{{ progress.skipped }}</dd>
            </div>
          </dl>
        </div>

        <div v-if="done" class="mt-5 flex justify-end border-t border-[#2f3d67] pt-5">
          <UButton label="Fermer" :class="primaryButtonClass" @click="isOpen = false" />
        </div>
      </div>
    </template>
  </UModal>
</template>

<script lang="ts" setup>
import type { ComputedRef, Ref } from 'vue'
import type { OsmBulkImportProgress } from '#src-core/types/payload/local-business.types'
import { useAlyvoDarkUi } from '#src-nuxt/app/composables/useAlyvoDarkUi'
import { useAlyvoEditModalUi } from '#src-nuxt/app/composables/useAlyvoEditModalUi'

/**
 * Props de la modale de progression d'import OSM.
 */
type OsmImportProgressModalProps = {
  progress: OsmBulkImportProgress
  done?: boolean
}

const props: OsmImportProgressModalProps = withDefaults(defineProps<OsmImportProgressModalProps>(), {
  done: false,
})

const isOpen: Ref<boolean> = defineModel<boolean>({ default: false })
const { modalUi } = useAlyvoEditModalUi()
const { primaryButtonClass } = useAlyvoDarkUi()

const percent: ComputedRef<number> = computed((): number => {
  if (props.progress.total <= 0) {
    return 0
  }
  return Math.min(100, Math.round((props.progress.processed / props.progress.total) * 100))
})
</script>
