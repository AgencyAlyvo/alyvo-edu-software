import { isTauri } from '@tauri-apps/api/core'
import { isPermissionGranted, requestPermission, sendNotification } from '@tauri-apps/plugin-notification'
import { watch } from 'vue'
import { ProspectsCacheService, type LinkedinCallEvent } from '#src-core/services/ProspectsCacheService'
import type { LinkedinProspectSummary } from '#src-core/types/response/linkedin.types'
import { useAuthStore } from '#src-nuxt/app/stores/auth.store'
import { useLinkedinProspectsStore } from '#src-nuxt/app/stores/linkedinProspects.store'
import { PARIS_TIME_ZONE, getParisDateParts, parseIsoAsParisDate } from '#src-nuxt/app/utils/parisTime'

/**
 * Type de rendez-vous surveille.
 */
type CallType = 'discovery' | 'sales'

/**
 * Donnees minimales pour une notification de rendez-vous.
 */
type CallNotification = {
  type: CallType
  prospect: LinkedinProspectSummary
  key: string
  timeLabel: string
}

const CHECK_INTERVAL_MS: number = 30_000
/**
 * Fenetre de tolerance: on notifie si l'heure du RDV est atteinte et date de moins de 3 minutes.
 * Cela rattrape un check manque (mise en veille, onglet inactif, delai d'intervalle).
 */
const DUE_GRACE_MS: number = 180_000
const NOTIFIED_STORAGE_KEY: string = 'alyvo_linkedin_call_notifications_sent'

/**
 * Formate une date en cle minute dans le fuseau francais (sert de cle de deduplication).
 * @param {Date} date - Date a formatter.
 * @returns {string} Cle YYYY-MM-DDTHH:mm.
 */
const formatParisMinuteKey: (date: Date) => string = (date: Date): string => {
  const parts: Intl.DateTimeFormatPart[] = new Intl.DateTimeFormat('fr-FR', {
    timeZone: PARIS_TIME_ZONE,
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    hourCycle: 'h23',
  }).formatToParts(date)

  /**
   * Retourne une partie formatee.
   * @param {Intl.DateTimeFormatPartTypes} type - Type de partie attendue.
   * @returns {string} Valeur de la partie.
   */
  const valueOf: (type: Intl.DateTimeFormatPartTypes) => string = (type: Intl.DateTimeFormatPartTypes): string =>
    parts.find((part: Intl.DateTimeFormatPart): boolean => part.type === type)?.value ?? ''

  return `${valueOf('year')}-${valueOf('month')}-${valueOf('day')}T${valueOf('hour')}:${valueOf('minute')}`
}

/**
 * Indique si une chaine ISO contient une composante horaire (et pas seulement une date).
 * @param {string} iso - Date ISO.
 * @returns {boolean} True si l'ISO porte une heure.
 */
const hasTimeComponent: (iso: string) => boolean = (iso: string): boolean => iso.includes('T') && iso.length > 10

/**
 * Lit les notifications deja envoyees.
 * @returns {Set<string>} Cles notifiees.
 */
const readNotifiedKeys: () => Set<string> = (): Set<string> => {
  try {
    const raw: string | null = localStorage.getItem(NOTIFIED_STORAGE_KEY)
    const parsed: unknown = raw ? JSON.parse(raw) : []

    return new Set(
      Array.isArray(parsed) ? parsed.filter((item: unknown): item is string => typeof item === 'string') : [],
    )
  } catch {
    return new Set()
  }
}

/**
 * Persiste les notifications envoyees.
 * @param {Set<string>} keys - Cles notifiees.
 * @returns {void}
 */
const writeNotifiedKeys: (keys: Set<string>) => void = (keys: Set<string>): void => {
  localStorage.setItem(NOTIFIED_STORAGE_KEY, JSON.stringify([...keys].slice(-300)))
}

/**
 * Verifie et demande la permission d'envoyer une notification native.
 * @returns {Promise<boolean>} True si la permission est accordee.
 */
const ensureNotificationPermission: () => Promise<boolean> = async (): Promise<boolean> => {
  let permissionGranted: boolean = await isPermissionGranted()

  if (!permissionGranted) {
    const permission: NotificationPermission = await requestPermission()
    permissionGranted = permission === 'granted'
  }

  return permissionGranted
}

/**
 * Construit le texte descriptif d'un prospect.
 * @param {LinkedinProspectSummary} prospect - Prospect LinkedIn.
 * @returns {string} Description compacte.
 */
const getProspectContext: (prospect: LinkedinProspectSummary) => string = (
  prospect: LinkedinProspectSummary,
): string => {
  const parts: string[] = [prospect.company, prospect.position, prospect.phone, prospect.email].filter(
    (part: string | null): part is string => Boolean(part),
  )

  return parts.join(' - ')
}

/**
 * Construit la cle date YYYY-MM-DD en fuseau Paris.
 * @param {Date} date - Date.
 * @returns {string} YYYY-MM-DD.
 */
const toParisDateKey: (date: Date) => string = (date: Date): string => {
  const parts: { year: number; month: number; day: number } = getParisDateParts(date)
  return `${parts.year}-${String(parts.month).padStart(2, '0')}-${String(parts.day).padStart(2, '0')}`
}

