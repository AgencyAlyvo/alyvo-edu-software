const UTF8_DECODER: TextDecoder = new TextDecoder('utf-8', { fatal: false })
const WINDOWS_1252_DECODER: TextDecoder = new TextDecoder('windows-1252', { fatal: false })

/**
 * Payload parfois serialise par le bridge Tauri quand l'encodage shell est `raw`.
 */
type SerializedBytePayload = {
  data?: unknown
}

/**
 * Indique si une valeur est une liste de bytes serialisee par le bridge Tauri.
 * @param {unknown} value - Valeur a controler.
 * @returns {boolean} True si la valeur peut etre transformee en Uint8Array.
 */
function isByteArray(value: unknown): value is number[] {
  return Array.isArray(value) && value.every((item: unknown): item is number => Number.isInteger(item))
}

/**
 * Convertit les formats possibles du plugin shell raw en bytes decodables.
 * @param {unknown} data - Sortie stdout/stderr brute.
 * @returns {Uint8Array | null} Vue bytes ou null si le type est inconnu.
 */
function toUint8Array(data: unknown): Uint8Array | null {
  if (data instanceof Uint8Array) {
    return data
  }

  if (data instanceof ArrayBuffer) {
    return new Uint8Array(data)
  }

  if (ArrayBuffer.isView(data)) {
    return new Uint8Array(data.buffer, data.byteOffset, data.byteLength)
  }

  if (isByteArray(data)) {
    return Uint8Array.from(data)
  }

  if (typeof data === 'object' && data !== null) {
    const payload: SerializedBytePayload = data as SerializedBytePayload

    if (isByteArray(payload.data)) {
      return Uint8Array.from(payload.data)
    }
  }

  return null
}

/**
 * Decode la sortie d'un processus (sidecar / CLI) sur Windows ou UTF-8.
 * @param {unknown} data - Chunk stdout/stderr brut ou deja decode.
 * @returns {string} Texte UTF-16 lisible dans l'UI.
 */
export function decodeProcessOutput(data: unknown): string {
  if (typeof data === 'string') {
    return data
  }

  const bytes: Uint8Array | null = toUint8Array(data)

  if (bytes === null || bytes.length === 0) {
    return ''
  }

  const asUtf8: string = UTF8_DECODER.decode(bytes)

  if (!asUtf8.includes('\uFFFD')) {
    return asUtf8
  }

  return WINDOWS_1252_DECODER.decode(bytes)
}

/**
 * Normalise une ligne de flux process (sans saut de ligne final).
 * @param {unknown} data - Chunk brut.
 * @returns {string} Ligne trim en fin uniquement.
 */
export function normalizeProcessStreamLine(data: unknown): string {
  return decodeProcessOutput(data)
    .replace(/\r?\n$/, '')
    .trimEnd()
}
