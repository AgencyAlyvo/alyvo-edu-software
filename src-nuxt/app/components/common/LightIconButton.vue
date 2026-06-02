<template>
  <button
    type="button"
    :title="title"
    :aria-label="title"
    :disabled="disabled || loading"
    :class="[
      'inline-flex h-8 w-8 cursor-pointer items-center justify-center rounded-md transition-colors disabled:cursor-not-allowed disabled:opacity-40',
      tone === 'danger'
        ? 'text-red-300 hover:bg-red-500/10 hover:text-red-200'
        : tone === 'info'
          ? 'text-[#8fd3ff] hover:bg-[#111c3f] hover:text-white'
          : tone === 'favorite-active'
            ? 'text-amber-300 hover:bg-amber-500/10 hover:text-amber-200'
            : 'text-[#c7d0ea] hover:bg-[#111c3f] hover:text-white',
    ]"
    @click="onClick"
  >
    <UIcon v-if="loading" name="i-heroicons-arrow-path" class="h-4 w-4 animate-spin" />
    <UIcon v-else :name="icon" class="h-4 w-4" />
  </button>
</template>

<script lang="ts" setup>
/**
 * Tonalite visuelle du bouton.
 */
type LightIconButtonTone = 'neutral' | 'danger' | 'info' | 'favorite-active'

/**
 * Props du bouton icone.
 */
type LightIconButtonProps = {
  icon: string
  title: string
  tone?: LightIconButtonTone
  loading?: boolean
  disabled?: boolean
}

/**
 * Evenements du bouton.
 */
type LightIconButtonEmits = {
  click: [event: MouseEvent]
}

withDefaults(defineProps<LightIconButtonProps>(), {
  tone: 'neutral',
  loading: false,
  disabled: false,
})

const emit: (event: 'click', payload: MouseEvent) => void = defineEmits<LightIconButtonEmits>()

/**
 * Gere le clic en propageant l'evenement uniquement si non desactive.
 * @param {MouseEvent} event - Evenement de clic.
 * @returns {void}
 */
const onClick: (event: MouseEvent) => void = (event: MouseEvent): void => {
  emit('click', event)
}
</script>
