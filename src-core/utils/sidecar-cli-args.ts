/**
 * Formate une option CLI pour sidecar (argparse / spawn Windows).
 * Evite qu'une valeur commencant par « - » soit prise pour une option separee.
 * @param {string} flag - Nom du flag sans tirets (ex. password) ou avec (ex. --password).
 * @param {string} value - Valeur de l'option.
 * @returns {string} Chaine du type --password=secret.
 */
export function formatSidecarCliOption(flag: string, value: string): string {
  const name: string = flag.startsWith('--') ? flag.slice(2) : flag

  return `--${name}=${value}`
}

/**
 * Options de placement fenetre Chrome (multi-instance nodriver).
 */
export type SidecarWindowLayoutOptions = {
  windowSlot: number
  windowSlots: number
}

/**
 * Ajoute --window-slot et --window-slots si plusieurs instances simultanees.
 * @param {string[]} args - Arguments CLI sidecar en cours de construction.
 * @param {SidecarWindowLayoutOptions | undefined} layout - Slot dans la vague parallele.
 * @returns {void}
 */
export function appendSidecarWindowLayoutCliArgs(
  args: string[],
  layout: SidecarWindowLayoutOptions | undefined,
): void {
  if (!layout || layout.windowSlots <= 1) {
    return
  }

  const slot: number = Math.max(0, Math.min(layout.windowSlot, layout.windowSlots - 1))

  args.push(formatSidecarCliOption('window-slot', String(slot)))
  args.push(formatSidecarCliOption('window-slots', String(layout.windowSlots)))
}
