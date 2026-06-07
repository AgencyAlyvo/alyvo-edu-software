import { DesktopCliService } from '#src-core/services/DesktopCliService'
import type { DesktopCliRunResult } from '#src-core/types/response/desktop-cli.types'

const WINDSCRIBE_STATUS_MAX_ATTEMPTS: number = 15
const WINDSCRIBE_STATUS_POLL_MS: number = 2000
const POST_PREPARE_PAUSE_MS: number = 2500
/** Delai apres taskkill pour liberer le profil Chrome avant un nouveau sidecar. */
const POST_CHROME_CLOSE_PAUSE_MS: number = 5000

/**
 * Normalise le texte CLI Windscribe (accents FR/EN) pour la detection d'etat.
 * @param {string} text - Sortie brute Windscribe.
 * @returns {string} Texte en minuscules sans accents.
 */
function normalizeWindscribeText(text: string): string {
  return text
    .toLowerCase()
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
}

/**
 * Indique si la sortie Windscribe signale une connexion active.
 * @param {string} text - Sortie CLI connect ou status.
 * @returns {boolean} True si une connexion est detectee.
 */
function isWindscribeConnectedOutput(text: string): boolean {
  const normalized: string = normalizeWindscribeText(text)

  if (
    normalized.includes('disconnected') ||
    normalized.includes('deconnecte') ||
    normalized.includes('not connected') ||
    normalized.includes('non connecte')
  ) {
    return false
  }

  if (normalized.includes('connected') || normalized.includes('connecte')) {
    return true
  }

  // Windscribe FR : « Connecté : Tampa - … » (UTF-8) ou mojibake si mal decode
  if (/connect[eé]\s*:/i.test(text) || text.includes('ConnectÃ©')) {
    return true
  }

  return false
}

/**
 * Options de preparation VPN avant lancement du sidecar Chrome.
 */
export type PrepareVpnBatchOptions = {
  windscribeCliPath: string
  location: string
  /** Ferme Chrome avant VPN/DNS (lot 2+ ; pas au tout premier compte). */
  closeChromeFirst: boolean
  batchNumber: number
  onLog?: (line: string) => void
}

/**
 * Preparation VPN + flush DNS avant lancement de Chrome (nodriver).
 */
export class OutlookBatchVpnService {
  /**
   * Avant chaque lot de 2 comptes : Windscribe connect → flush DNS → (Chrome ouvert par le sidecar).
   * @param {PrepareVpnBatchOptions} options - Chemins CLI et options de lot.
   * @returns {Promise<void>}
   */
  public static async prepareBeforeChrome(options: PrepareVpnBatchOptions): Promise<void> {
    const log: (line: string) => void = options.onLog ?? ((): void => {})
    const cliPath: string = options.windscribeCliPath.trim()
    const location: string = options.location.trim() || 'US'

    if (cliPath.length === 0) {
      throw new Error(
        'Chemin windscribe-cli.exe non configure. Renseignez-le dans Parametres avant de lancer la creation.',
      )
    }

    log(`[Lot ${options.batchNumber}] Preparation VPN + DNS avant Chrome`)

    if (options.closeChromeFirst) {
      log('Fermeture de Google Chrome / Chromium...')
      await OutlookBatchVpnService.closeChromeWithRetry(log)
      await OutlookBatchVpnService.sleep(POST_CHROME_CLOSE_PAUSE_MS)
    }

    log(`Windscribe — connexion a ${location}...`)
    const connectResult: DesktopCliRunResult = await DesktopCliService.runProgram(cliPath, ['connect', location])
    const connectOutput: string = [connectResult.stdout, connectResult.stderr].filter(Boolean).join('\n')

    if (connectOutput.length > 0) {
      log(connectOutput.split('\n').join('\n'))
    }

    if (connectResult.exitCode !== 0) {
      throw new Error(`Windscribe connect a echoue (code ${connectResult.exitCode}).`)
    }

    if (isWindscribeConnectedOutput(connectOutput)) {
      log('  Windscribe connecte (confirme par la commande connect).')
    } else {
      log('  Verification du statut Windscribe...')
      await OutlookBatchVpnService.waitForWindscribeConnected(cliPath, log)
    }

    log('Flush DNS Windows (ipconfig /flushdns) avant Chrome...')
    const dnsResult: DesktopCliRunResult = await DesktopCliService.flushDnsWindows()

    if (dnsResult.stdout.length > 0) {
      log(`  ${dnsResult.stdout}`)
    }

    if (dnsResult.exitCode !== 0) {
      throw new Error(`Flush DNS echoue (code ${dnsResult.exitCode}).`)
    }

    log('Pret : nodriver va ouvrir Chrome sur la nouvelle session reseau.')
    await OutlookBatchVpnService.sleep(POST_PREPARE_PAUSE_MS)
  }

