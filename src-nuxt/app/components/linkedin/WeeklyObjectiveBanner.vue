<template>
  <section class="rounded-lg border border-[#2f3d67] bg-[#0b1433]/70 p-5">
    <div class="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
      <div>
        <p class="text-sm text-[#9ba3bd]">Objectif invitations</p>
        <h2 class="mt-1 text-xl font-semibold text-white">{{ objective?.invitesSent ?? 0 }} / {{ targetValue }}</h2>
      </div>
      <div class="rounded-md border border-[#2f3d67] bg-[#050917]/70 px-4 py-3 text-right">
        <p class="text-xs text-[#9ba3bd]">Paramètre LinkedIn</p>
        <p class="mt-1 text-sm font-semibold text-white">{{ targetValue }} invitations / semaine</p>
      </div>
    </div>
    <UProgress class="mt-4" :model-value="objective?.progressionPercent ?? 0" color="primary" />
  </section>
</template>

<script lang="ts" setup>
import type { WeeklyObjective } from '#src-core/types/response/weekly.types'

/**
 * Props de la banniere objectif.
 */
type WeeklyObjectiveBannerProps = {
  objective?: WeeklyObjective
}

const props: WeeklyObjectiveBannerProps = defineProps<WeeklyObjectiveBannerProps>()
const targetValue: ComputedRef<number> = computed((): number => props.objective?.invitesTarget ?? 0)
</script>
