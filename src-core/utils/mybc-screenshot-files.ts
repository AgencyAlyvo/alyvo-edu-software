import type { BrowardStudentIdMybcScreenshots } from '#src-core/types/response/broward-student-id-sidecar.types'

/**
 * Convertit un Uint8Array en base64 (navigateur / Tauri).
 */
function uint8ArrayToBase64(bytes: Uint8Array): string {
  const chunkSize: number = 0x8000
  let binary: string = ''

  for (let offset: number = 0; offset < bytes.length; offset += chunkSize) {
    const slice: Uint8Array = bytes.subarray(offset, offset + chunkSize)
    binary += String.fromCharCode(...slice)
  }

  return btoa(binary)
}

/**
 * Lit les PNG locaux produits par le sidecar et les prepare pour l'API.
 */
export async function readMybcScreenshotsFromPaths(paths: {
  studentHome: string
  prospectMenu: string
  registrationStatus: string
}): Promise<BrowardStudentIdMybcScreenshots> {
  const { readFile } = await import('@tauri-apps/plugin-fs')

  const studentHomeBytes: Uint8Array = await readFile(paths.studentHome)
  const prospectMenuBytes: Uint8Array = await readFile(paths.prospectMenu)
  const registrationStatusBytes: Uint8Array = await readFile(paths.registrationStatus)

  if (
    studentHomeBytes.length === 0
    || prospectMenuBytes.length === 0
    || registrationStatusBytes.length === 0
  ) {
    throw new Error('Fichier capture myBC vide ou illisible.')
  }

  return {
    studentHomeBase64: uint8ArrayToBase64(studentHomeBytes),
    prospectMenuBase64: uint8ArrayToBase64(prospectMenuBytes),
    registrationStatusBase64: uint8ArrayToBase64(registrationStatusBytes),
  }
}
