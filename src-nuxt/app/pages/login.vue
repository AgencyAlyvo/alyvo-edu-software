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

      <form class="flex flex-col gap-6 px-5 py-0" @submit.prevent="signIn">
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
            autocomplete="current-password"
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

        <!-- Case à cocher "Rester connecté" avec tooltip explicatif. -->
        <div class="flex items-center gap-2">
          <label class="group inline-flex w-fit cursor-pointer items-center select-none">
            <input
              v-model="stayLoggedIn"
              class="peer absolute opacity-0"
              type="checkbox"
              id="stayLoggedIn"
              @change="onStayLoggedInChange"
            />
            <span
              class="flex h-[18px] w-[18px] shrink-0 items-center justify-center rounded border border-[#7b84a6] bg-[rgba(5,9,23,0.78)] transition-colors group-hover:border-[#9a65d5] peer-checked:border-[#9a65d5] peer-checked:bg-[#9a65d5] peer-focus-visible:ring-2 peer-focus-visible:ring-[#9a65d5]/40 peer-checked:[&>svg]:scale-100 peer-checked:[&>svg]:opacity-100"
            >
              <svg
                class="h-3 w-3 scale-75 text-[#07153d] opacity-0 transition duration-200"
                viewBox="0 0 12 10"
                fill="none"
                aria-hidden="true"
              >
                <path
                  d="M1 5.2 4.2 8.4 11 1.2"
                  stroke="currentColor"
                  stroke-width="2"
                  stroke-linecap="round"
                  stroke-linejoin="round"
                />
              </svg>
            </span>
            <span class="pl-2 text-sm font-medium text-[#9ba3bd] group-hover:text-[#d6daf0]">Rester connecté</span>
          </label>

          <button
            class="group/info relative flex h-6 w-6 cursor-help items-center justify-center rounded-full text-[#908e97] transition outline-none hover:text-[#d6daf0] focus-visible:ring-2 focus-visible:ring-[#9a65d5]/40"
            type="button"
            aria-label="Sauvegarder vos identifiants sur cet appareil et se connecter automatiquement au prochain lancement"
            @click.prevent
          >
            <svg
              class="h-[18px] w-[18px]"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="2"
              stroke-linecap="round"
              stroke-linejoin="round"
              aria-hidden="true"
            >
              <circle cx="12" cy="12" r="10" />
              <path d="M12 16v-4" />
              <path d="M12 8h.01" />
            </svg>

            <span
              class="pointer-events-none absolute bottom-full left-1/2 z-10 mb-2 w-56 -translate-x-1/2 rounded-md border border-[#2f3d67] bg-[#050917] px-3 py-2 text-left text-[11px] leading-4 text-[#d6daf0] opacity-0 shadow-[0_14px_30px_rgba(5,9,23,0.45)] transition group-hover/info:opacity-100 group-focus-visible/info:opacity-100"
            >
              Sauvegarder vos identifiants sur cet appareil et se connecter automatiquement au prochain lancement
            </span>
          </button>
        </div>

        <!-- Message d'erreur retourné par l'API. -->
        <p v-if="errorMessage" class="-mt-3 text-sm text-red-200">
          {{ errorMessage }}
        </p>

        <!-- Bouton de soumission, désactivé si le formulaire est invalide ou en cours d'envoi. -->
        <button
          class="flex translate-y-0 transform cursor-pointer items-center justify-center rounded-md bg-[linear-gradient(135deg,#102766_0%,#7446a6_100%)] px-6 py-2.5 text-sm font-semibold text-white shadow-[0_14px_30px_rgba(5,9,23,0.35)] duration-100 hover:bg-[linear-gradient(135deg,#17337c_0%,#9a65d5_100%)] active:translate-y-1 disabled:cursor-not-allowed disabled:brightness-[0.72]"
          type="submit"
          :disabled="isFormInvalid || buttonLoading"
        >
          {{ buttonLoading ? 'Chargement...' : 'Se connecter' }}
        </button>

        <!-- Lien vers la page de création de compte. -->
        <button
          class="-mt-3 flex cursor-pointer items-center justify-center rounded-md border border-[#2f3d67] bg-[rgba(5,9,23,0.42)] px-6 py-2.5 text-sm font-semibold text-[#d6daf0] transition hover:border-[#9a65d5] hover:text-white"
          type="button"
          @click="goToSignUp"
        >
          Créer un compte
        </button>
      </form>
    </section>
  </main>
</template>

<script lang="ts" setup>
import { computed, onMounted, ref } from 'vue'
import type { ComputedRef, Ref } from 'vue'