  /**
   * Entre deux comptes du meme lot VPN : ferme Chrome avant de relancer nodriver.
   * @param {(line: string) => void} [onLog] - Callback journal utilisateur.
   * @returns {Promise<void>}
   */
  public static async ensureChromeClosedBeforeSidecar(onLog?: (line: string) => void): Promise<void> {
    const log: (line: string) => void = onLog ?? ((): void => {})
    log('Fermeture de Chrome avant le compte suivant (meme lot VPN)...')
    await OutlookBatchVpnService.closeChromeWithRetry(log)
    log(`Attente ${POST_CHROME_CLOSE_PAUSE_MS / 1000}s (liberation du profil Chrome)...`)
    await OutlookBatchVpnService.sleep(POST_CHROME_CLOSE_PAUSE_MS)
  }

  /**
   * Ferme Chrome/Chromium apres un arret manuel de creation.
   * @param {(line: string) => void} [onLog] - Callback journal utilisateur.
   * @returns {Promise<void>}
   */
  public static async closeChromeAfterManualStop(onLog?: (line: string) => void): Promise<void> {
    const log: (line: string) => void = onLog ?? ((): void => {})
    log('Fermeture de Chrome apres arret manuel...')
    await OutlookBatchVpnService.closeChromeWithRetry(log)
    await OutlookBatchVpnService.sleep(POST_CHROME_CLOSE_PAUSE_MS)
  }

  /**
   * Ferme Chrome/Chromium (double passe si des processus subsistent).
   * @param {(line: string) => void} log - Callback journal.
   * @returns {Promise<void>}
   */
  private static async closeChromeWithRetry(log: (line: string) => void): Promise<void> {
    for (let attempt: number = 1; attempt <= 2; attempt += 1) {
      const chromeResult: DesktopCliRunResult = await DesktopCliService.closeChromeProcesses()

      if (chromeResult.stdout.length > 0) {
        log(`  ${chromeResult.stdout}`)
      }

      if (attempt === 1) {
        await OutlookBatchVpnService.sleep(1500)
      }
    }
  }

  /**
   * Attend que Windscribe signale une connexion active via `status`.
   * @param {string} cliPath - Chemin vers windscribe-cli.exe.
   * @param {(line: string) => void} log - Callback journal.
   * @returns {Promise<void>}
   */
  private static async waitForWindscribeConnected(cliPath: string, log: (line: string) => void): Promise<void> {
    for (let attempt: number = 1; attempt <= WINDSCRIBE_STATUS_MAX_ATTEMPTS; attempt += 1) {
      const status: Awaited<ReturnType<typeof DesktopCliService.runProgram>> = await DesktopCliService.runProgram(
        cliPath,
        ['status'],
      )
      const combined: string = `${status.stdout}\n${status.stderr}`

      if (isWindscribeConnectedOutput(combined)) {
        log('  Windscribe connecte (statut).')

        return
      }

      if (attempt === 1 || attempt % 5 === 0) {
        log(`  En attente de connexion Windscribe (${attempt}/${WINDSCRIBE_STATUS_MAX_ATTEMPTS})...`)
      }

      await OutlookBatchVpnService.sleep(WINDSCRIBE_STATUS_POLL_MS)
    }

    throw new Error('Windscribe : delai depasse en attente de connexion (status).')
  }

  /**
   * Pause asynchrone utilitaire.
   * @param {number} ms - Duree en millisecondes.
   * @returns {Promise<void>}
   */
  private static sleep(ms: number): Promise<void> {
    return new Promise((resolve: () => void) => {
      setTimeout(resolve, ms)
    })
  }
}
