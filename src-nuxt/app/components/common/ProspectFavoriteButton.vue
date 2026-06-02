<template>
  <UTooltip :text="isFavorite ? 'Retirer des favoris' : 'Ajouter aux favoris'">
    <UButton
      :icon="isFavorite ? 'i-heroicons-star-solid' : 'i-heroicons-star'"
      size="sm"
      color="neutral"
      variant="ghost"
      :loading="loading"
      :class="[
        isFavorite
          ? 'text-amber-300 hover:bg-amber-500/10 hover:text-amber-200'
          : 'text-[#9ba3bd] hover:bg-[#111c3f] hover:text-amber-200',
      ]"
      :aria-pressed="isFavorite"
      :aria-label="isFavorite ? 'Retirer des favoris' : 'Ajouter aux favoris'"
      @click="emit('toggle')"
    />
  </UTooltip>
</template>

<script lang="ts" setup>
/**
 * Props du bouton favori.
 */
type ProspectFavoriteButtonProps = {
  isFavorite: boolean
  loading?: boolean
}

/**
 * Evenements du bouton favori.
 */
type ProspectFavoriteButtonEmits = {
  toggle: []
}

defineProps<ProspectFavoriteButtonProps>()
const emit: (event: 'toggle') => void = defineEmits<ProspectFavoriteButtonEmits>()
</script>
