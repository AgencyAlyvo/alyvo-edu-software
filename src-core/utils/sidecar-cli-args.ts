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
