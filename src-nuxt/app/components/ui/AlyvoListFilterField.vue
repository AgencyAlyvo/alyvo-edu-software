<template>
  <div class="flex min-w-0 flex-col gap-1">
    <span class="text-xs font-medium text-[#c7d0ea]">{{ label }}</span>
    <p v-if="hint" class="text-[11px] leading-snug text-[#9ba3bd]">
      {{ hint }}
    </p>
    <div class="w-full min-w-0">
      <slot />
    </div>
  </div>
</template>

<script lang="ts" setup>
/**
 * Libelle + aide pour un champ de filtre de liste.
 */
type AlyvoListFilterFieldProps = {
  label: string
  hint?: string
}

defineProps<AlyvoListFilterFieldProps>()
</script>
