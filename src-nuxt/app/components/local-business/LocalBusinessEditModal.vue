<template>
  <UModal v-model:open="isOpen" :ui="modalUi">
    <template #content>
      <div class="bg-[radial-gradient(circle_at_top_right,rgba(154,101,213,0.18),transparent_34%),#071022] p-6">
        <div class="mb-5 flex items-center justify-between">
          <div>
            <p class="text-xs font-semibold tracking-[0.2em] text-[#9a65d5] uppercase">BUSINESS LOCAL</p>
            <h3 class="mt-1 text-xl font-semibold text-white">Modifier le business</h3>
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
            <UFormField label="Nom entreprise *" :ui="fieldUi" class="md:col-span-2">
              <UInput v-model="form.name" required variant="none" :ui="inputUi" />
            </UFormField>
            <UFormField label="Type de commerce (OSM)" :ui="fieldUi" class="md:col-span-2">
              <USelect v-model="form.osmType" :items="osmTypeItems" variant="none" :ui="selectUi" />
            </UFormField>
            <UFormField label="Adresse" :ui="fieldUi" class="md:col-span-2">
              <UInput v-model="form.address" variant="none" :ui="inputUi" />
            </UFormField>
            <UFormField label="Code postal" :ui="fieldUi">
              <UInput v-model="form.postalCode" variant="none" :ui="inputUi" />
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
            <UFormField label="Email" :ui="fieldUi">
              <UInput v-model="form.email" type="email" variant="none" :ui="inputUi" />
            </UFormField>
            <UFormField label="Telephone" :ui="fieldUi">
              <UInput v-model="form.phone" type="tel" variant="none" :ui="inputUi" />
            </UFormField>
            <UFormField label="URL Site web" :ui="fieldUi">
              <UInput v-model="form.website" variant="none" :ui="inputUi" />
            </UFormField>
            <UFormField label="URL Pages Jaunes" :ui="fieldUi">
              <UInput v-model="form.pagesJaunesUrl" variant="none" :ui="inputUi" />
            </UFormField>
            <UFormField label="Horaires" :ui="fieldUi" class="md:col-span-2">
              <textarea
                v-model="form.openingHours"
                rows="3"
                :class="textareaClass"
                placeholder="Format OSM opening_hours ou texte libre"
              />
            </UFormField>
          </div>

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
import {
  buildLocalBusinessOsmTypeFilterItems,
  getLocalBusinessOsmTagFamily,
} from '#src-core/constants/localBusinessOsmTypeLabels'
import type { UpdateLocalBusinessProspectPayload } from '#src-core/types/payload/local-business.types'
import type { LocalBusinessProspectFull } from '#src-core/types/response/local-business.types'
import { useAlyvoEditModalUi } from '#src-nuxt/app/composables/useAlyvoEditModalUi'
import { useLocalBusinessProspectsStore } from '#src-nuxt/app/stores/localBusinessProspects.store'

/**
 * Props de la modale d'edition.
 */
type LocalBusinessEditModalProps = {
  prospect: LocalBusinessProspectFull
}

/**
 * Item de select.
 */
type OsmTypeItem = {
  label: string
  value: string
}

/**
 * Champs du formulaire d'edition.
 */
type EditForm = {
  name: string
  osmType: string
  address: string
  postalCode: string
  city: string
  region: string
  country: string
  email: string
  phone: string
  website: string
  pagesJaunesUrl: string
  openingHours: string
}

const NONE_OSM_TYPE: string = '__none__'

const props: LocalBusinessEditModalProps = defineProps<LocalBusinessEditModalProps>()
const isOpen: Ref<boolean> = defineModel<boolean>({ default: false })
const store: ReturnType<typeof useLocalBusinessProspectsStore> = useLocalBusinessProspectsStore()
const toast: ReturnType<typeof useToast> = useToast()
const { modalUi, fieldUi, inputUi, selectUi, textareaClass } = useAlyvoEditModalUi()
const submitting: Ref<boolean> = ref(false)
const errorMessage: Ref<string> = ref('')

const osmTypeItems: OsmTypeItem[] = [
  { label: 'Non defini', value: NONE_OSM_TYPE },
  ...buildLocalBusinessOsmTypeFilterItems(),
]

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
 * Construit le formulaire a partir du prospect courant.
 * @returns {EditForm} Valeurs initiales du formulaire.
 */
const buildForm: () => EditForm = (): EditForm => ({
  name: props.prospect.name,
  osmType: props.prospect.subcategory ?? NONE_OSM_TYPE,
  address: props.prospect.address ?? '',
  postalCode: props.prospect.postalCode ?? '',
  city: props.prospect.city ?? '',
  region: props.prospect.region ?? '',
  country: props.prospect.country ?? 'France',
  email: props.prospect.email ?? '',
  phone: props.prospect.phone ?? '',
  website: props.prospect.website ?? '',
  pagesJaunesUrl: props.prospect.pagesJaunesUrl ?? '',
  openingHours: props.prospect.openingHours ?? '',
})

const form: Ref<EditForm> = ref(buildForm())

watch(
  () => props.prospect,
  (): void => {
    form.value = buildForm()
  },
)

/**
 * Soumet le formulaire de modification du business.
 * @returns {Promise<void>}
 */
const handleSubmit: () => Promise<void> = async (): Promise<void> => {
  errorMessage.value = ''
  submitting.value = true
  try {
    const osmType: string | null =
      !form.value.osmType || form.value.osmType === NONE_OSM_TYPE ? null : form.value.osmType
    const tagFamily: string | null = osmType ? getLocalBusinessOsmTagFamily(osmType) : null

    const payload: UpdateLocalBusinessProspectPayload = {
      name: form.value.name.trim(),
      subcategory: osmType,
      category: tagFamily ?? props.prospect.category,
      address: optionalString(form.value.address) ?? null,
      postalCode: optionalString(form.value.postalCode) ?? null,
      city: optionalString(form.value.city) ?? null,
      region: optionalString(form.value.region) ?? null,
      country: optionalString(form.value.country) ?? null,
      email: optionalString(form.value.email) ?? null,
      phone: optionalString(form.value.phone) ?? null,
      website: optionalString(form.value.website) ?? null,
      pagesJaunesUrl: optionalString(form.value.pagesJaunesUrl) ?? null,
      openingHours: optionalString(form.value.openingHours) ?? null,
    }
    await store.update(props.prospect.id, payload, { refreshCurrent: true })
    toast.add({ title: 'Business mis a jour', color: 'success', duration: 3000 })
    isOpen.value = false
  } catch (error: unknown) {
    errorMessage.value = (error as { message?: string }).message ?? 'Une erreur est survenue.'
  } finally {
    submitting.value = false
  }
}
</script>
