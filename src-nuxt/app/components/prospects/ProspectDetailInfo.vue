<template>
  <div class="flex flex-col gap-4">
    <section class="grid gap-4 rounded-lg border border-[#2f3d67] bg-[#0b1433]/70 p-5 md:grid-cols-2">
      <div class="flex items-start justify-between md:col-span-2">
        <p class="text-2xl font-bold text-white">{{ prospect.firstName }} {{ prospect.lastName }}</p>
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
          class="mt-1 inline-block text-sm break-words text-[#c7a8f2] transition-colors hover:text-white"
          :target="item.external ? '_blank' : undefined"
          :rel="item.external ? 'noreferrer' : undefined"
        >
          {{ item.value }}
        </a>
        <p v-else :class="['mt-1 text-sm break-words text-white', item.multiline ? 'whitespace-pre-line' : '']">
          {{ item.value || '-' }}
        </p>
      </div>
    </section>

    <ProspectCommercialTracking :prospect="prospect" />

    <ProspectEditModal v-model="editOpen" :prospect="prospect" />
  </div>
</template>

<script lang="ts" setup>
import type { Ref } from 'vue'
import type { LinkedinProspectFull } from '#src-core/types/response/linkedin.types'

/**
 *
 */
type ProspectDetailInfoProps = {
  prospect: LinkedinProspectFull
}

const editOpen: Ref<boolean> = ref(false)

/**
 *
 */
type DetailItem = {
  label: string
  value: string | number | null
  href?: string
  external?: boolean
  multiline?: boolean
  wide?: boolean
}

const props: ProspectDetailInfoProps = defineProps<ProspectDetailInfoProps>()

/**
 * Formate un booleen optionnel pour la fiche.
 * @param {boolean | null} value - Valeur booleenne optionnelle.
 * @returns {string | null} Libelle lisible.
 */
const formatBoolean: (value: boolean | null) => string | null = (value: boolean | null): string | null => {
  if (value === null) {
    return null
  }
  return value ? 'Oui' : 'Non'
}

const items: ComputedRef<DetailItem[]> = computed((): DetailItem[] => [
  {
    label: 'Email',
    value: props.prospect.email,
    href: props.prospect.email ? `mailto:${props.prospect.email}` : undefined,
  },
  {
    label: 'Telephone',
    value: props.prospect.phone,
    href: props.prospect.phone ? `tel:${props.prospect.phone}` : undefined,
  },
  { label: 'Poste', value: props.prospect.position },
  { label: 'Entreprise', value: props.prospect.company },
  { label: 'Secteur', value: props.prospect.industry },
  { label: 'Ville', value: props.prospect.city },
  { label: 'Region', value: props.prospect.region },
  { label: 'Pays', value: props.prospect.country },
  {
    label: 'URL LinkedIn',
    value: props.prospect.linkedinUrl,
    href: props.prospect.linkedinUrl ?? undefined,
    external: true,
  },
  {
    label: 'URL LinkedIn entreprise',
    value: props.prospect.companyLinkedinUrl,
    href: props.prospect.companyLinkedinUrl ?? undefined,
    external: true,
  },
  {
    label: 'URL Site web',
    value: props.prospect.websiteUrl,
    href: props.prospect.websiteUrl ?? undefined,
    external: true,
  },
  { label: 'Headline LinkedIn', value: props.prospect.profileHeadline, wide: true },
  { label: 'Open to work', value: formatBoolean(props.prospect.openToWork) },
  { label: 'Hiring', value: formatBoolean(props.prospect.hiring) },
  { label: 'Relations du prospect sur LinkedIn (contacts directs)', value: props.prospect.connectionsCount },
  { label: 'Abonnes du profil LinkedIn (personnes qui le suivent)', value: props.prospect.followerCount },
  { label: 'Taille declaree entreprise', value: props.prospect.companyEmployeeCountRange },
  { label: 'Type entreprise', value: props.prospect.companyType },
  { label: 'Tagline entreprise', value: props.prospect.companyTagline, wide: true },
  { label: 'Description entreprise', value: props.prospect.companyDescription, multiline: true, wide: true },
])
</script>
