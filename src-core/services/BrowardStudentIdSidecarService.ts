/**
 * Service frontend pour lancer le sidecar Tauri `binaries/broward-student-id`.
 */
import { BROWARD_STUDENT_ID_SIDECAR_NAME } from '#src-core/constants/broward-student-id-sidecar.constants'
import type {
  BrowardStudentIdOptions,
  BrowardStudentIdSidecarResult,
  BrowardStudentIdSkippedResult,
} from '#src-core/types/response/broward-student-id-sidecar.types'
import type { SidecarBrowardStudentIdJsonLine } from '#src-core/types/response/sidecar-broward-student-id-json.types'
import { normalizeProcessStreamLine } from '#src-core/utils/decode-process-output'
import { Command, type Child, type TerminatedPayload } from '@tauri-apps/plugin-shell'

export type {
  BrowardStudentIdOptions,
  BrowardStudentIdSidecarResult,
  BrowardStudentIdSkippedResult,
} from '#src-core/types/response/broward-student-id-sidecar.types'

/**
 *
 */
export type BrowardStudentIdSidecarOutcome =
  | { type: 'success'; result: BrowardStudentIdSidecarResult }
  | { type: 'skipped'; result: BrowardStudentIdSkippedResult }

const SIDECAR_LOG_EXCERPT_LINES: number = 80

/**
 * Erreur sidecar Student ID avec journal collecte.
 */
export class BrowardStudentIdSidecarError extends Error {
  public readonly logLines: readonly string[]

  /**
   * @param {string} message - Message d'erreur principal.
   * @param {readonly string[]} [logLines] - Lignes de journal.
   */
  constructor(message: string, logLines: readonly string[] = []) {
    super(message)
    this.name = 'BrowardStudentIdSidecarError'
    this.logLines = logLines
  }
}

/**
 * Arret manuel demande par l'utilisateur.
 */
export class BrowardStudentIdSidecarStoppedError extends Error {
  public readonly logLines: readonly string[]

  /**
   * @param {readonly string[]} [logLines] - Lignes de journal.
   */
  constructor(logLines: readonly string[] = []) {
    super("Recuperation Student ID arretee par l'utilisateur.")
    this.name = 'BrowardStudentIdSidecarStoppedError'
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
    const parsed: SidecarBrowardStudentIdJsonLine = JSON.parse(lastStreamLine) as SidecarBrowardStudentIdJsonLine

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
      ? `Le sidecar Student ID s'est termine avec le code ${exitCode}.`
      : "Le sidecar Student ID n'a produit aucune sortie. Verifiez npm run sidecar:build:student-id.")

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
 * @returns {never} Leve toujours une BrowardStudentIdSidecarError.
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

  throw new BrowardStudentIdSidecarError(message, logLines)
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
 * Lance le sidecar de recuperation Student ID Broward.
 */
export class BrowardStudentIdSidecarService {
  private static activeChild: Child | null = null
  private static readonly stopSignal: { requested: boolean } = { requested: false }

  /**
   * @returns {boolean} True si arret demande.
   */
  private static isStopRequested(): boolean {
    return BrowardStudentIdSidecarService.stopSignal.requested
  }

  /**
   * Arrete le sidecar en cours.
   * @returns {Promise<boolean>} True si kill envoye.
   */
  public static async stopCurrentActivation(): Promise<boolean> {
    const child: Child | null = BrowardStudentIdSidecarService.activeChild

    if (child === null) {
      BrowardStudentIdSidecarService.stopSignal.requested = true

      return false
    }

    BrowardStudentIdSidecarService.stopSignal.requested = true
    await child.kill()

    return true
  }

  /**
   * Execute le sidecar Student ID pour un compte.
   * @param {BrowardStudentIdOptions} options - Donnees compte.
   * @param {(line: string) => void} [onLog] - Callback journal.
   * @returns {Promise<BrowardStudentIdSidecarOutcome>} Succes ou skip (mail absent).
   */
  public static async activateAccount(
    options: BrowardStudentIdOptions,
    onLog?: (line: string) => void,
  ): Promise<BrowardStudentIdSidecarOutcome> {
    BrowardStudentIdSidecarService.stopSignal.requested = false

    const accountJson: string = JSON.stringify({
      accountId: options.accountId,
      email: options.email,
      password: options.password,
      birthday: options.birthday,
    })

    const command: Command<Uint8Array> = Command.sidecar(
      BROWARD_STUDENT_ID_SIDECAR_NAME,
      ['--account-json', accountJson],
      {
        encoding: 'raw',
        env: {
          PYTHONIOENCODING: 'utf-8',
          PYTHONUTF8: '1',
        },
      },
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
      BrowardStudentIdSidecarService.activeChild = await command.spawn()
      result = await closePromise
    } catch (executeError: unknown) {
      if (BrowardStudentIdSidecarService.isStopRequested()) {
        throw new BrowardStudentIdSidecarStoppedError(collectProgressLogLines(stderrLines, outputLines))
      }

      const message: string =
        executeError instanceof Error
          ? executeError.message
          : typeof executeError === 'string'
            ? executeError
            : 'Echec au lancement du sidecar Student ID. Reconstruisez avec npm run sidecar:build:student-id.'

      throw new BrowardStudentIdSidecarError(message, stderrLines)
    } finally {
      BrowardStudentIdSidecarService.activeChild = null
    }

    if (BrowardStudentIdSidecarService.isStopRequested()) {
      throw new BrowardStudentIdSidecarStoppedError(collectProgressLogLines(stderrLines, outputLines))
    }

    const stdout: string = outputLines.join('\n').trim()
    const stderr: string = stderrLines.join('\n').trim()
    const lines: string[] = stdout.length > 0 ? stdout.split(/\r?\n/) : outputLines
    const lastLine: string = lines[lines.length - 1] ?? ''

    if (lastLine.length === 0) {
      throwSidecarFailure(result.code, stdout, stderr, outputLines, stderrLines)
    }

    let parsed: SidecarBrowardStudentIdJsonLine

    try {
      parsed = JSON.parse(lastLine) as SidecarBrowardStudentIdJsonLine
    } catch {
      throwSidecarFailure(result.code, lastLine, stderr, outputLines, stderrLines)
    }

    if (parsed.skipped && parsed.accountId !== undefined) {
      return {
        type: 'skipped',
        result: {
          skipped: true,
          accountId: parsed.accountId,
          reason: 'MAIL_NOT_FOUND',
        },
      }
    }

    if (!parsed.ok || parsed.accountId === undefined || !parsed.schoolEmail || !parsed.studentId) {
      throwSidecarFailure(result.code, stdout, stderr, outputLines, stderrLines)
    }

    if (result.code !== 0) {
      throwSidecarFailure(result.code, stdout, stderr, outputLines, stderrLines)
    }

    return {
      type: 'success',
      result: {
        accountId: parsed.accountId,
        schoolEmail: parsed.schoolEmail,
        studentId: parsed.studentId,
        schoolEmailPassword: parsed.schoolEmailPassword ?? null,
      },
    }
  }
}
