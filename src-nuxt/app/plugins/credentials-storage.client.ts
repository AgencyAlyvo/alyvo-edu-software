import { CredentialsStorageService } from '#src-core/services/CredentialsStorageService'

/**
 * Plugin client-side qui injecte l'identifiant d'application dans le CredentialsStorageService.
 * Doit s'exécuter avant tout appel au service (login, auto-login).
 */
export default defineNuxtPlugin((): void => {
  const runtimeConfig: ReturnType<typeof useRuntimeConfig> = useRuntimeConfig()

  // Injecte l'identifiant issu de NUXT_PUBLIC_APP_IDENTIFIER pour déterminer
  // le sous-dossier de stockage des credentials selon l'environnement.
  CredentialsStorageService.configure(runtimeConfig.public.appIdentifier as string)
})
