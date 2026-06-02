<template>
  <UModal v-model:open="isOpen" :ui="modalUi">
    <template #content>
      <div class="bg-[radial-gradient(circle_at_top_right,rgba(154,101,213,0.18),transparent_34%),#071022] p-6">
        <div class="mb-5 flex items-center justify-between">
          <div>
            <p class="text-xs font-semibold tracking-[0.2em] text-[#9a65d5] uppercase">LINKEDIN</p>
            <h3 class="mt-1 text-xl font-semibold text-white">Modifier le prospect</h3>
          </div>
          <UButton
            icon="i-heroicons-x-mark"
            size="sm"
            color="neutral"
            variant="ghost"
            class="text-[#9ba3bd] hover:bg-[#111c3f] hover:text-white"
            @click="isOpen = false"
          />
        </div>

        <form class="flex flex-col gap-4" @submit.prevent="handleSubmit">
          <div class="grid gap-3 md:grid-cols-2">
            <UFormField label="Prenom *" :ui="fieldUi">
              <UInput v-model="form.firstName" required variant="none" :ui="inputUi" />
            </UFormField>
            <UFormField label="Nom *" :ui="fieldUi">
              <UInput v-model="form.lastName" required variant="none" :ui="inputUi" />
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
            <UFormField label="URL LinkedIn" :ui="fieldUi">
              <UInput v-model="form.linkedinUrl" variant="none" :ui="inputUi" />
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

          <details class="rounded-lg border border-[#2f3d67] bg-[#0b1433]/70 p-4">
            <summary class="cursor-pointer text-sm font-semibold text-[#dfe5ff]">
              Donnees enrichies LinkedIn / entreprise
            </summary>
            <div class="mt-4 grid gap-3 md:grid-cols-2">
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
          </details>

          <p v-if="errorMessage" class="text-xs text-red-400">{{ errorMessage }}</p>

          <div class="mt-2 flex justify-end gap-3 border-t border-[#2f3d67] pt-5">
            <UButton
              variant="ghost"
              label="Annuler"
              class="rounded-md px-4 py-2 font-semibold text-[#c7d0ea] hover:bg-[#111c3f] hover:text-white"
              @click="isOpen = false"
            />
            <UButton
              type="submit"
              label="Enregistrer"
              :loading="submitting"
              class="rounded-md bg-[linear-gradient(135deg,#102766_0%,#7446a6_100%)] px-5 py-2 font-semibold text-white shadow-[0_14px_30px_rgba(5,9,23,0.35)] transition hover:bg-[linear-gradient(135deg,#17337c_0%,#9a65d5_100%)] disabled:brightness-[0.72]"
            />
          </div>
        </form>
      </div>
    </template>
  </UModal>
</template>

<script lang="ts" setup>
import type { Ref } from 'vue'
import type { LinkedinProspectFull } from '#src-core/types/response/linkedin.types'
import type { UpdateLinkedinProspectPayload } from '#src-core/types/payload/linkedin.types'
import { useLinkedinProspectsStore } from '#src-nuxt/app/stores/linkedinProspects.store'

/**
 *
 */
type ProspectEditModalProps = {
  prospect: LinkedinProspectFull
}

/**
 *
 */
