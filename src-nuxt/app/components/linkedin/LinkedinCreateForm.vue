<template>
  <form class="flex flex-col gap-4" @submit.prevent="handleSubmit">
    <div class="grid gap-3 md:grid-cols-2">
      <UFormField label="URL LinkedIn" :ui="fieldUi" class="md:col-span-2">
        <div class="flex flex-col gap-2 sm:flex-row">
          <UInput v-model="form.linkedinUrl" variant="none" :ui="inputUi" class="min-w-0 flex-1" />
          <UButton
            type="button"
            label="Remplir auto"
            :loading="enriching"
            :disabled="!form.linkedinUrl || submitting"
            class="rounded-md border border-[#3f4f7d] bg-[#111c3f] px-4 py-2 font-semibold text-[#dfe5ff] transition hover:bg-[#182755] disabled:brightness-[0.72]"
            @click="handleEnrich"
          />
        </div>
      </UFormField>
      <UFormField label="Prenom *" :ui="fieldUi">
        <UInput v-model="form.firstName" variant="none" :ui="inputUi" />
      </UFormField>
      <UFormField label="Nom *" :ui="fieldUi">
        <UInput v-model="form.lastName" variant="none" :ui="inputUi" />
      </UFormField>
      <UFormField label="Poste" :ui="fieldUi">
        <UInput v-model="form.position" variant="none" :ui="inputUi" />
      </UFormField>
      <UFormField label="Entreprise" :ui="fieldUi">
        <UInput v-model="form.company" variant="none" :ui="inputUi" />
      </UFormField>
      <UFormField label="Secteur" :ui="fieldUi">
        <UInput v-model="form.industry" variant="none" :ui="inputUi" />
      </UFormField>
      <UFormField label="Ville" :ui="fieldUi">
        <UInput v-model="form.city" variant="none" :ui="inputUi" />
      </UFormField>
      <UFormField label="Region" :ui="fieldUi">
        <UInput v-model="form.region" variant="none" :ui="inputUi" />
      </UFormField>
      <UFormField label="Pays" :ui="fieldUi">
        <UInput v-model="form.country" variant="none" :ui="inputUi" />
      </UFormField>
      <UFormField label="URL Site web" :ui="fieldUi">
        <UInput v-model="form.websiteUrl" variant="none" :ui="inputUi" />
      </UFormField>
      <UFormField label="Email" :ui="fieldUi">
        <UInput v-model="form.email" type="email" variant="none" :ui="inputUi" />
      </UFormField>
      <UFormField label="Telephone" :ui="fieldUi">
        <UInput v-model="form.phone" type="tel" variant="none" :ui="inputUi" />
      </UFormField>
    </div>

    <div class="grid gap-3 border-t border-[#2f3d67] pt-4 md:grid-cols-2">
      <p class="text-xs font-semibold tracking-[0.16em] text-[#9a65d5] uppercase md:col-span-2">
        Donnees enrichies LinkedIn / entreprise
      </p>
      <UFormField label="Headline LinkedIn" :ui="fieldUi" class="md:col-span-2">
        <UInput v-model="form.profileHeadline" variant="none" :ui="inputUi" />
      </UFormField>
      <UFormField label="URL LinkedIn entreprise" :ui="fieldUi" class="md:col-span-2">
        <UInput v-model="form.companyLinkedinUrl" variant="none" :ui="inputUi" />
      </UFormField>
      <UFormField label="Taille declaree entreprise" :ui="fieldUi">
        <UInput v-model="form.companyEmployeeCountRange" variant="none" :ui="inputUi" />
      </UFormField>
      <UFormField label="Type entreprise" :ui="fieldUi">
        <UInput v-model="form.companyType" variant="none" :ui="inputUi" />
      </UFormField>
      <UFormField label="Tagline entreprise" :ui="fieldUi">
        <UInput v-model="form.companyTagline" variant="none" :ui="inputUi" />
      </UFormField>
      <UFormField label="Description entreprise" :ui="fieldUi" class="md:col-span-2">
        <textarea v-model="form.companyDescription" rows="4" :class="textareaClass" />
      </UFormField>
      <UFormField label="Relations du prospect sur LinkedIn (contacts directs)" :ui="fieldUi">
        <UInput v-model="form.connectionsCount" type="number" min="0" variant="none" :ui="inputUi" />
      </UFormField>
      <UFormField label="Abonnes du profil LinkedIn (personnes qui le suivent)" :ui="fieldUi">
        <UInput v-model="form.followerCount" type="number" min="0" variant="none" :ui="inputUi" />
      </UFormField>
      <UFormField label="Open to work" :ui="fieldUi">
        <select v-model="form.openToWork" :class="selectClass">
          <option :value="null">Inconnu</option>
          <option :value="true">Oui</option>
          <option :value="false">Non</option>
        </select>
      </UFormField>
      <UFormField label="Hiring" :ui="fieldUi">
        <select v-model="form.hiring" :class="selectClass">
          <option :value="null">Inconnu</option>
          <option :value="true">Oui</option>
          <option :value="false">Non</option>
        </select>
      </UFormField>
    </div>

    <p v-if="errorMessage" class="text-xs text-red-400">{{ errorMessage }}</p>
    <div class="mt-2 flex justify-end gap-3 border-t border-[#2f3d67] pt-5">
      <UButton
        variant="ghost"
        label="Annuler"
        class="rounded-md px-4 py-2 font-semibold text-[#c7d0ea] hover:bg-[#111c3f] hover:text-white"
        @click="emit('cancel')"
      />
      <UButton
        type="submit"
        label="Creer"
        :loading="submitting"
        class="rounded-md bg-[linear-gradient(135deg,#102766_0%,#7446a6_100%)] px-5 py-2 font-semibold text-white shadow-[0_14px_30px_rgba(5,9,23,0.35)] transition hover:bg-[linear-gradient(135deg,#17337c_0%,#9a65d5_100%)] disabled:brightness-[0.72]"
      />
    </div>
  </form>