import { CredentialsStorageService } from '#src-core/services/CredentialsStorageService'
import { TauriWindowService } from '#src-core/services/TauriWindowService'
import type { LoginPayload } from '#src-core/types/payload/auth.types'
import { useAuthStore } from '#src-nuxt/app/stores/auth.store'
import { useWindowTransitionStore } from '#src-nuxt/app/stores/windowTransition.store'

// Stores utilisés pour l'authentification et la transition de fenêtre.
const authStore: ReturnType<typeof useAuthStore> = useAuthStore()
const windowTransitionStore: ReturnType<typeof useWindowTransitionStore> = useWindowTransitionStore()

// État réactif du formulaire de connexion.
const credentials: Ref<LoginPayload> = ref({
  email: '',
  password: '',
})
const stayLoggedIn: Ref<boolean> = ref(false)
const showPassword: Ref<boolean> = ref(false)
const buttonLoading: Ref<boolean> = ref(false)
const errorMessage: Ref<string> = ref('')

// Désactive le bouton si l'un des champs obligatoires est vide.
const isFormInvalid: ComputedRef<boolean> = computed((): boolean => {
  return credentials.value.email.trim().length === 0 || credentials.value.password.trim().length === 0
})

// Supprime le fichier d'identifiants si l'utilisateur décoche "Rester connecté".
/**
 *
 */
const onStayLoggedInChange: () => Promise<void> = async (): Promise<void> => {
  if (!stayLoggedIn.value) {
    await CredentialsStorageService.clear()
  }
}

// Persiste les identifiants dans AppData si "Rester connecté" est coché, sinon supprime le fichier.
/**
 *
 */
const saveCredentialsIfNeeded: () => Promise<void> = async (): Promise<void> => {
  if (stayLoggedIn.value) {
    await CredentialsStorageService.save(credentials.value.email, credentials.value.password)
    return
  }

  await CredentialsStorageService.clear()
}

// Connecte l'utilisateur puis redirige vers la page principale si l'API valide les identifiants.
/**
 *
 */
const signIn: () => Promise<void> = async (): Promise<void> => {
  // Empêche une soumission concurrente ou avec un formulaire invalide.
  if (buttonLoading.value || isFormInvalid.value) {
    return
  }

  buttonLoading.value = true

  // Réinitialise l'erreur précédente avant le nouvel appel.
  errorMessage.value = ''

  try {
    await authStore.signIn(credentials.value)

    // Sauvegarde les identifiants si demandé, puis redimensionne la fenêtre Tauri.
    await saveCredentialsIfNeeded()
    windowTransitionStore.setLoading(true)
    await TauriWindowService.configureMainWindow()
    await navigateTo('/home')
  } catch (error: unknown) {
    console.error('SignIn error:', error)

    // Erreur réseau (backend inaccessible) : pas de status HTTP, TypeError ou fetch failed.
    const fetchError: { status?: number } = error as { status?: number }
    if (!fetchError.status) {
      errorMessage.value = 'Service indisponible. Vérifiez votre connexion ou réessayez plus tard.'
    } else {
      errorMessage.value = 'Connexion échouée. Vérifiez votre email et mot de passe.'
    }
  } finally {
    buttonLoading.value = false
    windowTransitionStore.setLoading(false)
  }
}

// Flag partagé entre login et signup pour indiquer une navigation interne au flow auth.
const authInternalNav: Ref<boolean> = useState('auth-internal-nav', (): boolean => false)

// Marque la navigation comme interne avant d'aller sur la page signup.
/**
 *
 */
const goToSignUp: () => void = (): void => {
  authInternalNav.value = true
  navigateTo('/signup')
}

// Configure la fenêtre Tauri au format de connexion et charge les identifiants sauvegardés depuis AppData.
// Ne recentre pas la fenêtre si l'utilisateur vient de la page signup (navigation interne).
// Déclenche l'auto-connexion si autoLogin est activé dans le fichier — désactivé après déconnexion manuelle.
onMounted(async (): Promise<void> => {
  const shouldCenter: boolean = !authInternalNav.value
  authInternalNav.value = false

  await TauriWindowService.configureLoginWindow(shouldCenter)
  windowTransitionStore.setLoading(false)

  // Charge les identifiants depuis AppData et pré-remplit le formulaire.
  const stored: Awaited<ReturnType<typeof CredentialsStorageService.load>> = await CredentialsStorageService.load()

  if (stored) {
    credentials.value = { email: stored.email, password: stored.password }
    stayLoggedIn.value = true

    // Auto-connexion uniquement si activée — désactivée après une déconnexion manuelle.
    if (stored.autoLogin) {
      await signIn()
    }
  }
})
</script>
