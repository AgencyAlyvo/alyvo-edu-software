/**
 * Identifiant du sidecar Outlook tel que declare dans `tauri.conf.json` > `bundle.externalBin`
 * et dans `capabilities/default.json` (permissions shell: spawn, execute, kill).
 *
 * Doit correspondre exactement a la chaine passee a `Command.sidecar()` cote frontend.
 * Tauri resout ensuite le binaire `src-tauri/binaries/outlook-creator-{TARGET_TRIPLE}`.
 */
export const OUTLOOK_CREATOR_SIDECAR_NAME: string = 'binaries/outlook-creator'