</template>

<script lang="ts" setup>
import type { Ref } from 'vue'
import type { CreateLinkedinProspectPayload } from '#src-core/types/payload/linkedin.types'
import { useLinkedinProspectsStore } from '#src-nuxt/app/stores/linkedinProspects.store'

/**
 * Evenements emis par le formulaire.
 */
type LinkedinCreateFormEmits = {
  created: []
  cancel: []
}

/**
 * Signature typee de l'emetteur.
 */
type LinkedinCreateFormEmit = ((event: 'created') => void) & ((event: 'cancel') => void)

/**
 * Etat du formulaire.
 */
type CreateForm = {
  firstName: string
  lastName: string
  position: string
  company: string
  industry: string
  city: string
  region: string
  country: string
  profileHeadline: string
  openToWork: boolean | null
  hiring: boolean | null
  connectionsCount: string
  followerCount: string
  linkedinUrl: string
  companyLinkedinUrl: string
  websiteUrl: string
  email: string
  phone: string
  companyEmployeeCountRange: string
  companyType: string
  companyTagline: string
  companyDescription: string
}

/**
 * Champs texte/nombre stockes comme chaines dans le formulaire.
 */
type CreateTextField = Exclude<keyof CreateForm, 'openToWork' | 'hiring'>

const emit: LinkedinCreateFormEmit = defineEmits<LinkedinCreateFormEmits>()
const prospectsStore: ReturnType<typeof useLinkedinProspectsStore> = useLinkedinProspectsStore()
const submitting: Ref<boolean> = ref(false)
const enriching: Ref<boolean> = ref(false)
const errorMessage: Ref<string> = ref('')
/** Configuration UI du champ de formulaire. */
type FieldUiConfig = { label: string; container: string }
const fieldUi: FieldUiConfig = {
  label: 'text-[#c7d0ea] font-medium',
  container: 'mt-1.5',
} as const
/** Configuration UI de l'input de formulaire. */
type InputUiConfig = { base: string }
const inputUi: InputUiConfig = {
  base: 'h-11 rounded-md border border-[#2f3d67] bg-[rgba(5,9,23,0.86)] px-3 text-[#f7f8ff] placeholder:text-[#626d90] shadow-[0_10px_24px_rgba(0,0,0,0.18)] outline-none transition hover:border-[#485780] focus:border-[#9a65d5] focus:shadow-[0_0_0_1px_rgba(154,101,213,0.28),0_10px_24px_rgba(0,0,0,0.18)]',
} as const

const textareaClass: string =
  'min-h-24 w-full resize-y rounded-md border border-[#2f3d67] bg-[rgba(5,9,23,0.86)] px-3 py-2 text-sm text-[#f7f8ff] shadow-[0_10px_24px_rgba(0,0,0,0.18)] outline-none transition hover:border-[#485780] focus:border-[#9a65d5] focus:shadow-[0_0_0_1px_rgba(154,101,213,0.28),0_10px_24px_rgba(0,0,0,0.18)]'
const selectClass: string =
  'h-11 w-full rounded-md border border-[#2f3d67] bg-[rgba(5,9,23,0.86)] px-3 text-sm text-[#f7f8ff] shadow-[0_10px_24px_rgba(0,0,0,0.18)] outline-none transition hover:border-[#485780] focus:border-[#9a65d5]'

const textFormFields: CreateTextField[] = [
  'firstName',
  'lastName',
  'position',
  'company',
  'industry',
  'city',
  'region',
  'country',
  'profileHeadline',
  'connectionsCount',
  'followerCount',
  'linkedinUrl',
  'companyLinkedinUrl',
  'websiteUrl',
  'email',
  'phone',
  'companyEmployeeCountRange',
  'companyType',
  'companyTagline',
  'companyDescription',
]