type EditForm = {
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

const props: ProspectEditModalProps = defineProps<ProspectEditModalProps>()
const isOpen: Ref<boolean> = defineModel<boolean>({ default: false })
const store: ReturnType<typeof useLinkedinProspectsStore> = useLinkedinProspectsStore()
const toast: ReturnType<typeof useToast> = useToast()
const submitting: Ref<boolean> = ref(false)
const errorMessage: Ref<string> = ref('')

/**
 * Configuration UI de la modale.
 */
type ModalUiConfig = { overlay: string; content: string; close: string }
const modalUi: ModalUiConfig = {
  overlay: 'bg-[#020617]/80 backdrop-blur-sm',
  content:
    'max-h-[calc(100vh-2rem)] w-[calc(100vw-2rem)] max-w-2xl overflow-y-auto rounded-lg border border-[#2f3d67] bg-[#071022] text-white shadow-[0_24px_80px_rgba(0,0,0,0.45)] ring-0 divide-y-0',
  close: 'text-[#9ba3bd] hover:text-white hover:bg-[#111c3f]',
} as const

/**
 * Configuration UI des champs.
 */
type FieldUiConfig = { label: string; container: string }
const fieldUi: FieldUiConfig = {
  label: 'text-[#c7d0ea] font-medium',
  container: 'mt-1.5',
} as const

/**
 * Configuration UI des inputs.
 */
type InputUiConfig = { base: string }
const inputUi: InputUiConfig = {
  base: 'h-11 rounded-md border border-[#2f3d67] bg-[rgba(5,9,23,0.86)] px-3 text-[#f7f8ff] placeholder:text-[#626d90] shadow-[0_10px_24px_rgba(0,0,0,0.18)] outline-none transition hover:border-[#485780] focus:border-[#9a65d5] focus:shadow-[0_0_0_1px_rgba(154,101,213,0.28),0_10px_24px_rgba(0,0,0,0.18)]',
} as const

const textareaClass: string =
  'min-h-24 w-full resize-y rounded-md border border-[#2f3d67] bg-[rgba(5,9,23,0.86)] px-3 py-2 text-sm text-[#f7f8ff] shadow-[0_10px_24px_rgba(0,0,0,0.18)] outline-none transition hover:border-[#485780] focus:border-[#9a65d5] focus:shadow-[0_0_0_1px_rgba(154,101,213,0.28),0_10px_24px_rgba(0,0,0,0.18)]'
const selectClass: string =
  'h-11 w-full rounded-md border border-[#2f3d67] bg-[rgba(5,9,23,0.86)] px-3 text-sm text-[#f7f8ff] shadow-[0_10px_24px_rgba(0,0,0,0.18)] outline-none transition hover:border-[#485780] focus:border-[#9a65d5]'

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
 * Construit le formulaire a partir du prospect courant.
 * @returns {EditForm} Valeurs initiales du formulaire.
 */
const buildForm: () => EditForm = (): EditForm => ({
  firstName: props.prospect.firstName,
  lastName: props.prospect.lastName,
  position: props.prospect.position ?? '',
  company: props.prospect.company ?? '',
  industry: props.prospect.industry ?? '',
  city: props.prospect.city ?? '',
  region: props.prospect.region ?? '',
  country: props.prospect.country ?? '',
  profileHeadline: props.prospect.profileHeadline ?? '',
  openToWork: props.prospect.openToWork,
  hiring: props.prospect.hiring,
  connectionsCount: props.prospect.connectionsCount != null ? String(props.prospect.connectionsCount) : '',
  followerCount: props.prospect.followerCount != null ? String(props.prospect.followerCount) : '',
  linkedinUrl: props.prospect.linkedinUrl ?? '',
  companyLinkedinUrl: props.prospect.companyLinkedinUrl ?? '',
  websiteUrl: props.prospect.websiteUrl ?? '',
  email: props.prospect.email ?? '',
  phone: props.prospect.phone ?? '',
  companyEmployeeCountRange: props.prospect.companyEmployeeCountRange ?? '',
  companyType: props.prospect.companyType ?? '',
  companyTagline: props.prospect.companyTagline ?? '',
  companyDescription: props.prospect.companyDescription ?? '',
})

const form: Ref<EditForm> = ref(buildForm()) as unknown as Ref<EditForm>

watch(isOpen, (open: boolean): void => {
  if (open) {
    form.value = buildForm()
    errorMessage.value = ''
  }
})

/**
 * Soumet le formulaire de modification du prospect.
 * @returns {Promise<void>} Promesse resolue apres la soumission.
 */
const handleSubmit: () => Promise<void> = async (): Promise<void> => {
  errorMessage.value = ''
  submitting.value = true
  try {
    const payload: UpdateLinkedinProspectPayload = {
      firstName: form.value.firstName,
      lastName: form.value.lastName,
      position: form.value.position || undefined,
      company: form.value.company || undefined,
      industry: form.value.industry || undefined,
      city: form.value.city || undefined,
      region: form.value.region || undefined,
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
    await store.update(props.prospect.id, payload)
    await store.fetchOne(props.prospect.id)
    toast.add({ title: 'Prospect mis à jour', color: 'success', duration: 3000 })
    isOpen.value = false
  } catch (error: unknown) {
    errorMessage.value = (error as { message?: string }).message ?? 'Une erreur est survenue.'
  } finally {
    submitting.value = false
  }
}
</script>
