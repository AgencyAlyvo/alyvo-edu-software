<template>
  <main
    class="mx-auto h-screen max-w-xl bg-[radial-gradient(circle_at_50%_8%,rgba(116,70,166,0.24),transparent_34%),linear-gradient(180deg,#0b1433_0%,#050917_100%)] text-white"
  >
    <WindowBar />

    <section class="flex flex-col items-stretch">
      <!-- Logo Alyvo centré en haut de la section. -->
      <div class="flex justify-center">
        <img
          class="w-[180px] drop-shadow-[0_18px_28px_rgba(0,0,0,0.24)] select-none"
          src="/logo-alyvo.png"
          alt="Alyvo"
          draggable="false"
        />
      </div>

      <form class="flex flex-col gap-6 px-5 py-0" @submit.prevent="signUp">
        <!-- Champ email. -->
        <div class="relative flex flex-col gap-2">
          <input
            v-model="credentials.email"
            class="relative flex h-12 w-full items-center justify-center rounded-md border-2 border-[#2f3d67] bg-[rgba(5,9,23,0.86)] pl-3 text-[#f7f8ff] shadow-[0_12px_30px_rgba(0,0,0,0.24)] outline-none placeholder:text-[#626d90] hover:border-[#485780] focus:border-[#9a65d5] focus:shadow-[0_0_0_1px_rgba(154,101,213,0.28),0_12px_30px_rgba(0,0,0,0.24)]"
            type="email"
            id="email"
            placeholder="email@alyvo.fr"
            autocomplete="email"
          />
        </div>

        <!-- Champ mot de passe avec bouton afficher/masquer. -->
        <div class="relative flex flex-col gap-2">
          <input
            v-model="credentials.password"
            class="relative flex h-12 w-full items-center justify-center rounded-md border-2 border-[#2f3d67] bg-[rgba(5,9,23,0.86)] pr-12 pl-3 text-[#f7f8ff] shadow-[0_12px_30px_rgba(0,0,0,0.24)] outline-none placeholder:text-[#626d90] hover:border-[#485780] focus:border-[#9a65d5] focus:shadow-[0_0_0_1px_rgba(154,101,213,0.28),0_12px_30px_rgba(0,0,0,0.24)]"
            :type="showPassword ? 'text' : 'password'"
            id="password"
            placeholder="Mot de passe"
            autocomplete="new-password"
          />

          <button
            class="absolute top-3 right-4 cursor-pointer text-[#9ba3bd] hover:text-white"
            type="button"
            :aria-label="showPassword ? 'Masquer le mot de passe' : 'Afficher le mot de passe'"
            @click="showPassword = !showPassword"
          >
            <svg
              v-if="!showPassword"
              width="24"
              height="24"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="2"
              stroke-linecap="round"
              stroke-linejoin="round"
            >
              <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" />
              <circle cx="12" cy="12" r="3" />
            </svg>
            <svg
              v-else
              width="24"
              height="24"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="2"
              stroke-linecap="round"
              stroke-linejoin="round"
            >
              <path
                d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"
              />
              <line x1="1" y1="1" x2="23" y2="23" />
            </svg>
          </button>
        </div>

        <!-- Champ confirmation du mot de passe avec bouton afficher/masquer. -->
        <div class="relative flex flex-col gap-2">
          <input
            v-model="credentials.passwordConfirmation"
            class="relative flex h-12 w-full items-center justify-center rounded-md border-2 border-[#2f3d67] bg-[rgba(5,9,23,0.86)] pr-12 pl-3 text-[#f7f8ff] shadow-[0_12px_30px_rgba(0,0,0,0.24)] outline-none placeholder:text-[#626d90] hover:border-[#485780] focus:border-[#9a65d5] focus:shadow-[0_0_0_1px_rgba(154,101,213,0.28),0_12px_30px_rgba(0,0,0,0.24)]"
            :type="showPasswordConfirmation ? 'text' : 'password'"
            id="passwordConfirmation"
            placeholder="Confirmer le mot de passe"
            autocomplete="new-password"
          />

          <button
            class="absolute top-3 right-4 cursor-pointer text-[#9ba3bd] hover:text-white"
            type="button"
            :aria-label="showPasswordConfirmation ? 'Masquer la confirmation' : 'Afficher la confirmation'"
            @click="showPasswordConfirmation = !showPasswordConfirmation"
          >
            <svg
              v-if="!showPasswordConfirmation"
              width="24"
              height="24"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="2"
              stroke-linecap="round"
              stroke-linejoin="round"
            >
              <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" />
              <circle cx="12" cy="12" r="3" />
            </svg>
            <svg
              v-else
              width="24"
              height="24"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="2"
              stroke-linecap="round"
              stroke-linejoin="round"
            >
              <path
                d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"
              />
              <line x1="1" y1="1" x2="23" y2="23" />
            </svg>
          </button>
        </div>

        <!-- Alerte affichée en temps réel si les deux mots de passe ne correspondent pas. -->
        <p v-if="passwordMismatch" class="-mt-3 text-sm text-amber-300">Les mots de passe ne correspondent pas.</p>

        <!-- Message d'erreur retourné par l'API ou la validation locale. -->
        <p v-if="errorMessage" class="-mt-3 text-sm text-red-300">
          {{ errorMessage }}
        </p>

        <!-- Bouton de soumission, désactivé si le formulaire est invalide ou en cours d'envoi. -->
        <button
          class="flex translate-y-0 transform cursor-pointer items-center justify-center rounded-md bg-[linear-gradient(135deg,#102766_0%,#7446a6_100%)] px-6 py-2.5 text-sm font-semibold text-white shadow-[0_14px_30px_rgba(5,9,23,0.35)] duration-100 hover:bg-[linear-gradient(135deg,#17337c_0%,#9a65d5_100%)] active:translate-y-1 disabled:cursor-not-allowed disabled:brightness-[0.72]"
          type="submit"
          :disabled="isFormInvalid || buttonLoading"
        >
          {{ buttonLoading ? 'Chargement...' : 'Créer un compte' }}
        </button>

        <!-- Lien de retour vers la page de connexion. -->
        <button
          class="flex cursor-pointer items-center justify-center rounded-md border border-[#2f3d67] bg-[rgba(5,9,23,0.42)] px-6 py-2.5 text-sm font-semibold text-[#d6daf0] transition hover:border-[#9a65d5] hover:text-white"
          type="button"
          @click="goToLogin"
        >
          Retour à la connexion
        </button>
      </form>
    </section>
  </main>