const form: Ref<CreateForm> = ref({
  firstName: '',
  lastName: '',
  position: '',
  company: '',
  industry: '',
  city: '',
  region: '',
  country: '',
  profileHeadline: '',
  openToWork: null,
  hiring: null,
  connectionsCount: '',
  followerCount: '',
  linkedinUrl: '',
  companyLinkedinUrl: '',
  websiteUrl: '',
  email: '',
  phone: '',
  companyEmployeeCountRange: '',
  companyType: '',
  companyTagline: '',
  companyDescription: '',
})

/**
 * Retourne une chaine trimmee ou undefined pour ne pas envoyer de champs vides.
 * @param {string} value - Valeur saisie.
 * @returns {string | undefined} Valeur optionnelle.
 */
const optionalString: (value: string) => string | undefined = (value: string): string | undefined => {
  const trimmed: string = value.trim()
  return trimmed || undefined
}

/**
 * Retourne un nombre valide ou undefined.
 * @param {string} value - Valeur numerique saisie.
 * @returns {number | undefined} Nombre optionnel.
 */
const optionalNumber: (value: string) => number | undefined = (value: string): number | undefined => {
  const trimmed: string = value.trim()
  if (!trimmed) {
    return undefined
  }
  const numberValue: number = Number(trimmed)
  return Number.isFinite(numberValue) ? numberValue : undefined
}

/**
 * Applique les champs retournes par l'enrichissement sans effacer les corrections manuelles.
 * @param {Partial<CreateLinkedinProspectPayload>} enrichment - Donnees detectees.
 * @returns {void}
 */
const applyEnrichment: (enrichment: Partial<CreateLinkedinProspectPayload>) => void = (
  enrichment: Partial<CreateLinkedinProspectPayload>,
): void => {
  for (const key of textFormFields) {
    const value: CreateLinkedinProspectPayload[CreateTextField] | undefined = enrichment[key]
    if ((typeof value === 'string' || typeof value === 'number') && String(value).trim() && !form.value[key]) {
      form.value[key] = String(value).trim()
    }
  }
  if (typeof enrichment.openToWork === 'boolean') {
    form.value.openToWork = enrichment.openToWork
  }
  if (typeof enrichment.hiring === 'boolean') {
    form.value.hiring = enrichment.hiring
  }
}

/**
 * Lance l'enrichissement n8n depuis l'URL LinkedIn saisie.
 * @returns {Promise<void>}
 */
const handleEnrich: () => Promise<void> = async (): Promise<void> => {
  errorMessage.value = ''
  if (!form.value.linkedinUrl) {
    errorMessage.value = "Ajoute d'abord une URL LinkedIn."
    return
  }
  enriching.value = true
  try {
    const enrichment: Partial<CreateLinkedinProspectPayload> = await prospectsStore.enrich(form.value.linkedinUrl)
    applyEnrichment(enrichment)
  } catch (error: unknown) {
    errorMessage.value = (error as { message?: string }).message ?? "Impossible d'enrichir ce profil LinkedIn."
  } finally {
    enriching.value = false
  }
}

/**
 * Soumet le formulaire.
 * @returns {Promise<void>}
 */
const handleSubmit: () => Promise<void> = async (): Promise<void> => {
  errorMessage.value = ''
  submitting.value = true
  try {
    if ((!form.value.firstName || !form.value.lastName) && form.value.linkedinUrl) {
      await handleEnrich()
    }
    if (!form.value.firstName || !form.value.lastName) {
      errorMessage.value = 'Le prenom et le nom sont obligatoires avant de creer le prospect.'
      return
    }
    const payload: CreateLinkedinProspectPayload = {
      firstName: form.value.firstName.trim(),
      lastName: form.value.lastName.trim(),
      position: optionalString(form.value.position),
      company: optionalString(form.value.company),
      industry: optionalString(form.value.industry),
      city: optionalString(form.value.city),
      region: optionalString(form.value.region),
      country: optionalString(form.value.country),
      profileHeadline: optionalString(form.value.profileHeadline),
      openToWork: form.value.openToWork ?? undefined,
      hiring: form.value.hiring ?? undefined,
      connectionsCount: optionalNumber(form.value.connectionsCount),
      followerCount: optionalNumber(form.value.followerCount),
      linkedinUrl: optionalString(form.value.linkedinUrl),
      companyLinkedinUrl: optionalString(form.value.companyLinkedinUrl),
      websiteUrl: optionalString(form.value.websiteUrl),
      email: optionalString(form.value.email),
      phone: optionalString(form.value.phone),
      companyEmployeeCountRange: optionalString(form.value.companyEmployeeCountRange),
      companyType: optionalString(form.value.companyType),
      companyTagline: optionalString(form.value.companyTagline),
      companyDescription: optionalString(form.value.companyDescription),
    }
    await prospectsStore.create(payload)
    emit('created')
  } catch (error: unknown) {
    errorMessage.value = (error as { message?: string }).message ?? 'Une erreur est survenue.'
  } finally {
    submitting.value = false
  }
}
</script>
