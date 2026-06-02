import { openUrl } from '@tauri-apps/plugin-opener'

/**
 * Normalise une URL externe avant ouverture.
 * @param {string | null | undefined} url - URL saisie sur le prospect.
 * @returns {string | undefined} URL exploitable avec protocole HTTP(S).
 */
export const normalizeExternalUrl: (url: string | null | undefined) => string | undefined = (
  url: string | null | undefined,
): string | undefined => {
  const trimmedUrl: string | undefined = url?.trim()
  if (!trimmedUrl) {
    return undefined
  }

  return /^[a-z][a-z\d+.-]*:\/\//i.test(trimmedUrl) ? trimmedUrl : `https://${trimmedUrl}`
}

/**
 * Ouvre une URL externe via Tauri, avec fallback navigateur.
 * @param {string | null | undefined} url - URL a ouvrir.
 * @returns {Promise<void>} Promesse resolue apres la tentative d'ouverture.
 */
export const openExternalUrl: (url: string | null | undefined) => Promise<void> = async (
  url: string | null | undefined,
): Promise<void> => {
  const normalizedUrl: string | undefined = normalizeExternalUrl(url)
  if (!normalizedUrl) {
    return
  }

  try {
    await openUrl(normalizedUrl)
  } catch {
    window.open(normalizedUrl, '_blank', 'noopener,noreferrer')
  }
}
