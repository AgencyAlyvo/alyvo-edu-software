<template>
  <section class="grid gap-4 rounded-lg border border-[#2f3d67] bg-[#0b1433]/70 p-5 md:grid-cols-2">
    <UFormField label="Invitations max / semaine" :ui="fieldUi">
      <UInput v-model.number="form.maxInvitesPerWeek" type="number" min="0" variant="none" :ui="inputUi" class="w-28" />
    </UFormField>
    <UFormField label="Delai relance 1" :ui="fieldUi">
      <div class="flex items-center gap-2">
        <UInput
          v-model.number="form.relance1DelayDays"
          type="number"
          min="0"
          variant="none"
          :ui="inputUi"
          class="w-20"
        />
        <span class="text-sm font-medium text-[#9ba3bd]">jours</span>
      </div>
    </UFormField>
    <UFormField label="Delai relance 2" :ui="fieldUi">
      <div class="flex items-center gap-2">
        <UInput
          v-model.number="form.relance2DelayDays"
          type="number"
          min="0"
          variant="none"
          :ui="inputUi"
          class="w-20"
        />
        <span class="text-sm font-medium text-[#9ba3bd]">jours</span>
      </div>
    </UFormField>
    <UFormField label="Delai relance 3" :ui="fieldUi">
      <div class="flex items-center gap-2">
        <UInput
          v-model.number="form.relance3DelayDays"
          type="number"
          min="0"
          variant="none"
          :ui="inputUi"
          class="w-20"
        />
        <span class="text-sm font-medium text-[#9ba3bd]">jours</span>
      </div>
    </UFormField>
    <div class="md:col-span-2">
      <UButton
        label="Enregistrer"
        :loading="loading"
        class="rounded-md bg-[linear-gradient(135deg,#102766_0%,#7446a6_100%)] px-5 py-2 font-semibold text-white shadow-[0_14px_30px_rgba(5,9,23,0.35)] transition hover:bg-[linear-gradient(135deg,#17337c_0%,#9a65d5_100%)] disabled:brightness-[0.72]"
        @click="save"
      />
    </div>
  </section>
</template>

<script lang="ts" setup>
import type { Ref } from 'vue'
import { useUserSettingsStore } from '#src-nuxt/app/stores/userSettings.store'
import type { UpdateUserSettingsPayload } from '#src-core/types/payload/settings.types'

const store: ReturnType<typeof useUserSettingsStore> = useUserSettingsStore()
const toast: ReturnType<typeof useToast> = useToast()
const loading: Ref<boolean> = ref(false)
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
const form: Ref<UpdateUserSettingsPayload> = ref({})

watchEffect((): void => {
  form.value = {
    maxInvitesPerWeek: store.settings?.maxInvitesPerWeek ?? 100,
    relance1DelayDays: store.settings?.relance1DelayDays ?? 3,
    relance2DelayDays: store.settings?.relance2DelayDays ?? 7,
    relance3DelayDays: store.settings?.relance3DelayDays ?? 15,
  }
})

/**
 * Sauvegarde les parametres LinkedIn.
 * @returns {Promise<void>}
 */
const save: () => Promise<void> = async (): Promise<void> => {
  loading.value = true
  try {
    await store.update(form.value)
    toast.add({
      title: 'Paramètres enregistrés',
      color: 'success',
      duration: 3000,
    })
  } catch {
    toast.add({
      title: 'Erreur',
      description: 'Impossible de sauvegarder les paramètres.',
      color: 'error',
      duration: 4000,
    })
  } finally {
    loading.value = false
  }
}
</script>
