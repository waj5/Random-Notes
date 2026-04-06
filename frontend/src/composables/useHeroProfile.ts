import { computed } from 'vue'
import { useAuthStore } from '../stores/auth'

export function useHeroProfile(options?: { guestTitle?: string }) {
  const authStore = useAuthStore()
  const guestTitle = options?.guestTitle ?? '随心广场'

  const heroTitle = computed(() => {
    if (authStore.isAuthenticated && authStore.user) {
      return authStore.user.nickname?.trim() || authStore.user.username || '我'
    }
    return guestTitle
  })

  const heroBioLine = computed(() => authStore.user?.bio?.trim() || '')

  return { heroTitle, heroBioLine }
}