/**
 * Recupere les appels d'aujourd'hui via le cache natif Rust (Rayon).
 * @param {Date} now - Instant courant.
 * @returns {Promise<LinkedinCallEvent[]>} Evenements du jour.
 */
const fetchTodayCallsFromCache: (now: Date) => Promise<LinkedinCallEvent[]> = async (
  now: Date,
): Promise<LinkedinCallEvent[]> => {
  const store: ReturnType<typeof useLinkedinProspectsStore> = useLinkedinProspectsStore()
  if (!store.cacheLoaded) {
    await store.ensureCacheLoaded()
  }
  if (ProspectsCacheService.isAvailable()) {
    return await ProspectsCacheService.linkedinCallsByDay(toParisDateKey(now))
  }
  return await store.aggregateCallsByDay(toParisDateKey(now))
}

/**
 * Filtre les appels du jour selon la fenetre de tolerance.
 * @param {LinkedinCallEvent[]} events - Appels du jour.
 * @param {Date} now - Date courante.
 * @returns {CallNotification[]} Rendez-vous a notifier.
 */
const getDueCalls: (events: LinkedinCallEvent[], now: Date) => CallNotification[] = (
  events: LinkedinCallEvent[],
  now: Date,
): CallNotification[] => {
  const dueCalls: CallNotification[] = []
  const nowMs: number = now.getTime()

  for (const event of events) {
    if (!event.hasTime || !hasTimeComponent(event.dateIso)) continue
    const date: Date | null = parseIsoAsParisDate(event.dateIso)
    if (!date) continue

    const diff: number = nowMs - date.getTime()
    if (diff < 0 || diff >= DUE_GRACE_MS) continue

    const minuteKey: string = formatParisMinuteKey(date)
    dueCalls.push({
      type: event.callType,
      prospect: event.prospect,
      key: `${minuteKey}:${event.callType}:${event.prospect.id}`,
      timeLabel: minuteKey.slice(11, 16),
    })
  }

  return dueCalls
}

/**
 * Envoie les notifications systeme pour les rendez-vous dus.
 * @param {CallNotification[]} dueCalls - Rendez-vous a notifier.
 * @returns {Promise<void>} Promesse resolue apres notification.
 */
const notifyDueCalls: (dueCalls: CallNotification[]) => Promise<void> = async (
  dueCalls: CallNotification[],
): Promise<void> => {
  if (dueCalls.length === 0 || !(await ensureNotificationPermission())) {
    return
  }

  const notifiedKeys: Set<string> = readNotifiedKeys()

  for (const call of dueCalls) {
    if (notifiedKeys.has(call.key)) {
      continue
    }

    const prospectName: string = `${call.prospect.firstName} ${call.prospect.lastName}`.trim()
    const title: string = call.type === 'discovery' ? 'Appel decouverte maintenant' : 'Appel de vente maintenant'
    const context: string = getProspectContext(call.prospect)
    const body: string = context ? `${prospectName} - ${context}` : prospectName

    sendNotification({
      title,
      body: `${body}\nHeure France : ${call.timeLabel}`,
    })
    notifiedKeys.add(call.key)
  }

  writeNotifiedKeys(notifiedKeys)
}

export default defineNuxtPlugin((): void => {
  const authStore: ReturnType<typeof useAuthStore> = useAuthStore()
  let intervalId: number | undefined
  let isChecking: boolean = false

  /**
   * Verifie les rendez-vous dus pour la fenetre de tolerance courante.
   * @returns {Promise<void>} Promesse resolue apres verification.
   */
  const checkDueCalls: () => Promise<void> = async (): Promise<void> => {
    if (!authStore.isAuthenticated || isChecking) {
      return
    }

    isChecking = true
    try {
      const now: Date = new Date()
      const events: LinkedinCallEvent[] = await fetchTodayCallsFromCache(now)
      await notifyDueCalls(getDueCalls(events, now))
    } catch (error: unknown) {
      console.warn('LinkedIn call notification check failed:', error)
    } finally {
      isChecking = false
    }
  }

  /**
   * Demarre la surveillance des rendez-vous.
   * @returns {void}
   */
  const start: () => void = (): void => {
    if (!isTauri() || intervalId !== undefined) {
      return
    }

    // Demande la permission des le demarrage pour que les notifications soient pretes.
    void ensureNotificationPermission()
    void checkDueCalls()
    intervalId = window.setInterval((): void => {
      void checkDueCalls()
    }, CHECK_INTERVAL_MS)
  }

  /**
   * Arrete la surveillance des rendez-vous.
   * @returns {void}
   */
  const stop: () => void = (): void => {
    if (intervalId !== undefined) {
      window.clearInterval(intervalId)
      intervalId = undefined
    }
  }

  watch(
    (): boolean => authStore.isAuthenticated,
    (isAuthenticated: boolean): void => {
      if (isAuthenticated) {
        start()
      } else {
        stop()
      }
    },
    { immediate: true },
  )

  window.addEventListener('beforeunload', stop)
})
