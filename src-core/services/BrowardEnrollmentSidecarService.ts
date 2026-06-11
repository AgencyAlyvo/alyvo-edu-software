/**
 * Service frontend pour lancer le sidecar Tauri `binaries/broward-enrollment`.
 */
import { BROWARD_ENROLLMENT_SIDECAR_NAME } from '#src-core/constants/broward-sidecar.constants'
import type { BrowardEnrollmentOptions, BrowardSidecarResult } from '#src-core/types/response/broward-sidecar.types'
import type { SidecarBrowardJsonLine } from '#src-core/types/response/sidecar-broward-json.types'
import { normalizeProcessStreamLine } from '#src-core/utils/decode-process-output'
import { SidecarActiveChildren } from '#src-core/utils/sidecar-active-children'
import { Command, type Child, type TerminatedPayload } from '@tauri-apps/plugin-shell'

export type { BrowardEnrollmentOptions, BrowardSidecarResult } from '#src-core/types/response/broward-sidecar.types'

const SIDECAR_LOG_EXCERPT_LINES: number = 80

/**
 * Erreur sidecar Broward avec journal collecte.
 */
export class BrowardSidecarError extends Error {
  public readonly logLines: readonly string[]

  /**
   * @param {string} message - Message d'erreur principal.
   * @param {readonly string[]} [logLines] - Lignes de journal.
   */
  constructor(message: string, logLines: readonly string[] = []) {
    super(message)
    this.name = 'BrowardSidecarError'
    this.logLines = logLines
  }
}

/**
 * Arret manuel demande par l'utilisateur.
 */
export class BrowardSidecarStoppedError extends Error {
  public readonly logLines: readonly string[]

  /**
   * @param {readonly string[]} [logLines] - Lignes de journal.
   */
  constructor(logLines: readonly string[] = []) {
    super("Inscription Broward arretee par l'utilisateur.")
    this.name = 'BrowardSidecarStoppedError'
    this.logLines = logLines
  }
}

/**
 * @param {readonly string[]} stderrLines - Lignes stderr.
 * @param {readonly string[]} outputLines - Lignes stdout.
 * @returns {string[]} Lignes de log progression.
 */
function collectProgressLogLines(stderrLines: readonly string[], outputLines: readonly string[]): string[] {
  const fromStderr: string[] = [...stderrLines]
  const fromStdout: string[] = outputLines.filter((line: string) => !line.trim().startsWith('{'))

  return fromStderr.length > 0 ? fromStderr : fromStdout
}

/**
 * @param {string} lastStreamLine - Derniere ligne stdout.
 * @returns {string | null} Message d'erreur JSON.
 */
function readJsonErrorMessage(lastStreamLine: string): string | null {
  if (lastStreamLine.length === 0) {
    return null
  }

  try {
    const parsed: SidecarBrowardJsonLine = JSON.parse(lastStreamLine) as SidecarBrowardJsonLine

    if (parsed.error) {
      return parsed.error
    }
  } catch {
    // ignore
  }

  return null
}

/**
 * @param {number | null} exitCode - Code sortie.
 * @param {string} stdout - Stdout complet.
 * @param {string} stderr - Stderr complet.
 * @param {readonly string[]} streamLines - Lignes stdout stream.
 * @param {readonly string[]} stderrLines - Lignes stderr stream.
 * @returns {string} Message utilisateur.
 */
function buildSidecarFailureMessage(
  exitCode: number | null,
  stdout: string,
  stderr: string,
  streamLines: readonly string[],
  stderrLines: readonly string[],
): string {
  const lastStreamLine: string = streamLines[streamLines.length - 1]?.trim() ?? ''
  const jsonError: string | null = readJsonErrorMessage(lastStreamLine)
  const progressLines: string[] = collectProgressLogLines(stderrLines, streamLines)
  const stderrFromBuffer: string[] =
    progressLines.length > 0
      ? progressLines
      : stderr
          .trim()
          .split(/\r?\n/)
          .filter((line: string) => line.length > 0)

  let headline: string =
    jsonError ??
    (exitCode !== null && exitCode !== 0
      ? `Le sidecar Broward s'est termine avec le code ${exitCode}.`
      : "Le sidecar Broward n'a produit aucune sortie. Verifiez npm run sidecar:build:broward.")

  if (!jsonError && stdout.trim().length > 0 && !stdout.trim().startsWith('{')) {
    headline = stdout.trim()
  }

  const excerpt: string = stderrFromBuffer.slice(-SIDECAR_LOG_EXCERPT_LINES).join('\n')

  if (excerpt.length > 0) {
    return `${headline}\n\n--- Journal sidecar (Python) ---\n${excerpt}`
  }

  return headline
}

/**
 * @param {number | null} exitCode - Code sortie.
 * @param {string} stdout - Stdout.
 * @param {string} stderr - Stderr.
 * @param {readonly string[]} outputLines - Lignes stdout.
 * @param {readonly string[]} stderrLines - Lignes stderr.
 * @returns {never} Leve toujours une BrowardSidecarError.
 */
function throwSidecarFailure(
  exitCode: number | null,
  stdout: string,
  stderr: string,
  outputLines: readonly string[],
  stderrLines: readonly string[],
): never {
  const message: string = buildSidecarFailureMessage(exitCode, stdout, stderr, outputLines, stderrLines)
  const logLines: string[] = collectProgressLogLines(stderrLines, outputLines)

  throw new BrowardSidecarError(message, logLines)
}

/**
 * @param {unknown} payload - Chunk brut shell.
 * @param {string[]} buffer - Buffer lignes.
 * @param {(line: string) => void} [onLog] - Callback UI.
 * @returns {void}
 */
