/**
 * Service frontend pour lancer le sidecar Tauri `binaries/outlook-creator`.
 *
 * Responsabilites :
 * - Spawn du processus sidecar via `@tauri-apps/plugin-shell` (Python/nodriver embarques dans le binaire).
 * - Relais des lignes stderr vers l'UI (logs de progression nodriver).
 * - Parse de la derniere ligne JSON stdout (`SidecarOutlookJsonLine`) en `OutlookSidecarResult`.
 *
 * Runtime : Chrome ou Chromium doit etre installe sur le PC utilisateur (dev et production).
 * Aucun mode simule : nodriver est toujours utilise.
 */
import { OUTLOOK_CREATOR_SIDECAR_NAME } from '#src-core/constants/outlook-sidecar.constants'
import type { OutlookCreationOptions, OutlookSidecarResult } from '#src-core/types/response/outlook-sidecar.types'
import type { SidecarOutlookJsonLine } from '#src-core/types/response/sidecar-outlook-json.types'
import { normalizeProcessStreamLine } from '#src-core/utils/decode-process-output'
import { formatSidecarCliOption } from '#src-core/utils/sidecar-cli-args'
import { Command, type Child, type TerminatedPayload } from '@tauri-apps/plugin-shell'

export type { OutlookCreationOptions, OutlookSidecarResult } from '#src-core/types/response/outlook-sidecar.types'

const SIDECAR_LOG_EXCERPT_LINES: number = 80

const SIDECAR_SPAWN_OPTIONS: {
  encoding: 'raw'
  env: Record<string, string>
} = {
  encoding: 'raw',
  env: {
    PYTHONIOENCODING: 'utf-8',
    PYTHONUTF8: '1',
  },
}

/**
 * Erreur sidecar avec le journal stderr/stdout collecte pendant l'execution.
 */
export class OutlookSidecarError extends Error {
  public readonly logLines: readonly string[]

  /**
   * @param {string} message - Message d'erreur principal.
   * @param {readonly string[]} [logLines] - Lignes de journal collectees.
   */
  constructor(message: string, logLines: readonly string[] = []) {
    super(message)
    this.name = 'OutlookSidecarError'
    this.logLines = logLines
  }
}

/**
 * Erreur controlee quand l'utilisateur arrete la creation en cours.
 */
export class OutlookSidecarStoppedError extends Error {
  public readonly logLines: readonly string[]

  /**
   * @param {readonly string[]} [logLines] - Lignes de journal collectees avant l'arret.
   */
  constructor(logLines: readonly string[] = []) {
    super("Creation Outlook arretee par l'utilisateur.")
    this.name = 'OutlookSidecarStoppedError'
    this.logLines = logLines
  }
}

/**
 * Lignes de progression (hors ligne JSON finale sur stdout).
 * @param {readonly string[]} stderrLines - Lignes stderr collectees.
 * @param {readonly string[]} outputLines - Lignes stdout collectees.
 * @returns {string[]} Lignes de log a afficher.
 */
function collectProgressLogLines(stderrLines: readonly string[], outputLines: readonly string[]): string[] {
  const fromStderr: string[] = [...stderrLines]
  const fromStdout: string[] = outputLines.filter((line: string) => !line.trim().startsWith('{'))

  return fromStderr.length > 0 ? fromStderr : fromStdout
}

/**
 * Extrait le message d'erreur depuis la derniere ligne JSON stdout, si presente.
 * @param {string} lastStreamLine - Derniere ligne du flux sidecar.
 * @returns {string | null} Message d'erreur JSON ou null.
 */
function readJsonErrorMessage(lastStreamLine: string): string | null {
  if (lastStreamLine.length === 0) {
    return null
  }

  try {
    const parsed: SidecarOutlookJsonLine = JSON.parse(lastStreamLine) as SidecarOutlookJsonLine

    if (parsed.error) {
      return parsed.error
    }
  } catch {
    // ignore invalid JSON in stream
  }

  return null
}

/**
 * Construit un message d'erreur lisible avec extrait du journal sidecar.
 * @param {number | null} exitCode - Code de sortie du processus.
 * @param {string} stdout - Sortie standard complete.
 * @param {string} stderr - Sortie d'erreur complete.
 * @param {readonly string[]} streamLines - Lignes stdout stream.
 * @param {readonly string[]} stderrLines - Lignes stderr stream.
 * @returns {string} Message utilisateur avec extrait de journal.
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
      ? `Le sidecar s'est termine avec le code ${exitCode}.`
      : "Le sidecar n'a produit aucune sortie. Verifiez npm run sidecar:build et Chrome.")

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
 * Leve une erreur sidecar avec le journal collecte.
 * @param {number | null} exitCode - Code de sortie du processus.
 * @param {string} stdout - Sortie standard.
 * @param {string} stderr - Sortie d'erreur.
 * @param {readonly string[]} outputLines - Lignes stdout stream.
 * @param {readonly string[]} stderrLines - Lignes stderr stream.
 * @returns {never} Leve toujours une OutlookSidecarError.
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

  throw new OutlookSidecarError(message, logLines)
}

/**
 * Enregistre une ligne de flux sidecar (stdout/stderr).
 * @param {unknown} payload - Donnees brutes du plugin shell.
 * @param {string[]} buffer - Buffer de lignes collectees.
 * @param {(line: string) => void} [onLog] - Callback journal UI.
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
 * Lance le sidecar Python/nodriver pour creer un compte Outlook.
 */
