<template>
  <div class="rounded-lg border border-dashed border-[#2f3d67] bg-[#0b1433]/40 p-8 text-center">
    <UIcon :name="icon" class="mx-auto h-8 w-8 text-[#9a65d5]" />
    <p class="mt-3 text-sm font-medium text-white">{{ title }}</p>
    <p v-if="description" class="mt-1 text-sm text-[#9ba3bd]">{{ description }}</p>
  </div>
</template>

<script lang="ts" setup>
/**
 * Props d'un etat vide.
 */
type EmptyStateProps = {
  title: string
  description?: string
  icon?: string
}

withDefaults(defineProps<EmptyStateProps>(), {
  description: undefined,
  icon: 'i-heroicons-inbox',
})
</script>
