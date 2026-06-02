import { useAuthStore } from '#src-nuxt/app/stores/auth.store'
import type { RouteLocationNormalized } from 'vue-router'

export default defineNuxtRouteMiddleware((to: RouteLocationNormalized) => {
  if (!to.path.startsWith('/home')) {
    return
  }

  const authStore: ReturnType<typeof useAuthStore> = useAuthStore()
  authStore.restoreSession()

  if (!authStore.isAuthenticated) {
    return navigateTo('/login')
  }
})
