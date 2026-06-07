export const CAPSOLVER_CREATE_TASK_URL: string = 'https://api.capsolver.com/createTask'
export const CAPSOLVER_GET_RESULT_URL: string = 'https://api.capsolver.com/getTaskResult'
export const CAPSOLVER_POLL_INTERVAL_MS: number = 2000
export const CAPSOLVER_MAX_POLL_ATTEMPTS: number = 60

/** Corps JSON generique renvoye par l'API CapSolver. */
export type CapSolverJson = Record<string, unknown>

/** Erreur renvoyee lors d'un appel CapSolver invalide ou echoue. */
export class CapSolverError extends Error {
  /**
   * @param {string} message - Message d'erreur lisible.
   */
  constructor(message: string) {
    super(message)
    this.name = 'CapSolverError'
  }
}

/**
 * Construit le corps createTask pour reCAPTCHA v2 proxy-less.
 * @param {string} clientKey - Cle API CapSolver.
 * @param {string} websiteUrl - URL de la page.
 * @param {string} websiteKey - Site key reCAPTCHA.
 * @returns {CapSolverJson} Payload JSON createTask.
 */
export function buildRecaptchaV2ProxyLessCreatePayload(
  clientKey: string,
  websiteUrl: string,
  websiteKey: string,
): CapSolverJson {
  return {
    clientKey,
    task: {
      type: 'ReCaptchaV2TaskProxyLess',
      websiteURL: websiteUrl,
      websiteKey,
    },
  }
}

/**
 * Extrait le taskId d'une reponse createTask.
 * @param {CapSolverJson} data - Corps JSON CapSolver.
 * @returns {string} Identifiant de tache.
 */
export function parseCapSolverTaskId(data: CapSolverJson): string {
  if (Number(data.errorId ?? 0) !== 0) {
    throw new CapSolverError(String(data.errorDescription ?? data.errorCode ?? 'createTask a echoue'))
  }

  const taskId: unknown = data.taskId
  if (typeof taskId !== 'string' || !taskId.trim()) {
    throw new CapSolverError('CapSolver : taskId absent dans la reponse.')
  }

  return taskId
}

/**
 * Extrait le token gRecaptchaResponse d'une reponse getTaskResult prete.
 * @param {CapSolverJson} data - Corps JSON CapSolver.
 * @returns {string} Token reCAPTCHA.
 */
export function parseCapSolverRecaptchaToken(data: CapSolverJson): string {
  if (Number(data.errorId ?? 0) !== 0) {
    throw new CapSolverError(String(data.errorDescription ?? data.errorCode ?? 'getTaskResult a echoue'))
  }

  const status: string = String(data.status ?? '')
  if (status === 'failed') {
    throw new CapSolverError('CapSolver : resolution echouee (status failed).')
  }

  if (status !== 'ready') {
    throw new CapSolverError(`CapSolver : statut inattendu "${status}".`)
  }

  const solution: CapSolverJson =
    typeof data.solution === 'object' && data.solution !== null ? (data.solution as CapSolverJson) : {}

  const token: unknown = solution.gRecaptchaResponse
  if (typeof token !== 'string' || !token.trim()) {
    throw new CapSolverError('CapSolver : gRecaptchaResponse absent.')
  }

  return token
}

/**
 * Indique si getTaskResult doit continuer a poller.
 * @param {CapSolverJson} data - Corps JSON CapSolver.
 * @returns {boolean} True si le statut est encore en cours.
 */
export function isCapSolverResultPending(data: CapSolverJson): boolean {
  if (Number(data.errorId ?? 0) !== 0) {
    throw new CapSolverError(String(data.errorDescription ?? data.errorCode ?? 'getTaskResult a echoue'))
  }

  const status: string = String(data.status ?? '')
  if (status === 'failed') {
    throw new CapSolverError('CapSolver : resolution echouee (status failed).')
  }

  return status !== 'ready'
}

/** Fetch injectable pour mocker createTask / getTaskResult en test. */
export type CapSolverFetch = typeof fetch

/** Options de poll et de mock pour solveRecaptchaV2ProxyLess. */
export type SolveRecaptchaV2Options = {
  readonly fetchImpl?: CapSolverFetch
  readonly pollIntervalMs?: number
  readonly maxPollAttempts?: number
  readonly sleep?: (ms: number) => Promise<void>
}

/**
 * Resout un reCAPTCHA v2 via CapSolver (ReCaptchaV2TaskProxyLess).
 * Utilise par les tests ; le sidecar Python possede sa propre implementation.
 * @param {string} apiKey - Cle API CapSolver.
 * @param {string} websiteUrl - URL de la page.
 * @param {string} websiteKey - Site key reCAPTCHA.
 * @param {SolveRecaptchaV2Options} [options] - Options de test (fetch mock, timers).
 * @returns {Promise<string>} Token g-recaptcha-response.
 */
export async function solveRecaptchaV2ProxyLess(
  apiKey: string,
  websiteUrl: string,
  websiteKey: string,
  options: SolveRecaptchaV2Options = {},
): Promise<string> {
  const key: string = apiKey.trim()
  if (!key) {
    throw new CapSolverError('CAPSOLVER_API_KEY manquante.')
  }

  const fetchImpl: CapSolverFetch = options.fetchImpl ?? fetch
  const pollIntervalMs: number = options.pollIntervalMs ?? CAPSOLVER_POLL_INTERVAL_MS
  const maxPollAttempts: number = options.maxPollAttempts ?? CAPSOLVER_MAX_POLL_ATTEMPTS
  const sleep: (ms: number) => Promise<void> =
    options.sleep ?? ((ms: number): Promise<void> => new Promise((resolve: () => void) => setTimeout(resolve, ms)))

  const createResponse: Response = await fetchImpl(CAPSOLVER_CREATE_TASK_URL, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(buildRecaptchaV2ProxyLessCreatePayload(key, websiteUrl, websiteKey)),
  })

  if (!createResponse.ok) {
    throw new CapSolverError(`CapSolver createTask HTTP ${createResponse.status}.`)
  }

  const taskId: string = parseCapSolverTaskId((await createResponse.json()) as CapSolverJson)

  for (let attempt: number = 1; attempt <= maxPollAttempts; attempt += 1) {
    await sleep(pollIntervalMs)

    const resultResponse: Response = await fetchImpl(CAPSOLVER_GET_RESULT_URL, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ clientKey: key, taskId }),
    })

    if (!resultResponse.ok) {
      throw new CapSolverError(`CapSolver getTaskResult HTTP ${resultResponse.status}.`)
    }

    const resultData: CapSolverJson = (await resultResponse.json()) as CapSolverJson

    if (isCapSolverResultPending(resultData)) {
      continue
    }

    return parseCapSolverRecaptchaToken(resultData)
  }

  throw new CapSolverError('CapSolver : delai depasse en attente du token.')
}
