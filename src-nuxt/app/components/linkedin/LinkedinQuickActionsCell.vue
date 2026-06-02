<template>
  <div class="flex items-center gap-1">
    <ProspectFavoriteButton
      :is-favorite="prospect.isFavorite"
      :loading="favoriteLoading"
      @toggle="emit('toggleFavorite')"
    />
    <UTooltip text="Ouvrir LinkedIn">
      <UButton
        :disabled="!prospect.linkedinUrl"
        :href="normalizeExternalUrl(prospect.linkedinUrl)"
        icon="i-heroicons-arrow-top-right-on-square"
        color="neutral"
        variant="ghost"
        class="text-[#c7d0ea] hover:bg-[#111c3f] hover:text-white"
        @click.prevent.stop="openLinkedin"
      />
    </UTooltip>
    <UTooltip text="Mettre a jour depuis LinkedIn">
      <UButton
        icon="i-heroicons-arrow-path"
        color="neutral"
        variant="ghost"
        :disabled="!prospect.linkedinUrl"
        :loading="refreshing"
        class="text-[#8fd3ff] hover:bg-[#111c3f] hover:text-white"
        @click="emit('refresh')"
      />
    </UTooltip>
    <UTooltip text="Supprimer le prospect">
      <UButton
        icon="i-heroicons-trash"
        color="error"
        variant="ghost"
        :loading="deleting"
        class="text-red-300 hover:bg-red-500/10 hover:text-red-200"
        @click="emit('delete')"
      />
    </UTooltip>
  </div>
</template>

<script lang="ts" setup>
import type { LinkedinProspectSummary } from '#src-core/types/response/linkedin.types'
import { normalizeExternalUrl, openExternalUrl } from '#src-nuxt/app/utils/externalUrl'

/**
 * Props des actions rapides.
 */
type LinkedinQuickActionsCellProps = {
  prospect: LinkedinProspectSummary
  refreshing?: boolean
  deleting?: boolean
  favoriteLoading?: boolean
}

/**
 *
 */
type LinkedinQuickActionsCellEmits = {
  refresh: []
  delete: []
  toggleFavorite: []
}

const props: LinkedinQuickActionsCellProps = defineProps<LinkedinQuickActionsCellProps>()
const emit: ((event: 'refresh') => void) & ((event: 'delete') => void) & ((event: 'toggleFavorite') => void) =
  defineEmits<LinkedinQuickActionsCellEmits>()

/**
 * Ouvre la page LinkedIn du prospect.
 * @returns {Promise<void>} Promesse resolue apres ouverture.
 */
const openLinkedin: () => Promise<void> = async (): Promise<void> => {
  await openExternalUrl(props.prospect.linkedinUrl)
}
</script>
