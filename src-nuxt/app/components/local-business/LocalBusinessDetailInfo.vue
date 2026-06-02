<template>
  <div class="flex flex-col gap-4">
    <section class="grid gap-4 rounded-lg border border-[#2f3d67] bg-[#0b1433]/70 p-5 md:grid-cols-2">
      <div class="flex items-start justify-between md:col-span-2">
        <p class="text-2xl font-bold text-white">{{ prospect.name }}</p>
        <UTooltip text="Modifier">
          <UButton
            icon="i-heroicons-pencil-square"
            size="sm"
            color="neutral"
            variant="ghost"
            class="text-[#9ba3bd] hover:bg-[#111c3f] hover:text-white"
            @click="editOpen = true"
          />
        </UTooltip>
      </div>

      <div v-for="item in items" :key="item.label" :class="item.wide ? 'md:col-span-2' : undefined">
        <p class="text-xs text-[#9ba3bd] uppercase">{{ item.label }}</p>
        <a
          v-if="item.href && item.value"
          :href="item.href"
          class="mt-1 inline-block text-sm break-words text-[#c7a8f2] transition-colors hover:text-white hover:underline"
          :target="item.external ? '_blank' : undefined"
          :rel="item.external ? 'noopener noreferrer' : undefined"
        >
          {{ item.value }}
        </a>
        <p v-else :class="['mt-1 text-sm break-words text-white', item.multiline ? 'whitespace-pre-line' : '']">
          {{ item.value || '-' }}
        </p>
        <p v-if="item.hint" class="mt-1 text-xs text-[#9ba3bd]">{{ item.hint }}</p>
      </div>
    </section>

    <LocalBusinessCommercialTracking :prospect="prospect" />

    <LocalBusinessEditModal v-model="editOpen" :prospect="prospect" />
  </div>
</template>

<script lang="ts" setup>
import type { Ref } from 'vue'
import { getLocalBusinessOsmTypeLabel } from '#src-core/constants/localBusinessOsmTypeLabels'
import type { LocalBusinessProspectFull } from '#src-core/types/response/local-business.types'
import { formatOsmOpeningHoursForDisplay } from '#src-nuxt/app/utils/formatOsmOpeningHours'

/**
 * Props de la carte identite d'un business local.
 */
type LocalBusinessDetailInfoProps = {
  prospect: LocalBusinessProspectFull
}

/**
 * Ligne affichee dans la grille identite.
 */
type DetailItem = {
  label: string
  value: string | null
  href?: string
  external?: boolean
  multiline?: boolean
  wide?: boolean
  hint?: string
}

const props: LocalBusinessDetailInfoProps = defineProps<LocalBusinessDetailInfoProps>()
const editOpen: Ref<boolean> = ref(false)

const osmTypeLabel: ComputedRef<string> = computed((): string =>
  getLocalBusinessOsmTypeLabel(props.prospect.subcategory, props.prospect.category),
)

const openingHoursLabel: ComputedRef<string> = computed((): string => {
  const formatted: string | null = formatOsmOpeningHoursForDisplay(props.prospect.openingHours)
  return formatted ?? '-'
})

const items: ComputedRef<DetailItem[]> = computed((): DetailItem[] => [
  { label: 'Type de commerce', value: osmTypeLabel.value },
  { label: 'Adresse', value: props.prospect.address },
  { label: 'Code postal', value: props.prospect.postalCode },
  { label: 'Ville', value: props.prospect.city },
  { label: 'Region', value: props.prospect.region },
  { label: 'Pays', value: props.prospect.country ?? 'France' },
  {
    label: 'Email',
    value: props.prospect.email,
    href: props.prospect.email ? `mailto:${props.prospect.email}` : undefined,
    hint: props.prospect.email && props.prospect.emailSource ? `Source : ${props.prospect.emailSource}` : undefined,
  },
  {
    label: 'Telephone',
    value: props.prospect.phone,
    href: props.prospect.phone ? `tel:${props.prospect.phone}` : undefined,
  },
  {
    label: 'URL Site web',
    value: props.prospect.website,
    href: props.prospect.website ?? undefined,
    external: true,
  },
  {
    label: 'URL Pages Jaunes',
    value: props.prospect.pagesJaunesUrl,
    href: props.prospect.pagesJaunesUrl ?? undefined,
    external: true,
  },
  {
    label: 'Horaires',
    value: openingHoursLabel.value,
    multiline: true,
    wide: true,
  },
  {
    label: 'Source OSM',
    value:
      props.prospect.osmType && props.prospect.osmId
        ? `${props.prospect.osmType}/${props.prospect.osmId}`
        : 'Saisi manuellement',
  },
])
</script>