export class OutlookCreatorSidecarService {
  /** Processus sidecar actuellement lance via Tauri. */
  private static activeChild: Child | null = null
  /** Flag d'arret manuel demande par l'utilisateur. */
  private static readonly stopSignal: { requested: boolean } = { requested: false }

  /**
   * Indique si l'utilisateur a demande l'arret pendant un await.
   * @returns {boolean} True si le sidecar doit etre considere comme arrete.
   */
  private static isStopRequested(): boolean {
    return OutlookCreatorSidecarService.stopSignal.requested
  }

  /**
   * Arrete le sidecar Outlook actuellement lance, si present.
   * @returns {Promise<boolean>} True si un processus actif a recu une demande d'arret.
   */
  public static async stopCurrentCreation(): Promise<boolean> {
    const child: Child | null = OutlookCreatorSidecarService.activeChild

    if (child === null) {
      OutlookCreatorSidecarService.stopSignal.requested = true

      return false
    }

    OutlookCreatorSidecarService.stopSignal.requested = true
    await child.kill()

    return true
  }

  /**
   * Execute le sidecar et parse la ligne JSON finale sur stdout.
   * @param {OutlookCreationOptions} options - Mot de passe, date de naissance et noms exclus.
   * @param {(line: string) => void} [onLog] - Callback pour chaque ligne de log sidecar.
   * @returns {Promise<OutlookSidecarResult>} Compte Outlook cree.
   */
  public static async createOutlookAccount(
    options: OutlookCreationOptions,
    onLog?: (line: string) => void,
  ): Promise<OutlookSidecarResult> {
    OutlookCreatorSidecarService.stopSignal.requested = false

    const usedNamesJson: string = JSON.stringify(
      (options.usedNamePairs ?? []).map((pair: { firstName: string; lastName: string }): [string, string] => [
        pair.firstName,
        pair.lastName,
      ]),
    )

    const sidecarArgs: string[] = [
      formatSidecarCliOption('password', options.password),
      formatSidecarCliOption('birthday', options.birthday),
      formatSidecarCliOption('used-names', usedNamesJson),
    ]

    if (options.skipDnsFlush) {
      sidecarArgs.push('--skip-dns-flush')
    }

    const command: Command<Uint8Array> = Command.sidecar(
      OUTLOOK_CREATOR_SIDECAR_NAME,
      sidecarArgs,
      SIDECAR_SPAWN_OPTIONS,
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

    try {
      OutlookCreatorSidecarService.activeChild = await command.spawn()
      result = await closePromise
    } catch (executeError: unknown) {
      if (OutlookCreatorSidecarService.isStopRequested()) {
        throw new OutlookSidecarStoppedError(collectProgressLogLines(stderrLines, outputLines))
      }

      const message: string =
        executeError instanceof Error
          ? executeError.message
          : typeof executeError === 'string'
            ? executeError
            : 'Echec au lancement du sidecar (processus introuvable ou argument invalide). Reconstruisez avec npm run sidecar:build.'

      throw new OutlookSidecarError(message, stderrLines)
    } finally {
      OutlookCreatorSidecarService.activeChild = null
    }

    if (OutlookCreatorSidecarService.isStopRequested()) {
      throw new OutlookSidecarStoppedError(collectProgressLogLines(stderrLines, outputLines))
    }

    const stdout: string = outputLines.join('\n').trim()
    const stderr: string = stderrLines.join('\n').trim()
    const lines: string[] = stdout.length > 0 ? stdout.split(/\r?\n/) : outputLines
    const lastLine: string = lines[lines.length - 1] ?? ''

    if (lastLine.length === 0) {
      throwSidecarFailure(result.code, stdout, stderr, outputLines, stderrLines)
    }

    let parsed: SidecarOutlookJsonLine

    try {
      parsed = JSON.parse(lastLine) as SidecarOutlookJsonLine
    } catch {
      throwSidecarFailure(result.code, lastLine, stderr, outputLines, stderrLines)
    }

    if (!parsed.ok || !parsed.email || !parsed.password || !parsed.firstName || !parsed.lastName) {
      throwSidecarFailure(result.code, stdout, stderr, outputLines, stderrLines)
    }

    if (result.code !== 0) {
      throwSidecarFailure(result.code, stdout, stderr, outputLines, stderrLines)
    }

    return {
      email: parsed.email,
      password: parsed.password,
      firstName: parsed.firstName,
      lastName: parsed.lastName,
      birthday: parsed.birthday ?? options.birthday,
    }
  }
}
