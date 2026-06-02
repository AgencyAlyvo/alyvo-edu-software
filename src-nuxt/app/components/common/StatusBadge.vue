<template>
  <UBadge
    :color="badge.color"
    variant="soft"
    :label="badge.label"
    :class="wrap ? 'h-auto max-w-full items-start py-1.5' : undefined"
    :ui="wrap ? badgeWrapUi : undefined"
  />
</template>

<script lang="ts" setup>
import { useStatusBadge } from '#src-nuxt/app/composables/useStatusBadge'
import type { LinkedinProspectStatus } from '#src-core/types/enums/linkedin.enums'
import type { StatusBadgeConfig } from '#src-nuxt/app/composables/useStatusBadge'

/**
 * Props du badge de statut.
 */
type StatusBadgeProps = {
  status?: LinkedinProspectStatus | string | null
  /** Permet le retour a la ligne pour les libelles longs. */
  wrap?: boolean
}

/** Styles Nuxt UI pour un badge multiligne. */
type BadgeWrapUiConfig = { label: string }
const badgeWrapUi: BadgeWrapUiConfig = {
  label: 'whitespace-normal text-left leading-snug',
} as const

const props: StatusBadgeProps = withDefaults(defineProps<StatusBadgeProps>(), {
  status: null,
  wrap: false,
})
const { getStatusBadge }: ReturnType<typeof useStatusBadge> = useStatusBadge()
const badge: ComputedRef<StatusBadgeConfig> = computed((): StatusBadgeConfig => getStatusBadge(props.status))
</script>