</template>

<script lang="ts" setup>
import { computed, onMounted, ref } from 'vue'
import type { ComputedRef, Ref } from 'vue'

import { TauriWindowService } from '#src-core/services/TauriWindowService'
import type { SignUpPayload } from '#src-core/types/payload/auth.types'
import { useAuthStore } from '#src-nuxt/app/stores/auth.store'
import { useWindowTransitionStore } from '#src-nuxt/app/stores/windowTransition.store'

// Stores utilisés pour l'authentification et la transition de fenêtre.
const authStore: ReturnType<typeof useAuthStore> = useAuthStore()
const windowTransitionStore: ReturnType<typeof useWindowTransitionStore> = useWindowTransitionStore()

// État réactif du formulaire d'inscription.
const credentials: Ref<SignUpPayload> = ref({
  email: '',
  password: '',
  passwordConfirmation: '',
})
const showPassword: Ref<boolean> = ref(false)
const showPasswordConfirmation: Ref<boolean> = ref(false)
const buttonLoading: Ref<boolean> = ref(false)
const errorMessage: Ref<string> = ref('')

// Vérifie en temps réel si les deux mots de passe saisis sont différents.
const passwordMismatch: ComputedRef<boolean> = computed((): boolean => {
  return (
    credentials.value.password.length > 0 &&
    credentials.value.passwordConfirmation.length > 0 &&
    credentials.value.password !== credentials.value.passwordConfirmation
  )
})

// Désactive le bouton si un champ est vide ou si les mots de passe ne correspondent pas.
const isFormInvalid: ComputedRef<boolean> = computed((): boolean => {
  return (
    credentials.value.email.trim().length === 0 ||
    credentials.value.password.trim().length === 0 ||
    credentials.value.passwordConfirmation.trim().length === 0 ||
    passwordMismatch.value
  )
})

// Inscrit l'utilisateur puis redirige vers la page principale si l'API accepte le compte.
/**
 *
 */
const signUp: () => Promise<void> = async (): Promise<void> => {
  // Empêche une soumission concurrente ou avec un formulaire invalide.
  if (buttonLoading.value || isFormInvalid.value) {
    return
  }

  buttonLoading.value = true

  // Réinitialise l'erreur précédente avant le nouvel appel.
  errorMessage.value = ''

  try {
    await authStore.signUp(credentials.value)

    // Redimensionne la fenêtre Tauri pour la vue principale avant la navigation.
    windowTransitionStore.setLoading(true)
    await TauriWindowService.configureMainWindow()
    await navigateTo('/home')
  } catch (error: unknown) {
    console.error('SignUp error:', error)

    // Extrait le code d'erreur et les erreurs de validation de la réponse Adonis.
    const fetchError: { status?: number; data?: { code?: string; errors?: { message: string }[] } } = error as {
      status?: number
      data?: { code?: string; errors?: { message: string }[] }
    }
    const status: number | undefined = fetchError.status
    const code: string | undefined = fetchError.data?.code
    const vineErrors: { message: string }[] | undefined = fetchError.data?.errors

    if (code === 'E_EMAIL_ALREADY_USED' || status === 409) {
      errorMessage.value = 'Cette adresse email est déjà utilisée.'
    } else if (status === 422 && vineErrors && vineErrors.length > 0) {
      errorMessage.value = vineErrors.at(0)?.message ?? 'Données invalides.'
    } else {
      errorMessage.value = 'Inscription échouée. Veuillez réessayer.'
    }
  } finally {
    buttonLoading.value = false
    windowTransitionStore.setLoading(false)
  }
}

// Flag partagé entre login et signup pour indiquer une navigation interne au flow auth.
const authInternalNav: Ref<boolean> = useState('auth-internal-nav', (): boolean => false)

// Marque la navigation comme interne avant de retourner sur la page login.
/**
 *
 */
const goToLogin: () => void = (): void => {
  authInternalNav.value = true
  navigateTo('/login')
}

// Configure la fenêtre Tauri au format de connexion au montage de la page.
// Ne recentre pas la fenêtre si l'utilisateur vient de la page login (navigation interne).
onMounted(async (): Promise<void> => {
  const shouldCenter: boolean = !authInternalNav.value
  authInternalNav.value = false

  await TauriWindowService.configureLoginWindow(shouldCenter)
  windowTransitionStore.setLoading(false)
})
</script>