function handleSidecarStreamPayload(payload: unknown, buffer: string[], onLog?: (line: string) => void): void {
  const normalized: string = normalizeProcessStreamLine(payload)

  if (normalized.trim().length === 0) {
    return
  }

  buffer.push(normalized.trim())

  if (!normalized.trim().startsWith('{')) {
    onLog?.(normalized)
  }
}

/**
 * Lance le sidecar d'inscription Broward.
 */
export class BrowardEnrollmentSidecarService {
  private static readonly stopSignal: { requested: boolean } = { requested: false }
  private static readonly activeChildren: SidecarActiveChildren = new SidecarActiveChildren(
    BrowardEnrollmentSidecarService.stopSignal,
  )

  /**
   * @returns {boolean} True si arret demande.
   */
  private static isStopRequested(): boolean {
    return BrowardEnrollmentSidecarService.activeChildren.isStopRequested()
  }

  /**
   * Reinitialise le flag d'arret avant un nouveau lot.
   * @returns {void}
   */
  public static prepareBatch(): void {
    BrowardEnrollmentSidecarService.activeChildren.resetStopSignal()
  }

  /**
   * Arrete tous les sidecars Broward en cours.
   * @returns {Promise<boolean>} True si kill envoye.
   */
  public static async stopCurrentEnrollment(): Promise<boolean> {
    return BrowardEnrollmentSidecarService.activeChildren.stopAll()
  }

  /**
   * Execute le sidecar Broward pour un compte.
   * @param {BrowardEnrollmentOptions} options - Donnees compte.
   * @param {string} capsolverApiKey - Cle API CapSolver.
   * @param {(line: string) => void} [onLog] - Callback journal.
   * @returns {Promise<BrowardSidecarResult>} Resultat inscription.
   */
  public static async enrollAccount(
    options: BrowardEnrollmentOptions,
    capsolverApiKey: string,
    onLog?: (line: string) => void,
  ): Promise<BrowardSidecarResult> {
    const apiKey: string = capsolverApiKey.trim()
    if (apiKey.length === 0) {
      throw new BrowardSidecarError('Cle API CapSolver manquante. Configurez-la dans Parametres.')
    }

    const accountJson: string = JSON.stringify({
      accountId: options.accountId,
      firstName: options.firstName,
      lastName: options.lastName,
      birthday: options.birthday,
      email: options.email,
      password: options.password,
    })

    const spawnOptions: {
      encoding: 'raw'
      env: Record<string, string>
    } = {
      encoding: 'raw',
      env: {
        PYTHONIOENCODING: 'utf-8',
        PYTHONUTF8: '1',
        CAPSOLVER_API_KEY: apiKey,
      },
    }

    const command: Command<Uint8Array> = Command.sidecar(
      BROWARD_ENROLLMENT_SIDECAR_NAME,
      ['--account-json', accountJson],
      spawnOptions,
    )

    const outputLines: string[] = []
    const stderrLines: string[] = []

    command.stdout.on('data', (line: unknown) => {
      handleSidecarStreamPayload(line, outputLines, onLog)
    })

    command.stderr.on('data', (line: unknown) => {
      handleSidecarStreamPayload(line, stderrLines, onLog)
    })

    const closePromise: Promise<TerminatedPayload> = new Promise(
      (resolve: (payload: TerminatedPayload) => void, reject: (reason: Error) => void): void => {
        command.once('close', resolve)
        command.once('error', (error: string): void => reject(new Error(error)))
      },
    )

    let result: TerminatedPayload
    let spawnedChild: Child | null = null

    try {
      spawnedChild = await command.spawn()
      BrowardEnrollmentSidecarService.activeChildren.register(spawnedChild)
      result = await closePromise
    } catch (executeError: unknown) {
      if (BrowardEnrollmentSidecarService.isStopRequested()) {
        throw new BrowardSidecarStoppedError(collectProgressLogLines(stderrLines, outputLines))
      }

      const message: string =
        executeError instanceof Error
          ? executeError.message
          : typeof executeError === 'string'
            ? executeError
            : 'Echec au lancement du sidecar Broward. Reconstruisez avec npm run sidecar:build:broward.'

      throw new BrowardSidecarError(message, stderrLines)
    } finally {
      if (spawnedChild !== null) {
        BrowardEnrollmentSidecarService.activeChildren.unregister(spawnedChild)
      }
    }

    if (BrowardEnrollmentSidecarService.isStopRequested()) {
      throw new BrowardSidecarStoppedError(collectProgressLogLines(stderrLines, outputLines))
    }

    const stdout: string = outputLines.join('\n').trim()
    const stderr: string = stderrLines.join('\n').trim()
    const lines: string[] = stdout.length > 0 ? stdout.split(/\r?\n/) : outputLines
    const lastLine: string = lines[lines.length - 1] ?? ''

    if (lastLine.length === 0) {
      throwSidecarFailure(result.code, stdout, stderr, outputLines, stderrLines)
    }

    let parsed: SidecarBrowardJsonLine

    try {
      parsed = JSON.parse(lastLine) as SidecarBrowardJsonLine
    } catch {
      throwSidecarFailure(result.code, lastLine, stderr, outputLines, stderrLines)
    }

    if (!parsed.ok || parsed.accountId === undefined || !parsed.email) {
      throwSidecarFailure(result.code, stdout, stderr, outputLines, stderrLines)
    }

    if (result.code !== 0) {
      throwSidecarFailure(result.code, stdout, stderr, outputLines, stderrLines)
    }

    return {
      accountId: parsed.accountId,
      email: parsed.email,
    }
  }
}
