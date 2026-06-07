/**
 * Resultat d'une commande systeme executee via Tauri.
 */
export type DesktopCliRunResult = {
  exitCode: number
  stdout: string
  stderr: string
}
